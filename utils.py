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