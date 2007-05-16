import re
from django.conf import settings

# Python 2.3 compatibility
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

find_tag_re = re.compile('[-\w]+', re.U)

def get_tag_name_list(tag_names):
    """
    Find tag names in the given string and return them as a list.
    """
    if not isinstance(tag_names, unicode) and tag_names is not None:
        tag_names = tag_names.decode(settings.DEFAULT_CHARSET)
    results = find_tag_re.findall(tag_names or '')
    return [item.encode(settings.DEFAULT_CHARSET) for item in results]