import math, re, types
from django.conf import settings
from django.db.models.query import QuerySet

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

def get_tag_list(tags):
    """
    Utility method for accepting tag input in a flexible manner.

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
                return Tag.objects.filter(name__in=tags)
            elif 'tag' in contents:
                return tags
            elif 'int' in contents:
                return Tag.objects.filter(id__in=tags)
        else:
            raise ValueError('If a list or tuple of tags is provided, they must all be tag names, Tag objects or Tag ids')
    else:
        raise ValueError('The tag input given was invalid')

# Font size distribution algorithms
LOGARITHMIC, LINEAR = 1, 2

def calculate_cloud(tags, steps=4, distribution=LOGARITHMIC):
    """
    Add a ``font_size`` attribute to each tag according to the
    frequency of its use, as indicated by its ``count``
    attribute.

    ``steps`` defines the range of font sizes - ``font_size`` will
    be an integer between 1 and ``steps`` (inclusive).

    ``distribution`` defines the type of font size distribution
    algorithm which will be used - logarithmic or linear. It must be
    either ``tagging.utils.LOGARITHMIC`` or ``tagging.utils.LINEAR``.

    The algorithm to scale the tags logarithmically is from a
    blog post by Anders Pearson, 'Scaling tag clouds':
    http://thraxil.com/users/anders/posts/2005/12/13/scaling-tag-clouds/
    """
    if len(tags) > 0:
        thresholds = []
        counts = [tag.count for tag in tags]
        max_weight = float(max(counts))
        min_weight = float(min(counts))

        # Set up the appropriate thresholds
        if distribution == LOGARITHMIC:
            thresholds = [math.pow(max_weight - min_weight + 1, float(i) / float(steps)) \
                          for i in range(1, steps + 1)]
        elif distribution == LINEAR:
            delta = (max_weight - min_weight) / float(steps)
            thresholds = [min_weight + i * delta for i in range(1, steps + 1)]
        else:
            raise ValueError('Invalid font size distribution algorithm specified: %s' % distribution)

        for tag in tags:
            font_set = False
            for i in range(steps):
                if not font_set and tag.count <= thresholds[i]:
                    tag.font_size = i + 1
                    font_set = True
    return tags