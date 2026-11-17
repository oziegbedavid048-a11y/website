"""The emails the site sends, as plain text plus a simple HTML version.

Kept deliberately plain: no images, no tracking, no styling beyond what makes
the text easy to read. Every email client shows the plain text if it cannot
show the HTML. All of them share one layout and one footer.
"""

from datetime import date

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape, linebreaks

BRAND = 'Zentra Direct'
FONT = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
INK = '#1f2933'
NAVY = '#14305a'
MUTED = '#7b8794'


def _site_url():
    return (getattr(settings, 'SITE_URL', '') or 'https://zentradirect.com').rstrip('/')


def _host():
    return _site_url().split('://', 1)[-1]


def _support_email():
    return getattr(settings, 'SUPPORT_EMAIL', '') or 'support@zentradirect.com'


def _footer_text():
    return (
        f'{BRAND}\n'
        f'{_host()} | {_support_email()}\n'
        'This is an automated message. Please do not reply to this email.\n'
        f'(c) {date.today().year} {BRAND}. All rights reserved.\n'
    )


def _footer_html():
    """A simple, tidy footer: the name, two links, one line of small print."""
    url = escape(_site_url())
    support = escape(_support_email())
    return f"""
<tr><td style="padding:28px 0 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #e4e7eb;">
    <tr><td style="padding:20px 0 4px;font-size:14px;font-weight:700;color:{NAVY};letter-spacing:0.02em;">{BRAND}</td></tr>
    <tr><td style="padding:0 0 12px;font-size:13px;line-height:1.6;">
      <a href="{url}" style="color:{NAVY};text-decoration:none;">{escape(_host())}</a>
      <span style="color:#cbd2d9;">&nbsp;&nbsp;|&nbsp;&nbsp;</span>
      <a href="mailto:{support}" style="color:{NAVY};text-decoration:none;">{support}</a>
    </td></tr>
    <tr><td style="font-size:12px;line-height:1.6;color:{MUTED};">
      This is an automated message. Please do not reply to this email.<br>
      &copy; {date.today().year} {BRAND}. All rights reserved.
    </td></tr>
  </table>
</td></tr>"""


def _p(text):
    return f'<p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:{INK};">{text}</p>'


