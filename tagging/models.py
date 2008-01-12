"""
Models for generic tagging.
"""
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from tagging.managers import TagManager, TaggedItemManager
from tagging.validators import isTag

class Tag(models.Model):
    """
    A tag.
    """
    name = models.CharField(_('name'), max_length=50, unique=True, db_index=True, validator_list=[isTag])

    objects = TagManager()

    class Meta:
        ordering = ('name',)
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    class Admin:
        pass

    def __unicode__(self):
        return self.name

class TaggedItem(models.Model):
    """
    Holds the relationship between a tag and the item being tagged.
    """
    tag          = models.ForeignKey(Tag, verbose_name=_('tag'), related_name='items')
    content_type = models.ForeignKey(ContentType, verbose_name=_('content type'))
    object_id    = models.PositiveIntegerField(_('object id'), db_index=True)
    object       = generic.GenericForeignKey('content_type', 'object_id')

    objects = TaggedItemManager()

    class Meta:
        # Enforce unique tag association per object
        unique_together = (('tag', 'content_type', 'object_id'),)
        verbose_name = _('tagged item')
        verbose_name_plural = _('tagged items')

    class Admin:
        pass

    def __unicode__(self):
        return u'%s [%s]' % (self.object, self.tag)
