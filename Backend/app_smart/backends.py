import ssl
import smtplib

from django.core.mail.backends.smtp import EmailBackend


class UnverifiedSMTPBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False

        connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        connection.set_debuglevel(self.fail_silently)

        if self.use_tls:
            connection.starttls(context=ssl._create_unverified_context())
            connection.ehlo()

        if self.username and self.password:
            connection.login(self.username, self.password)

        self.connection = connection
        return True
