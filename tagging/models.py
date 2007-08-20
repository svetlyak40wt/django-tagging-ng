"""
Models for generic tagging.
"""
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from tagging.managers import TagManager, TaggedItemManager
from tagging.validators import isTag

class Tag(models.Model):
    """
    A basic tag.
    """
    name = models.CharField(max_length=50, unique=True, db_index=True, validator_list=[isTag])

    objects = TagManager()

    class Meta:
        db_table = 'tag'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ('name',)

    class Admin:
        pass

    def __unicode__(self):
        return self.name

class TaggedItem(models.Model):
    """
    Holds the relationship between a tag and the item being tagged.
    """
    tag = models.ForeignKey(Tag, related_name='items')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')

    objects = TaggedItemManager()

    class Meta:
        db_table = 'tagged_item'
        verbose_name = 'Tagged Item'
        verbose_name_plural = 'Tagged Items'
        # Enforce unique tag association per object
        unique_together = (('tag', 'content_type', 'object_id'),)

    class Admin:
        pass

    def __unicode__(self):
        return u'%s [%s]' % (self.object, self.tag)
