# Basic field validation framework
from collections import namedtuple
import re

Field = namedtuple("Field", "name title validators")

email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
def validate_email(value, field):
	if not re.match(email_regex, value):
		return "Must be a valid email address"

def validate_required(value, field):
	if value is None or value == "":
		return "%s is required" % field.title

def validate_max_chars(length):
	def v(value, field):
		if len(value) > length:
			return "Must contain no more than %s characters" % length
	return v

def validate_min_chars(length):
	def v(value, field):
		if len(value) < length:
			return "Must contain at least %s characters" % length
	return v

def validate_fields(fields, body):
	errors = {}

	for field in fields:
		value = body[field.name].strip()

		for validator in field.validators:
			message = validator(value, field)
			if message:
				errors[field.name] = message
				break
				# errors.append({
				# 	'field': field.name,
				# 	'message': message
				# })

	return errors
