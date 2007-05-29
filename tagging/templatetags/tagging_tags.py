from django.db.models import get_model
from django.template import Library, Node, TemplateSyntaxError, resolve_variable
from tagging.models import Tag, TaggedItem

register = Library()

class TagsForModelNode(Node):
    def __init__(self, model, context_var, counts):
        self.model = model
        self.context_var = context_var
        self.counts = counts

    def render(self, context):
        model = get_model(*self.model.split('.'))
        context[self.context_var] = Tag.objects.usage_for_model(model, counts=self.counts)
        return ''

class TagsForObjectNode(Node):
    def __init__(self, obj, context_var):
        self.obj = obj
        self.context_var = context_var

    def render(self, context):
        obj = resolve_variable(self.obj, context)
        context[self.context_var] = Tag.objects.get_for_object(obj)
        return ''

class TaggedObjectsNode(Node):
    def __init__(self, tag, model, context_var):
        self.tag = tag
        self.context_var = context_var
        self.model = model

    def render(self, context):
        tag = resolve_variable(self.tag, context)
        model = get_model(*self.model.split('.'))
        context[self.context_var] = TaggedItem.objects.get_by_model(model,
                                                                    tag)
        return ''

def do_tags_for_model(parser, token):
    """
    Retrieves a list of ``Tag`` objects associated with a given model
    and stores them in a context variable.

    The model is specified in ``[appname].[modelname]`` format.

    If specified - by providing extra ``with counts`` arguments - adds
    a ``count`` attribute to each tag containing the number of
    instances of the given model which have been tagged with it.

    Example usage::

        {% tags_for_model products.Widget as widget_tags %}

        {% tags_for_model products.Widget as widget_tags with counts %}
    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits not in (4, 6):
        raise TemplateSyntaxError('%s tag requires either three or five arguments' % bits[0])
    if bits[2] != 'as':
        raise TemplateSyntaxError("second argument to %s tag must be 'as'" % bits[0])
    if len_bits == 6:
        if bits[4] != 'with':
            raise TemplateSyntaxError("if given, fourth argument to %s tag must be 'with'" % bits[0])
        if bits[5] != 'counts':
            raise TemplateSyntaxError("if given, fifth argument to %s tag must be 'counts'" % bits[0])
    if len_bits == 4:
        return TagsForModelNode(bits[1], bits[3], counts=False)
    else:
        return TagsForModelNode(bits[1], bits[3], counts=True)

def do_tags_for_object(parser, token):
    """
    Retrieves a list of ``Tag`` objects associated with an object and
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
    if bits[2] != 'in':
        raise TemplateSyntaxError("second argument to %s tag must be 'in'" % bits[0])
    if bits[4] != 'as':
        raise TemplateSyntaxError("fourth argument to %s tag must be 'as'" % bits[0])
    return TaggedObjectsNode(bits[1], bits[3], bits[5])

register.tag('tags_for_model', do_tags_for_model)
register.tag('tags_for_object', do_tags_for_object)
register.tag('tagged_objects', do_tagged_objects)