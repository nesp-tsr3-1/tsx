import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tsx.config import config
import ssl
from concurrent.futures import ThreadPoolExecutor

smtp_host = config.get('smtp', 'host')
smtp_port = config.getint('smtp', 'port')
smtp_username = config.get('smtp', 'username')
smtp_password = config.get('smtp', 'password')
smtp_use_starttls = config.getboolean('smtp', 'use_starttls')
smtp_sender = config.get('smtp', 'default_sender')
admin_recipient = config.get('api', 'admin_notification_email')

_executor = ThreadPoolExecutor(1)

def send_email(email_address, subject, message, background=False):
	if background:
		_executor.submit(send_email, email_address, subject, message)
		return

	s = smtplib.SMTP(smtp_host, port=smtp_port)
	if smtp_use_starttls:
		ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
		ssl_context.set_ciphers('DEFAULT:!DH')
		s.starttls(context=ssl_context)
	s.login(smtp_username, smtp_password)

	msg = MIMEMultipart()

	msg['From'] = smtp_sender
	msg['To'] = email_address
	msg['Subject'] = subject
	msg.attach(MIMEText(message, 'plain'))

	s.sendmail(smtp_sender, email_address, msg.as_string())
	s.quit()


def send_admin_notification(subject, message):
	if admin_recipient:
		send_email(admin_recipient, 'TSX Notification: %s' % subject, message, background=True)
