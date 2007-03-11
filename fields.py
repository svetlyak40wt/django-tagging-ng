from django.db.models.fields import CharField
from tagging.validators import isTagList
from tagging.models import Tag
from django.dispatch import dispatcher
from django.db.models import signals

class TagField(CharField):
    """
    A "special" character field that actually works as a relationship to tags
    "under the hood". This exposes a space-separated string of tags, but does
    the splitting/reordering/etc. under the hood.
    """

    def __init__(self, **kwargs):
        kwargs["maxlength"] = kwargs.get("maxlength", 255)
        kwargs["blank"] = kwargs.get("blank", True)
        kwargs["validator_list"] = [isTagList] + kwargs.get("validator_list", [])
        super(TagField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        super(TagField, self).contribute_to_class(cls, name)

        # Make this object the descriptor for field access.
        setattr(cls, self.name, self)

        # Make sure to clean up the TaggedItems after the object is deleted.
        dispatcher.connect(self.__delete__, signal=signals.post_delete, sender=cls)

    def __get__(self, instance, owner=None):
        """
        Tag getter. Returns an instance's tags if accessed on an instance, and
        all of a model's tags if called on a class. That is, this model::

            class Link(models.Model):
                ...
                tags = TagField()


        Lets you do both of these::

            >>> l = Link.objects.get(...)
            >>> l.tags
            "tag1 tag2 tag3"

            >>> Link.tags
            "tag1 tag2 tag3 tag4"

        """
        if instance is not None:
            tags = Tag.objects.get_for_object(instance)
        else:
            tags = Tag.objects.usage_for_model(type(instance))
        return " ".join(map(str, tags))

    def __set__(self, instance, value):
        """
        Set an object's tags.
        """
        if instance is None:
            raise AttributeError("%s can only be set on instances." % self.name)
        Tag.objects.update_tags(instance, value)

    def __delete__(self, instance):
        """
        Clear all of an object's tags.
        """
        if instance is None:
            raise AttributeError("%s can only be cleared on instances." % self.name)
        Tag.objects.update_tags(instance, "")

    def get_internal_type(self):
        return "CharField"