import math
import re
import types

from django.db.models.query import QuerySet
from django.utils.encoding import force_unicode, smart_unicode

# Python 2.3 compatibility
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

find_tag_re = re.compile(r'[-\w]+', re.U)

def get_tag_name_list(tag_names):
    """
    Finds tag names in the given string and return them as a list.
    """
    if tag_names is not None:
        tag_names = force_unicode(tag_names)
    results = find_tag_re.findall(tag_names or '')
    return results

def get_tag_list(tags):
    """
    Utility function for accepting tag input in a flexible manner.

    If a ``Tag`` object is given, it will be returned in a list as
    its single occupant.

    If given, the tag names in the following will be used to create a
    ``Tag`` ``QuerySet``:

        * A string, which may contain multiple tag names.
        * A list or tuple of strings corresponding to tag names.
        * A list or tuple of integers corresponding to tag ids.

    If given, the following will be returned as-is:

        * A list or tuple of ``Tag`` objects.
        * A ``Tag`` ``QuerySet``.
    """
    from tagging.models import Tag
    if isinstance(tags, Tag):
        return [tags]
    elif isinstance(tags, QuerySet) and tags.model is Tag:
        return tags
    elif isinstance(tags, types.StringTypes):
        return Tag.objects.filter(name__in=get_tag_name_list(tags))
    elif isinstance(tags, (types.ListType, types.TupleType)):
        if len(tags) == 0:
            return tags
        contents = set()
        for item in tags:
            if isinstance(item, types.StringTypes):
                contents.add('string')
            elif isinstance(item, Tag):
                contents.add('tag')
            elif isinstance(item, (types.IntType, types.LongType)):
                contents.add('int')
        if len(contents) == 1:
            if 'string' in contents:
                return Tag.objects.filter(name__in=[smart_unicode(tag) \
                                                    for tag in tags])
            elif 'tag' in contents:
                return tags
            elif 'int' in contents:
                return Tag.objects.filter(id__in=tags)
        else:
            raise ValueError(u'If a list or tuple of tags is provided, they must all be tag names, Tag objects or Tag ids.')
    else:
        raise ValueError(u'The tag input given was invalid.')

def get_tag(tag):
    """
    Utility function for accepting single tag input in a flexible
    manner.

    If a ``Tag`` object is given it will be returned as-is; if a
    string or integer are given, they will be used to lookup the
    appropriate ``Tag``.

    If no matching tag can be found, ``None`` will be returned.
    """
    from tagging.models import Tag
    if isinstance(tag, Tag):
        return tag

    try:
        if isinstance(tag, types.StringTypes):
            return Tag.objects.get(name=tag)
        elif isinstance(tag, (types.IntType, types.LongType)):
            return Tag.objects.get(id=tag)
    except Tag.DoesNotExist:
        pass

    return None

# Font size distribution algorithms
LOGARITHMIC, LINEAR = 1, 2

def _calculate_thresholds(min_weight, max_weight, steps):
    delta = (max_weight - min_weight) / float(steps)
    return [min_weight + i * delta for i in range(1, steps + 1)]

def _calculate_tag_weight(weight, max_weight, distribution):
    """
    Logarithmic tag weight calculation is based on code from the
    `Tag Cloud`_ plugin for Mephisto, by Sven Fuchs.

    .. _`Tag Cloud`: http://www.artweb-design.de/projects/mephisto-plugin-tag-cloud
    """
    if distribution == LINEAR or max_weight == 1:
        return weight
    elif distribution == LOGARITHMIC:
        return math.log(weight) * max_weight / math.log(max_weight)
    raise ValueError(u'Invalid distribution algorithm specified: %s.' % distribution)

def calculate_cloud(tags, steps=4, distribution=LOGARITHMIC):
    """
    Add a ``font_size`` attribute to each tag according to the
    frequency of its use, as indicated by its ``count``
    attribute.

    ``steps`` defines the range of font sizes - ``font_size`` will
    be an integer between 1 and ``steps`` (inclusive).

    ``distribution`` defines the type of font size distribution
    algorithm which will be used - logarithmic or linear. It must be
    one of ``tagging.utils.LOGARITHMIC`` or ``tagging.utils.LINEAR``.
    """
    if len(tags) > 0:
        counts = [tag.count for tag in tags]
        min_weight = float(min(counts))
        max_weight = float(max(counts))
        thresholds = _calculate_thresholds(min_weight, max_weight, steps)
        for tag in tags:
            font_set = False
            tag_weight = _calculate_tag_weight(tag.count, max_weight, distribution)
            for i in range(steps):
                if not font_set and tag_weight <= thresholds[i]:
                    tag.font_size = i + 1
                    font_set = True
    return tags