def _layout(body_html):
    """One centred column of text, the brand name above it and the footer below."""
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{BRAND}</title></head>
<body style="margin:0;padding:0;background:#ffffff;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;font-family:{FONT};">
<tr><td style="padding:0 0 24px;font-size:18px;font-weight:700;color:{NAVY};">{BRAND}</td></tr>
<tr><td>{body_html}</td></tr>
{_footer_html()}
</table>
</td></tr>
</table>
</body>
</html>
"""


def _quote_html(text):
    """A message quoted in a light box, line breaks kept, everything escaped."""
    return (f'<div style="margin:0 0 20px;padding:14px 16px;border-left:3px solid {NAVY};background:#f5f7fa;'
            f'font-size:14px;line-height:1.6;color:{INK};">{linebreaks(escape(text))}</div>')


def _send(to, subject, text, html):
    message = EmailMultiAlternatives(subject=subject, body=text, to=[to])
    message.attach_alternative(html, 'text/html')
    return message


# ---------- sign-up code ----------

def verification_code_email(to, code, minutes):
    """The email with the 6-digit sign-up code."""
    subject = f'Your {BRAND} verification code'
    text = (
        'Hello,\n\n'
        f'Use the code below to verify your email address and continue opening your {BRAND} account.\n\n'
        f'    {code}\n\n'
        f'This code expires in {minutes} minutes. For your security, do not share it with anyone. '
        f'{BRAND} will never ask you for this code.\n\n'
        'If you did not request this code, you can safely ignore this email.\n\n'
        f'Regards,\n{BRAND}\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p('Hello,')
        + _p(f'Use the code below to verify your email address and continue opening your {BRAND} account.')
        + f'<p style="margin:8px 0 24px;font-size:32px;line-height:1.2;font-weight:700;letter-spacing:6px;color:{NAVY};">{escape(code)}</p>'
        + _p(f'This code expires in {minutes} minutes. For your security, do not share it with anyone. '
             f'{BRAND} will never ask you for this code.')
        + _p('If you did not request this code, you can safely ignore this email.')
        + _p(f'Regards,<br>{BRAND}')
    )
    return _send(to, subject, text, _layout(body))


# ---------- support ----------

def ticket_opened_email(to, ticket, first_message):
    """Sent when someone opens a support ticket."""
    ref = ticket.reference
    subject = f'Support ticket opened: {ticket.subject} [{ref}]'
    text = (
        'Hello,\n\n'
        f'Thank you for contacting {BRAND} support. Your ticket has been opened and our team will reply as soon as possible.\n\n'
        f'Ticket: {ref}\nSubject: {ticket.subject}\n\n'
        f'Your message:\n{first_message}\n\n'
        'You can read our replies and answer them in your dashboard under Support.\n\n'
        f'Regards,\n{BRAND} Support\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p('Hello,')
        + _p(f'Thank you for contacting {BRAND} support. Your ticket has been opened and our team will reply as soon as possible.')
        + _p(f'<b>Ticket:</b> {escape(ref)}<br><b>Subject:</b> {escape(ticket.subject)}')
        + _quote_html(first_message)
        + _p(f'You can read our replies and answer them in your dashboard under '
             f'<a href="{escape(_site_url())}/account/support" style="color:{NAVY};">Support</a>.')
        + _p(f'Regards,<br>{BRAND} Support')
    )
    return _send(to, subject, text, _layout(body))


def ticket_reply_email(to, ticket, reply):
    """Sent when our team replies to a ticket."""
    ref = ticket.reference
    subject = f'New reply to your support ticket [{ref}]'
    text = (
        'Hello,\n\n'
        f'Our support team has replied to your ticket "{ticket.subject}" ({ref}):\n\n'
        f'{reply}\n\n'
        'To answer, open your dashboard and go to Support.\n\n'
        f'Regards,\n{BRAND} Support\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p('Hello,')
        + _p(f'Our support team has replied to your ticket <b>{escape(ticket.subject)}</b> ({escape(ref)}):')
        + _quote_html(reply)
        + _p(f'To answer, open your dashboard and go to '
             f'<a href="{escape(_site_url())}/account/support" style="color:{NAVY};">Support</a>.')
        + _p(f'Regards,<br>{BRAND} Support')
    )
    return _send(to, subject, text, _layout(body))


# ---------- sign-in code ----------

def sign_in_code_email(to, code, minutes):
    """The 6-digit code asked for after the password, before the dashboard opens."""
    subject = f'Your {BRAND} sign-in code'
    text = (
        'Hello,\n\n'
        f'Use the code below to finish signing in to your {BRAND} account.\n\n'
        f'    {code}\n\n'
        f'This code expires in {minutes} minutes. Do not share it with anyone. '
        f'{BRAND} will never ask you for this code.\n\n'
        'If you did not try to sign in, someone may know your password. '
        f'Please contact us at {_support_email()} straight away.\n\n'
        f'Regards,\n{BRAND}\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p('Hello,')
        + _p(f'Use the code below to finish signing in to your {BRAND} account.')
        + f'<p style="margin:8px 0 24px;font-size:32px;line-height:1.2;font-weight:700;letter-spacing:6px;color:{NAVY};">{escape(code)}</p>'
        + _p(f'This code expires in {minutes} minutes. Do not share it with anyone. '
             f'{BRAND} will never ask you for this code.')
        + _p('If you did not try to sign in, someone may know your password. '
             f'Please contact us at <a href="mailto:{escape(_support_email())}" style="color:{NAVY};">'
             f'{escape(_support_email())}</a> straight away.')
        + _p(f'Regards,<br>{BRAND}')
    )
    return _send(to, subject, text, _layout(body))


# ---------- identity verification ----------

def verification_approved_email(to, name):
    """Sent once, when a client's identity verification is approved."""
    hello = f'Hello {name},' if name else 'Hello,'
    url = _site_url() + '/account'
    subject = 'Your identity has been verified'
    text = (
        f'{hello}\n\n'
        f'Your identity verification is complete and your {BRAND} account is now fully verified.\n\n'
        'You can now use every feature of your account, including withdrawals.\n\n'
        f'Sign in: {url}\n\n'
        f'If you have any questions, contact us at {_support_email()}.\n\n'
        f'Regards,\n{BRAND}\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p(escape(hello))
        + _p(f'Your identity verification is complete and your {BRAND} account is now fully verified.')
        + _p('You can now use every feature of your account, including withdrawals.')
        + f'<p style="margin:8px 0 24px;"><a href="{escape(url)}" style="display:inline-block;padding:12px 22px;'
          f'border-radius:8px;background:{NAVY};color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;">'
          'Go to my account</a></p>'
        + _p(f'If you have any questions, contact us at <a href="mailto:{escape(_support_email())}" '
             f'style="color:{NAVY};">{escape(_support_email())}</a>.')
        + _p(f'Regards,<br>{BRAND}')
    )
    return _send(to, subject, text, _layout(body))


