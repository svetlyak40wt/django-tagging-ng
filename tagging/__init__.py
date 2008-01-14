from django.utils.translation import ugettext as _

from tagging.managers import ModelTagManager, ModelTaggedItemManager

VERSION = (0, 3, 'pre')

class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model more than once.
    """
    pass

registry = []

def register(model, tag_descriptor_attr='tags',
             tagged_item_manager_attr='tagged'):
    """
    Sets the given model class up for working with tags.
    """
    if model in registry:
        raise AlreadyRegistered(
            _('The model %s has already been registered with tagging.') % model.__name__)
    registry.append(model)

    # Add tag descriptor
    setattr(model, tag_descriptor_attr, TagDescriptor())

    # Add custom manager
    ModelTaggedItemManager().contribute_to_class(model,
                                                 tagged_item_manager_attr)

class TagDescriptor(object):
    """
    A descriptor which provides access to a ``ModelTagManager`` for
    model classes and simple retrieval, updating and deletion of tags
    for model instances.
    """
    def __get__(self, instance, owner):
        if not instance:
            tag_manager = ModelTagManager()
            tag_manager.model = owner
            return tag_manager
        else:
            return Tag.objects.get_for_object(instance)

    def __set__(self, instance, value):
        Tag.objects.update_tags(instance, value)

    def __del__(self, instance):
        Tag.objects.update_tags(instance, None)
