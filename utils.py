import re

# Python 2.3 compatibility
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

find_tag_re = re.compile('[-\w]+')

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

    >>> get_tag_name_list(None)
    []
    >>> get_tag_name_list('')
    []
    >>> get_tag_name_list('foo')
    ['foo']
    >>> get_tag_name_list('foo bar')
    ['foo', 'bar']
    >>> get_tag_name_list('foo,bar')
    ['foo', 'bar']
    >>> get_tag_name_list(',  , foo   ,   bar ,  ,baz, , ,')
    ['foo', 'bar', 'baz']
    """
    return find_tag_re.findall(tag_names or '')