# ---------- trade alert (to the broker's own inbox) ----------

def trade_alert_email(to, rows, subject):
    """A plain table of a new trade's details. `rows` is a list of (label, value)."""
    text = 'A client has placed a trade.\n\n' + '\n'.join(f'{k}: {v}' for k, v in rows) + '\n\n--\n' + _footer_text()
    cells = ''.join(
        f'<tr><td style="padding:8px 12px;border-bottom:1px solid #e4e7eb;font-size:14px;color:{MUTED};white-space:nowrap;">{escape(k)}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #e4e7eb;font-size:14px;color:{INK};font-weight:600;">{escape(str(v))}</td></tr>'
        for k, v in rows
    )
    body = (
        _p('A client has placed a trade.')
        + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 20px;border-top:1px solid #e4e7eb;">{cells}</table>'
    )
    return _send(to, subject, text, _layout(body))


# ---------- password reset ----------

def password_reset_code_email(to, code, minutes):
    """The 6-digit code that lets a client choose a new password."""
    subject = f'Reset your {BRAND} password'
    text = (
        'Hello,\n\n'
        f'We received a request to reset the password for your {BRAND} account. '
        'Use the code below to choose a new password.\n\n'
        f'    {code}\n\n'
        f'This code expires in {minutes} minutes. Do not share it with anyone. '
        f'{BRAND} will never ask you for this code.\n\n'
        'If you did not ask to reset your password, you can ignore this email. Your password will not change.\n\n'
        f'Regards,\n{BRAND}\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p('Hello,')
        + _p(f'We received a request to reset the password for your {BRAND} account. '
             'Use the code below to choose a new password.')
        + f'<p style="margin:8px 0 24px;font-size:32px;line-height:1.2;font-weight:700;letter-spacing:6px;color:{NAVY};">{escape(code)}</p>'
        + _p(f'This code expires in {minutes} minutes. Do not share it with anyone. '
             f'{BRAND} will never ask you for this code.')
        + _p('If you did not ask to reset your password, you can ignore this email. Your password will not change.')
        + _p(f'Regards,<br>{BRAND}')
    )
    return _send(to, subject, text, _layout(body))


def password_changed_email(to):
    """Confirms a password change, so a client notices one they did not make."""
    subject = f'Your {BRAND} password was changed'
    text = (
        'Hello,\n\n'
        f'The password for your {BRAND} account was just changed, and you have been signed out on all devices.\n\n'
        f'If you made this change, no action is needed. If you did not, contact us at {_support_email()} straight away.\n\n'
        f'Regards,\n{BRAND}\n\n'
        '--\n'
        + _footer_text()
    )
    body = (
        _p('Hello,')
        + _p(f'The password for your {BRAND} account was just changed, and you have been signed out on all devices.')
        + _p('If you made this change, no action is needed. If you did not, contact us at '
             f'<a href="mailto:{escape(_support_email())}" style="color:{NAVY};">{escape(_support_email())}</a> straight away.')
        + _p(f'Regards,<br>{BRAND}')
    )
    return _send(to, subject, text, _layout(body))
