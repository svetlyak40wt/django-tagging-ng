"""
Models for generic tagging.
"""
import math
from django.db import backend, connection, models
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from tagging.utils import get_tag_name_list

# Generic relations were moved in Django revision 5172
try:
    from django.contrib.contenttypes import generic
except ImportError:
    import django.db.models as generic

# Python 2.3 compatibility
if not hasattr(__builtins__, 'set'):
    from sets import Set as set

class TagManager(models.Manager):
    def update_tags(self, obj, tag_names):
        """
        Update tags associated with an object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        current_tags = list(self.filter(items__content_type__pk=ctype.id,
                                        items__object_id=obj.id))
        updated_tag_names = set(get_tag_name_list(tag_names))

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

    def usage_for_model(self, Model, counts=False):
        """
        Create a queryset matching all tags associated with instances
        of the given Model.

        If ``counts`` is True, a ``count`` attribute will be added to
        each tag, indicating how many times it has been used against
        the Model in question.
        """
        ctype = ContentType.objects.get_for_model(Model)
        qs = self.filter(items__content_type__pk=ctype.id).distinct()
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

    def cloud_for_model(self, Model, steps=4):
        """
        Obtain a list of tags associated with instances of the given
        Model, giving each tag a ``count`` attribute indicating how
        many times it has been used and a ``font_size`` attribute for
        use in displaying a tag cloud.

        ``steps`` defines the range of font sizes - ``font_size`` will
        be an integer between 1 and ``steps`` (inclusive).
        """
        tags = list(self.usage_for_model(Model, counts=True))
        return self.calculate_cloud(tags, steps)

    def calculate_cloud(self, tags, steps=4):
        """
        Add a ``font_size`` attribute to each tag according to the
        frequency of its use, as indicated by its ``count``
        attribute.

        ``steps`` defines the range of font sizes - ``font_size`` will
        be an integer between 1 and ``steps`` (inclusive).

        The log based tag cloud calculation used is from
        http://www.car-chase.net/2007/jan/16/log-based-tag-clouds-python/
        """
        if len(tags) > 0:
            new_thresholds, results = [], []
            temp = [tag.count for tag in tags]
            max_weight = float(max(temp))
            min_weight = float(min(temp))
            new_delta = (max_weight - min_weight)/float(steps)
            for i in range(steps + 1):
                new_thresholds.append((100 * math.log((min_weight + i * new_delta) + 2), i))
            for tag in tags:
                font_set = False
                for threshold in new_thresholds[1:int(steps)+1]:
                    if (100 * math.log(tag.count + 2)) <= threshold[0] and not font_set:
                        tag.font_size = threshold[1]
                        font_set = True
        return tags

class Tag(models.Model):
    name = models.SlugField(maxlength=50, unique=True)

    objects = TagManager()

    class Meta:
        db_table = 'tag'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ('name',)

    class Admin:
        pass

    def __str__(self):
        return self.name

class TaggedItemManager(models.Manager):
    def get_by_model(self, Model, tag):
        """
        Create a queryset matching instances of the given Model
        associated with a given Tag or list of Tags.
        """
        if isinstance(tag, (list, tuple, QuerySet)):
            if len(tag) == 1: # Optimisation for single tag
                tag = tag[0]
            else:
                return self.get_intersection_by_model(Model, tag)
        ctype = ContentType.objects.get_for_model(Model)
        rel_table = backend.quote_name(self.model._meta.db_table)
        return Model.objects.extra(
            tables=[self.model._meta.db_table], # Use a non-explicit join
            where=[
                '%s.content_type_id = %%s' % rel_table,
                '%s.tag_id = %%s' % rel_table,
                '%s.%s = %s.object_id' % (backend.quote_name(Model._meta.db_table),
                                          backend.quote_name(Model._meta.pk.column),
                                          rel_table)
            ],
            params=[ctype.id, tag.id],
        )

    def get_intersection_by_model(self, Model, tags):
        """
        Create a queryset matching instances of the given Model
        associated with all the given list of Tags.

        FIXME The query currently used to grab the ids of objects
              which have all the tags should be all that we need run,
              using a non-explicit join for the QuerySet returned, as
              in get_by_model, but there's currently no way to get the
              required GROUP BY and HAVING clauses into Django's ORM.

              Once the ORM is capable of this, we should have a
              solution which requires only a single query and won't
              have the problem where the number of ids in the IN
              clause in the QuerySet could exceed the length allowed,
              as could currently happen.
        """
        rel_table = backend.quote_name(self.model._meta.db_table)
        model_table = backend.quote_name(Model._meta.db_table)
        model_pk = '%s.%s' % (model_table,
                              backend.quote_name(Model._meta.pk.column))
        tag_count = len(tags)
        # This query selects the ids of all objects which have all the
        # given tags.
        query = """
        SELECT %s
        FROM %s, %s
        WHERE %s.content_type_id = %%s
          AND %s.tag_id IN (%s)
          AND %s = %s.object_id
        GROUP BY %s
        HAVING COUNT(%s) = %%s""" % (
            model_pk,
            model_table, rel_table,
            rel_table,
            rel_table, ','.join(['%s'] * tag_count),
            model_pk, rel_table,
            model_pk,
            model_pk
        )
        ctype = ContentType.objects.get_for_model(Model)
        cursor = connection.cursor()
        cursor.execute(query,
                       [ctype.id] + [tag.id for tag in tags] + [tag_count])
        try:
            ids = cursor.fetchall()[0]
        except IndexError:
            ids = []
        return Model.objects.filter(pk__in=ids)

class TaggedItem(models.Model):
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

    def __str__(self):
        return '%s [%s]' % (self.object, self.tag)