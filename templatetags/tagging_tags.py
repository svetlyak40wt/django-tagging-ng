from django.db.models import get_model
from django.template import Library, Node, TemplateSyntaxError, resolve_variable

from tagging.models import Tag, TaggedItem

register = Library()

class TagsForObjectNode(Node):
    def __init__(self, object, context_var):
        self.object = object
        self.context_var = context_var

    def render(self, context):
        self.object = resolve_variable(self.object, context)
        context[self.context_var] = Tag.objects.get_for_object(self.object)
        return ''

class TaggedObjectsNode(Node):
    def __init__(self, tag, model, context_var):
        self.tag = tag
        self.context_var = context_var
        self.model = get_model(*model.split('.'))

    def render(self, context):
        self.tag = resolve_variable(self.tag, context)
        context[self.context_var] = TaggedItem.objects.get_by_model(self.model,
                                                                    self.tag)
        return ''

@register.tag(name='tags_for_object')
def do_tags_for_object(parser, token):
    """
    Retrieves a list of Tag objects associated with an object and
    stores them in a context variable.

    Example usage::

        {% tags_for_object foo_object as tag_list %}
    """
    bits = token.contents.split()
    if len(bits) != 4:
        raise TemplateSyntaxError('%s tag requires exactly three arguments' % bits[0])
    if bits[2] != 'as':
        raise TemplateSyntaxError("second argument to %s tag must be 'as'" % bits[0])
    return TagsForObjectNode(bits[1], bits[3])

@register.tag(name='tagged_objects')
def do_tagged_objects(parser, token):
    """
    Retrieves a list of objects for a given Model which are tagged with
    a given Tag and stores them in a context variable.

    The tag must be an instance of a ``Tag``, not the name of a tag.

    The model is specified in ``[appname].[modelname]`` format.

    Example usage::

        {% tagged_objects foo_tag in tv.Model as object_list %}
    """
    bits = token.contents.split()
    if len(bits) != 6:
        raise TemplateSyntaxError('%s tag requires exactly five arguments' % bits[0])
    if bits[2] != 'for':
        raise TemplateSyntaxError("second argument to %s tag must be 'in'" % bits[0])
    if bits[4] != 'as':
        raise TemplateSyntaxError("fourth argument to %s tag must be 'as'" % bits[0])
    return TaggedObjectsNode(bits[1], bits[3], bits[5])