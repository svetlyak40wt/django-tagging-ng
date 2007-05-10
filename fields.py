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

        # Save tags back to the database post-save
        dispatcher.connect(self._save, signal=signals.post_save, sender=cls)

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
        # Handle access on the model (i.e. Link.tags)
        if instance is None:
            return tags2str(Tag.objects.usage_for_model(owner))

        tags = self._get_instance_tag_cache(instance)
        if tags is None:
            if instance._get_pk_val() is None:
                self._set_instance_tag_cache(instance, "")
            else:
                self._set_instance_tag_cache(instance, tags2str(Tag.objects.get_for_object(instance)))
        return self._get_instance_tag_cache(instance)

    def __set__(self, instance, value):
        """
        Set an object's tags.
        """
        if instance is None:
            raise AttributeError("%s can only be set on instances." % self.name)
        self._set_instance_tag_cache(instance, value)

    def _save(self, signal, sender, instance):
        """
        Save tags back to the database
        """
        tags = self._get_instance_tag_cache(instance)
        if tags is not None :
            Tag.objects.update_tags(instance, tags)

    def __delete__(self, instance):
        """
        Clear all of an object's tags.
        """
        self._set_instance_tag_cache(instance, "")

    def _get_instance_tag_cache(self, instance):
        """
        Helper: get an instance's tag cache.
        """
        return getattr(instance, "_%s_cache" % self.attname, None)

    def _set_instance_tag_cache(self, instance, tags):
        """
        Helper: set and instance's tag cache.
        """
        setattr(instance, "_%s_cache" % self.attname, tags)

    def get_internal_type(self):
        return "CharField"

# Helper
def tags2str(tagset):
    return " ".join(t.name for t in tagset)