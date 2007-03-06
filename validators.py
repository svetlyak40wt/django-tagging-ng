import re
from django.core.validators import ValidationError
from tagging.utils import split_tag_list

tag_list_re = re.compile(r'^[-\w]+(?:(?:,\s|[,\s])[-\w]+)*$')

def isTagList(field_data, all_data):
    """
    Validates that ``field_data`` is a valid list of tag names,
    separated by a single comma, a single space or a comma followed
    by a space.

    >>> isTagList('foo', {})
    >>> isTagList('foo bar baz', {})
    >>> isTagList('foo,bar,baz', {})
    >>> isTagList('foo, bar, baz', {})
    >>> isTagList('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb bar', {})
    >>> isTagList('', {})
    Traceback (most recent call last):
        ...
    ValidationError: ['Tag names must contain only letters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
    >>> isTagList(' foo', {})
    Traceback (most recent call last):
        ...
    ValidationError: ['Tag names must contain only letters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
    >>> isTagList('foo ', {})
    Traceback (most recent call last):
        ...
    ValidationError: ['Tag names must contain only letters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
    >>> isTagList('foo  bar', {})
    Traceback (most recent call last):
        ...
    ValidationError: ['Tag names must contain only letters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
    >>> isTagList('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbn bar', {})
    Traceback (most recent call last):
        ...
    ValidationError: ['Tag names must be no longer than 50 characters.']
    """
    if not tag_list_re.search(field_data):
        raise ValidationError('Tag names must contain only letters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.')
    tag_names = split_tag_list(field_data)
    for tag_name in tag_names:
        if len(tag_name) > 50:
            raise ValidationError('Tag names must be no longer than 50 characters.')