import re

from django.core.validators import ValidationError
from django.utils.encoding import smart_unicode

from tagging.utils import get_tag_name_list

tag_re = re.compile(r'^[-\w]+$', re.U)
tag_list_re = re.compile(r'^[-\w]+(?:(?:,\s|[,\s])[-\w]+)*$', re.U)

def isTagList(field_data, all_data):
    """
    Validates that ``field_data`` is a valid list of tag names,
    separated by a single comma, a single space or a comma followed
    by a space.
    """
    if field_data is not None:
        field_data = smart_unicode(field_data)
    if not tag_list_re.search(field_data):
        raise ValidationError(u'Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.')
    tag_names = get_tag_name_list(field_data)
    for tag_name in tag_names:
        if len(tag_name) > 50:
            raise ValidationError(u'Tag names must be no longer than 50 characters.')

def isTag(field_data, all_data):
    """
    Validates that ``field_data`` is a valid tag name.
    """
    if field_data is not None:
        field_data = smart_unicode(field_data)
    if not tag_re.match(field_data):
        raise ValidationError(u'Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens.')
