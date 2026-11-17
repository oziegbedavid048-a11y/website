"""Email verification codes for sign-up.

A visitor types their email, we send a 6-digit code, they type it back, and
only then can they create the account. The code is never stored: only a keyed
hash of it. It expires after 10 minutes, allows 5 guesses, and can be asked for
again only after a short wait.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from .emails import password_reset_code_email, sign_in_code_email, verification_code_email
from .models import EmailCode

CODE_TTL = timedelta(minutes=10)
MAX_GUESSES = 5
RESEND_AFTER = timedelta(seconds=45)
TOKEN_TTL_SECONDS = 30 * 60
TOKEN_SALT = 'zentra.email-verified'  # noqa: S105 (a label that separates token types, not a secret)


class Cooldown(Exception):
    def __init__(self, seconds):
        super().__init__(f'wait {seconds} seconds')
        self.seconds = seconds


class SendFailed(Exception):
    pass


class CodeProblem(Exception):
    """A wrong, expired or used-up code. The message is safe to show."""


def _hash(email, code, purpose='signup'):
    # The purpose is part of the hash, so a sign-up code never works for signing in.
    label = email if purpose == 'signup' else f'{purpose}:{email}'
    return hmac.new(settings.SECRET_KEY.encode(), f'{label}:{code}'.encode(), hashlib.sha256).hexdigest()


EMAILS = {'signup': verification_code_email, 'signin': sign_in_code_email, 'reset': password_reset_code_email}


def send_code(email, purpose='signup'):
    """Create and email a code. Returns (seconds until it expires, the code)."""
    now = timezone.now()
    latest = EmailCode.objects.filter(email=email).order_by('-created_at').first()
    if latest and now - latest.created_at < RESEND_AFTER:
        raise Cooldown(max(1, int((RESEND_AFTER - (now - latest.created_at)).total_seconds())))

    code = f'{secrets.randbelow(10 ** 6):06d}'
    EmailCode.objects.filter(email=email, used=False).update(used=True)  # only the newest code works
    EmailCode.objects.filter(created_at__lt=now - timedelta(days=1)).delete()
    record = EmailCode.objects.create(email=email, code_hash=_hash(email, code, purpose), expires_at=now + CODE_TTL)
    try:
        EMAILS[purpose](email, code, int(CODE_TTL.total_seconds() // 60)).send(fail_silently=False)
    except Exception as exc:
        record.delete()  # not sent, so it must not block asking again
        raise SendFailed(str(exc)) from exc
    return int(CODE_TTL.total_seconds()), code


def check_code(email, code, purpose='signup'):
    """Check a typed code. Returns a signed token that proves the email was verified.

    The code's row is locked while it is checked, so guesses sent at the same
    moment are counted one by one and a code can only ever be used once. The
    guess count is saved before any error is raised, so a wrong guess always
    counts.
    """
    code = str(code or '').strip()
    with transaction.atomic():
        entry = (EmailCode.objects.select_for_update()
                 .filter(email=email, used=False).order_by('-created_at').first())
        if entry is None or entry.expires_at < timezone.now():
            problem = 'That code has expired. Ask for a new one.'
        elif entry.attempts >= MAX_GUESSES:
            entry.used = True
            entry.save(update_fields=['used'])
            problem = 'Too many wrong codes. Ask for a new one.'
        else:
            entry.attempts += 1
            right = len(code) == 6 and code.isdigit() and hmac.compare_digest(entry.code_hash, _hash(email, code, purpose))
            if right:
                entry.used = True
                problem = ''
            else:
                left = MAX_GUESSES - entry.attempts
                if left <= 0:
                    entry.used = True
                problem = ('That code is not right. Check it and try again.' if left > 0
                           else 'Too many wrong codes. Ask for a new one.')
            entry.save(update_fields=['attempts', 'used'])
    if problem:
        raise CodeProblem(problem)
    return signing.dumps({'email': email}, salt=TOKEN_SALT)


def verified_email(token):
    """The email a token proves was verified, or None if it is missing, forged or old."""
    try:
        return signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_TTL_SECONDS).get('email')
    except (signing.BadSignature, TypeError):
        return None
