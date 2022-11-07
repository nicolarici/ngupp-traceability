import smtpd
import asyncore

class CustomSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data, mail_options=None, rcpt_options=None):
        print(data.decode('utf-8'))
        return

server = CustomSMTPServer(('localhost', 1025), None)

asyncore.loop()