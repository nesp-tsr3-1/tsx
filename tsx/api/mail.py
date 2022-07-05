import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tsx.config import config
import ssl

smtp_host = config.get('smtp', 'host')
smtp_port = config.getint('smtp', 'port')
smtp_username = config.get('smtp', 'username')
smtp_password = config.get('smtp', 'password')
smtp_use_starttls = config.getboolean('smtp', 'use_starttls')
smtp_sender = config.get('smtp', 'default_sender')

def send_email(email_address, subject, message):
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
