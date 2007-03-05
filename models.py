"""
Models for generic tagging.
"""
import urllib
from django.db import backend, models

# Models
from django.contrib.contenttypes.models import ContentType

class TagManager(models.Manager):
    def update_tags(self, obj, tag_list):
        """
        Update tags associated with an object, where the updated list
        of tags is given as a space-delimited string.
        """
        ctype = ContentType.objects.get_for_model(obj)
        current_tags = list(self.filter(items__content_type__pk=ctype.id,
                                        items__object_id=obj.id))
        updated_tag_names = []
        if tag_list != None:
            updated_tag_names = tag_list.split()

        # Remove tags which no longer apply
        tags_for_removal = [tag for tag in current_tags \
                            if tag.name not in updated_tag_names]
        if len(tags_for_removal) > 0:
            TaggedItem.objects.filter(content_type__pk=ctype.id,
                                      object_id=obj.id,
                                      tag__in=tags_for_removal).delete()

        # Add new tags
        current_tag_names = [tag.name for tag in current_tags]
        for tag_name in updated_tag_names:
            if tag_name not in current_tag_names:
                tag, created = self.get_or_create(name=tag_name)
                TaggedItem.objects.create(tag=tag, object=obj)

    def get_for_object(self, obj):
        """
        Create a queryset matching all tags associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(items__content_type__pk=ctype.id,
                           items__object_id=obj.id)

    def usage_for_model(self, Model, counts=True):
        """
        Create a queryset matching all tags associated with instances
        of the given Model.

        If ``counts`` is True, a 'count' attribute will be added to
        each tag, indicating how many times it has been used.
        """
        ctype = ContentType.objects.get_for_model(Model)
        qs = self.filter(items__content_type__pk=ctype.id)
        if counts is True:
            qs = qs.extra(
                select={
                    'count': 'SELECT COUNT(*) FROM tagged_item ' \
                             ' WHERE tagged_item.tag_id = tag.id ' \
                             ' AND tagged_item.content_type_id = %s',
                },
                params=[ctype.id],
            )
        return qs

class Tag(models.Model):
    name = models.SlugField(maxlength=50, unique=True)

    objects = TagManager()

    class Meta:
        db_table = 'tag'

    class Admin:
        pass

    def __str__(self):
        return self.name

class TaggedItemManager(models.Manager):
    def get_by_model(self, Model, tag):
        """
        Create a queryset matching instances of the given Model
        associated the given Tag.
        """
        qn = backend.quote_name
        ctype = ContentType.objects.get_for_model(Model)
        opts = self.model._meta
        return Model.objects.extra(
            tables=[opts.db_table], # Use a non-explicit join
            where=[
                '%s.content_type_id = %%s' % qn(opts.db_table),
                '%s.tag_id = %%s' % qn(opts.db_table),
                '%s.%s = %s.object_id' % (qn(Model._meta.db_table),
                                          qn(Model._meta.pk.column),
                                          qn(opts.db_table))
            ],
            params=[ctype.id, tag.id],
        )

class TaggedItem(models.Model):
    tag = models.ForeignKey(Tag, related_name='items')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = models.GenericForeignKey('content_type', 'object_id')

    objects = TaggedItemManager()

    class Meta:
        db_table = 'tagged_item'
        unique_together = (('tag', 'content_type', 'object_id'),)

    class Admin:
        pass

    def __str__(self):
        return '%s [%s]' % (self.object, self.tag)