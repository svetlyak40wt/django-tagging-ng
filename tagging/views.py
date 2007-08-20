from django.http import Http404
from django.views.generic.list_detail import object_list

from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

def tagged_object_list(request, model=None, tag=None, related_tags=False,
        related_tag_counts=True, **kwargs):
    """
    A thin wrapper around
    ``django.views.generic.list_detail.object_list`` which creates a
    ``QuerySet`` containing instances of the given model tagged with
    the given tag.

    In addition to the context variables set up by ``object_list``, a
    ``tag`` context variable will contain the ``Tag`` instance
    for the given tag.

    If ``related_tags`` is ``True``, a ``related_tags`` context variable
    will contain tags related to the given tag for the given model.
    Additionally, if ``related_tag_counts`` is ``True``, each related tag
    will have a ``count`` attribute indicating the number of items which
    have it in addition to the given tag.
    """
    if model is None:
        try:
            model = kwargs['model']
        except KeyError:
            raise AttributeError(u'tagged_object_list must be called with a model.')

    if tag is None:
        try:
            tag = kwargs['tag']
        except KeyError:
            raise AttributeError(u'tagged_object_list must be called with a tag.')

    tag_instance = get_tag(tag)
    if tag_instance is None:
        raise Http404(u'No Tag found matching "%s".' % tag)
    queryset = TaggedItem.objects.get_by_model(model, tag_instance)
    if not kwargs.has_key('extra_context'):
        kwargs['extra_context'] = {}
    kwargs['extra_context']['tag'] = tag_instance
    if related_tags:
        kwargs['extra_context']['related_tags'] = \
            Tag.objects.related_for_model(tag_instance, model,
                                          counts=related_tag_counts)
    return object_list(request, queryset, **kwargs)
