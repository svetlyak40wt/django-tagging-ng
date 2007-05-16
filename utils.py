import re
from django.conf import settings

# Python 2.3 compatibility
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

find_tag_re = re.compile('[-\w]+', re.U)

class DummyTag:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

def create_dummy_tags(tag_list):
    """
    Given a string of tag names, creates a list of dummy tag objects
    with ``name`` attributes.

    This can be used to reuse an item's list of tag names for display
    purposes instead of loading tags from the database.
    """
    tag_names = set(split_tag_list(tag_list))
    return [DummyTag(tag_name) for tag_name in tag_names]

def get_tag_name_list(tag_names):
    """
    Find tag names in the given string and return them as a list.
    """
    if not isinstance(tag_names, unicode) and tag_names is not None:
        tag_names = tag_names.decode(settings.DEFAULT_CHARSET)
    results = find_tag_re.findall(tag_names or '')
    return [item.encode(settings.DEFAULT_CHARSET) for item in results]