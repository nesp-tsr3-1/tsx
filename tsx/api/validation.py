# Basic field validation framework
from collections.abc import Collection, Callable
from dataclasses import dataclass, field
import re

# Field = namedtuple("Field", "name title validators")

@dataclass
class Field:
	name: str
	title: str = ''
	validators: Collection[Callable] = field(default_factory=list)
	type: str = 'any'

email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

def value_present(value):
	return value != None and value != ""

def validate_email(value, field, context):
	if value_present(value) and not re.match(email_regex, value):
		return "Must be a valid email address"

def validate_required(value, field, context):
	if not value_present(value):
		return "%s is required" % (field.title or "This field")

def validate_max_chars(length):
	def _validate_max_chars(value, field, context):
		if value_present(value) and len(value) > length:
			return "Must contain no more than %s characters" % length
	return _validate_max_chars

def validate_min_chars(length):
	def _validate_min_chars(value, field, context):
		if value_present(value) and len(value) < length:
			return "Must contain at least %s characters" % length
	return _validate_min_chars

def validate_one_of(*items):
	def _validate_one_of(value, field, context):
		if value_present(value) and value not in items:
			return "Must be one of: %s" % ", ".join(items)
	return _validate_one_of

def validate_integer(min_value=None, max_value=None):
	def _validate_integer(value, field, context):
		ok = True
		if value_present(value):
			try:
				x = int(value)
				if min_value != None:
					ok = ok and x >= min_value
				if max_value != None:
					ok = ok and x <= max_value
			except ValueError:
				ok = False

			if not ok:
				if min_value != None:
					if max_value != None:
						criteria = " between %s and %s (inclusive)" % (min_value, max_value)
					else:
						criteria = " greater than or equal to %s" % min_value
				else:
					if max_value != None:
						criteria = " less than or equal to %s" % max_value
					else:
						criteria + ""
				return "Must be a whole number%s" % criteria

	return _validate_integer


def validate_fields(fields, body, context=None):
	errors = {}

	for field in fields:
		value = body[field.name]

		if type(value) == str:
			value = value.strip()

		for validator in field.validators:
			message = validator(value, field, context)
			if message:
				errors[field.name] = message
				break
				# errors.append({
				# 	'field': field.name,
				# 	'message': message
				# })

	return errors
