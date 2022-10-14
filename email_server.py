import smtpd
import asyncore

class CustomSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data, mail_options=None, rcpt_options=None):
        print(data.decode('us-ascii')[95:])
        return

server = CustomSMTPServer(('localhost', 1025), None)

asyncore.loop()