"""
Models for generic tagging.
"""
import types
from django.db import backend, connection, models
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from tagging.utils import calculate_cloud, get_tag_name_list, get_tag_list, LOGARITHMIC
from tagging.validators import isTag

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

    def related_for_model(self, tags, Model, counts=False):
        """
        Obtain a list of tags related to a given list of tags - that
        is, other tags used by items which have all the given tags.

        If ``counts`` is True, a ``count`` attribute will be added to
        each tag, indicating the number of items which have it in
        addition to the given list of tags.
        """
        tags = get_tag_list(tags)
        tag_count = len(tags)
        ctype = ContentType.objects.get_for_model(Model)
        count_select = ''
        if counts is True:
            count_select = ', COUNT(ti.object_id)'
        query = """
        SELECT t.id, t.name%s
        FROM tagged_item ti INNER JOIN tag t ON ti.tag_id = t.id
        WHERE ti.content_type_id = %s
          AND ti.object_id IN
          (
              SELECT tagged_item.object_id
              FROM tagged_item, tag
              WHERE tagged_item.content_type_id = %s
                AND tag.id = tagged_item.tag_id
                AND tag.id IN (%s)
              GROUP BY tagged_item.object_id
              HAVING COUNT(tagged_item.object_id) = %s
          )
          AND t.id NOT IN (%s)
        GROUP BY t.id
        ORDER BY 2 ASC""" % (
            count_select, ctype.id,
            ctype.id, ','.join(['%s'] * tag_count), tag_count,
            ','.join(['%s'] * tag_count)
        )

        cursor = connection.cursor()
        cursor.execute(query, [tag.id for tag in tags] * 2)
        related = []
        for row in cursor.fetchall():
            tag = Tag(*row[:2])
            if counts is True:
                tag.count = row[2]
            related.append(tag)
        return related

    def cloud_for_model(self, Model, steps=4, distribution=LOGARITHMIC):
        """
        Obtain a list of tags associated with instances of the given
        Model, giving each tag a ``count`` attribute indicating how
        many times it has been used and a ``font_size`` attribute for
        use in displaying a tag cloud.

        ``steps`` defines the range of font sizes - ``font_size`` will
        be an integer between 1 and ``steps`` (inclusive).

        ``distribution`` defines the type of font size distribution
        algorithm which will be used - logarithmic or linear. It must
        be either ``tagging.utils.LOGARITHMIC`` or
        ``tagging.utils.LINEAR``.
        """
        tags = list(self.usage_for_model(Model, counts=True))
        return calculate_cloud(tags, steps)

class Tag(models.Model):
    name = models.CharField(maxlength=50, unique=True, db_index=True, validator_list=[isTag])

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
    def get_by_model(self, Model, tags):
        """
        Create a queryset matching instances of the given Model
        associated with a given Tag or list of Tags.
        """
        tags = get_tag_list(tags)
        if len(tags) == 1:
            tag = tags[0] # Optimisation for single tag
        else:
            return self.get_intersection_by_model(Model, tags)
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
        tags = get_tag_list(tags)
        tag_count = len(tags)
        rel_table = backend.quote_name(self.model._meta.db_table)
        model_table = backend.quote_name(Model._meta.db_table)
        model_pk = '%s.%s' % (model_table,
                              backend.quote_name(Model._meta.pk.column))
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
            ids = [row[0] for row in cursor.fetchall()]
        except IndexError:
            ids = []
        return Model.objects.filter(pk__in=ids)

    def get_related(self, obj, Model, num=None):
        """
        Retrieve instances of ``Model`` which share tags with the
        model instance ``obj``, ordered by the number of shared tags
        in descending order.

        If ``num`` is given, a maximum of ``num`` instances will be
        returned.
        """
        ctype = ContentType.objects.get_for_model(obj)
        related_ctype = ContentType.objects.get_for_model(Model)
        related_table = backend.quote_name(Model._meta.db_table)
        query = """
        SELECT %s.id, COUNT(related_tagged_item.object_id) AS count
        FROM %s, tagged_item, tag, tagged_item related_tagged_item
        WHERE tagged_item.object_id = %s
          AND tagged_item.content_type_id =  %s
          AND tag.id = tagged_item.tag_id
          AND related_tagged_item.content_type_id = %s
          AND related_tagged_item.tag_id = tagged_item.tag_id
          AND %s.id = related_tagged_item.object_id""" % (
              related_table, related_table, obj.id, ctype.id, related_ctype.id, related_table
        )
        if ctype.id == related_ctype.id:
            query += """
            AND related_tagged_item.object_id != tagged_item.object_id"""
        query += """
        GROUP BY related_tagged_item.object_id
        ORDER BY count DESC"""

        cursor = connection.cursor()
        cursor.execute(query, [])
        if num is not None:
            object_ids = [row[0] for row in cursor.fetchall()[:num]]
        else:
            object_ids = [row[0] for row in cursor.fetchall()]

        # Use in_bulk here instead of an id__in lookup, because id__in would
        # clobber the ordering.
        object_dict = Model._default_manager.in_bulk(object_ids)
        return [object_dict[object_id] for object_id in object_ids]

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