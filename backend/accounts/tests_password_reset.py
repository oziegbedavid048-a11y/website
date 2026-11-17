"""Forgotten password: an emailed code, then a new password."""

import json
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase

OLD = 'ZentraTest2026x'
NEW = 'BrandNewPass2027y'


def code_in(message):
    return re.search(r'\b(\d{6})\b', message.body).group(1)


class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user('fay@example.com', 'fay@example.com', OLD)
        self.client = Client(enforce_csrf_checks=True)
        self.client.get('/api/auth/csrf/')

    def post(self, url, body=None, client=None):
        c = client or self.client
        return c.post(url, data=json.dumps(body or {}), content_type='application/json',
                      HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)

    def forgot(self, email='fay@example.com'):
        return self.post('/api/auth/password/forgot/', {'email': email})

    def reset(self, code, password=NEW, email='fay@example.com'):
        return self.post('/api/auth/password/reset/', {'email': email, 'code': code, 'password': password})

    def test_full_reset_then_sign_in_with_the_new_password(self):
        res = self.forgot('Fay@Example.com')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reset your', mail.outbox[0].subject)
        res = self.reset(code_in(mail.outbox[0]))
        self.assertEqual(res.status_code, 200, res.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW))
        self.assertFalse(self.user.check_password(OLD))
        self.assertIn('password was changed', mail.outbox[-1].subject)
        # The new password works (and still asks for the sign-in code).
        res = self.post('/api/auth/login/', {'email': 'fay@example.com', 'password': NEW})
        self.assertTrue(res.json()['code_required'])

    def test_unknown_email_gets_the_same_answer_and_no_email(self):
        known = self.forgot().json()
        cache.clear()
        unknown = self.forgot('nobody@example.com').json()
        self.assertEqual(known['message'], unknown['message'])
        self.assertEqual(len(mail.outbox), 1)  # only the real account got one

    def test_a_wrong_code_changes_nothing(self):
        self.forgot()
        right = code_in(mail.outbox[0])
        wrong = '000000' if right != '000000' else '111111'
        self.assertEqual(self.reset(wrong).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD))

    def test_a_weak_password_is_refused_before_the_code_is_used(self):
        self.forgot()
        code = code_in(mail.outbox[0])
        res = self.reset(code, password='weak')
        self.assertEqual(res.status_code, 400)
        self.assertIn('password', res.json()['errors'])
        self.assertEqual(self.reset(code).status_code, 200)  # the code still works after fixing it

    def test_a_code_works_only_once(self):
        self.forgot()
        code = code_in(mail.outbox[0])
        self.assertEqual(self.reset(code).status_code, 200)
        self.assertEqual(self.reset(code, password='AnotherPass2028z').status_code, 400)

    def test_a_sign_in_code_cannot_reset_a_password(self):
        self.post('/api/auth/login/', {'email': 'fay@example.com', 'password': OLD})
        sign_in_code = code_in(mail.outbox[-1])
        self.assertEqual(self.reset(sign_in_code).status_code, 400)

    def test_resetting_signs_out_other_devices(self):
        other = Client()
        other.force_login(self.user)
        self.assertIsNotNone(other.get('/api/auth/me/').json()['user'])
        self.forgot()
        self.reset(code_in(mail.outbox[0]))
        self.assertIsNone(other.get('/api/auth/me/').json()['user'])
