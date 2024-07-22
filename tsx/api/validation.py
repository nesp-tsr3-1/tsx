# Basic field validation framework
from collections.abc import Collection, Callable
from dataclasses import dataclass
import re

# Field = namedtuple("Field", "name title validators")

@dataclass
class Field:
	name: str
	title: str
	validators: Collection[Callable]
	type: str = 'any'

email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

def value_present(value):
	return value != None and value != ""

def validate_email(value, field):
	if value_present(value) and not re.match(email_regex, value):
		return "Must be a valid email address"

def validate_required(value, field):
	if not value_present(value):
		return "%s is required" % field.title

def validate_max_chars(length):
	def _validate_max_chars(value, field):
		if value_present(value) and len(value) > length:
			return "Must contain no more than %s characters" % length
	return _validate_max_chars

def validate_min_chars(length):
	def _validate_min_chars(value, field):
		if value_present(value) and len(value) < length:
			return "Must contain at least %s characters" % length
	return _validate_min_chars

def validate_one_of(*items):
	def _validate_one_of(value, field):
		if value_present(value) and value not in items:
			return "Must be one of: %s" % ", ".join(items)

def validate_fields(fields, body):
	errors = {}

	for field in fields:
		value = body[field.name]

		if type(value) == str:
			value = value.strip()

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
