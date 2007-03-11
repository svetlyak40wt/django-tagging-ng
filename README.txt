==============
Django Tagging
==============

A generic tagging application for Django projects, which allows
association of a number of tags with any ``Model`` instance and makes
retrieval of tags simple.


Tagging objects
===============

``TagManager`` methods
-----------------------

The ``Tag`` model's ``Manager`` object, accessible through its
``objects`` attribute, defines a method which may be used to tag
objects.

update_tags(obj, tag_list)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Updates tags associated with an object.

``tag_list`` is a string containing tag names with which ``obj``
should be tagged. Tag names must be valid slugs. Multiple tag names
may be specified, separated by any number of commas and spaces.

If ``tag_list`` is ``None``, the object's tags will be cleared.


Retrieving tagged objects
=========================

``TaggedItemManager`` methods
------------------------------

The ``TaggedItem`` model's ``Manager`` object, accessible through its
``objects`` attribute, defines methods which may be used to retrieve
objects based on the ``Tag`` objects they are tagged with.

``get_by_model(Model, tag)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``tag`` is an instance of a ``Tag``, returns a ``QuerySet``
containing all instances of ``Model`` which are tagged with ``tag``.

If ``tag`` is a list of tags, returns a ``QuerySet`` containing all
instances of ``Model`` which are tagged with every tag in the list.


Retrieving tags
===============

``TagManager`` methods
-----------------------

The ``Tag`` model's ``Manager`` object also defines methods which may
be used to retrieve ``Tag`` objects.

get_for_object(obj)
~~~~~~~~~~~~~~~~~~~

Returns a ``QuerySet`` containing all ``Tag`` objects associated with
``obj``.

usage_for_model(Model, counts=True)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a ``QuerySet`` containing the distinct ``Tag`` objects
associated with all instances of model ``Model``.

If ``counts`` is ``True``, a ``count`` attribute will be added to each
``Tag``, indicating how many times it has been associated with all
instances of ``Model``.

cloud_for_model(Model, steps=4)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a list of the distinct ``Tag`` objects associated with all
instances of ``Model``, each having along a ``count`` attribute as
above and an additional ``font_size`` attribute, for use in creation
of a tag cloud (a weighted list).

``steps`` defines the number of font sizes available - ``font_size``
may be an integer between ``1`` and ``steps``, inclusive.

The algorithm used to calculate font sizes is from a blog post by
Chase Davis, `Log-based tag clouds in Python`_.

.. _`Log-based tag clouds in Python`: http://www.car-chase.net/2007/jan/16/log-based-tag-clouds-python/


Fields
======

The ``tagging.fields`` module contains fields which make it easy to
integrate tagging into your models and into the
``django.contrib.admin`` application.

Field types
-----------

``TagField``
~~~~~~~~~~~~

A ``CharField`` that actually works as a relationship to tags "under
the hood".

Using this example model::

    class Link(models.Model):
        ...
        tags = TagField()

Setting tags::

    >>> l = Link.objects.get(...)
    >>> l.tags = 'tag1 tag2 tag3'

Getting tags for an instance::

    >>> l.tags
    'tag1 tag2 tag3'

Getting tags for a model - i.e. all tags used by all instances of the
model::

    >>> Link.tags
    'tag1 tag2 tag3 tag4 tag5'

This field will also validate that it has been given a valid list of
tag names, separated by a single comma, a single space or a comma
followed by a space, using the ``isTagList`` validator from
``tagging.validators``.


Simplified tagging and retrieval of tags with properties
========================================================

If you're not using ``TagField``, a useful method for simplifying
tagging and retrieval of tags for your models is to set up a property::

    from django.db import models
    from tagging.models import Tag

    class MyModel(models.Model):
        name = models.CharField(maxlength=100)
        tag_list = models.CharField(maxlength=255)

        def save(self):
            super(MyModel, self).save()
            self.tags = self.tag_list

        def _get_tags(self):
            return Tag.objects.get_for_object(self)

        def _set_tags(self, tag_list):
            Tag.objects.update_tags(self, tag_list)

        tags = property(_get_tags, _set_tags)

        def __str__(self):
            return self.name

Once you've set this up, you can access and set tags in a fairly
natural way::

    >>> obj = MyModel.objects.get(pk=1)
    >>> obj.tags = 'foo bar'
    >>> obj.tags
    [<Tag: foo>, <Tag: bar>]

Remember that ``obj.tags`` will return a ``QuerySet``, so you can
perform further filtering on it, should you need to.