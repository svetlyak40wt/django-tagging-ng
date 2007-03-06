import re

# Python 2.3 compatibility
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

split_tag_re = re.compile('[\s,]+')

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

def split_tag_list(tag_list):
    """
    Split the given list of tags on whitespace and commas and return
    a list of tags.

    >>> split_tag_list(None)
    []
    >>> split_tag_list('')
    []
    >>> split_tag_list('foo')
    ['foo']
    >>> split_tag_list('foo bar')
    ['foo', 'bar']
    >>> split_tag_list('foo,bar')
    ['foo', 'bar']
    >>> split_tag_list(',  , foo   ,   bar ,  ,baz, , ,')
    ['foo', 'bar', 'baz']
    """
    return [t for t in split_tag_re.split(tag_list or '') if t]