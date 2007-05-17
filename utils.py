import math, re
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

def calculate_cloud(tags, steps=4):
    """
    Add a ``font_size`` attribute to each tag according to the
    frequency of its use, as indicated by its ``count``
    attribute.

    ``steps`` defines the range of font sizes - ``font_size`` will
    be an integer between 1 and ``steps`` (inclusive).

    The log based tag cloud calculation used is from
    http://www.car-chase.net/2007/jan/16/log-based-tag-clouds-python/
    """
    if len(tags) > 0:
        new_thresholds, results = [], []
        temp = [tag.count for tag in tags]
        max_weight = float(max(temp))
        min_weight = float(min(temp))
        new_delta = (max_weight - min_weight)/float(steps)
        for i in range(steps + 1):
            new_thresholds.append((100 * math.log((min_weight + i * new_delta) + 2), i))
        for tag in tags:
            font_set = False
            for threshold in new_thresholds[1:int(steps)+1]:
                if (100 * math.log(tag.count + 2)) <= threshold[0] and not font_set:
                    tag.font_size = threshold[1]
                    font_set = True
    return tags