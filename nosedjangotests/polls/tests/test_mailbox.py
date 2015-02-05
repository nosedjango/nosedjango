from django.test import TestCase
from django.core import mail


class MailBoxTestCase(TestCase):
    def test_AAA_send_mail(self):
        self.assertEqual(len(mail.outbox), 0)
        mail.send_mail(
            subject='subject',
            message='body',
            from_email='foo@gmail.com',
            recipient_list=['bar@gmail.com'],
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_BBB_send_mail(self):
        self.test_AAA_send_mail()
