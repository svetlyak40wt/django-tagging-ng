=================
Django Tagging NG
=================

This is a enhanced tagging application for Django projects

- For installation instructions, see the file "INSTALL.txt" in this directory

- For detailed instructions on how to configure and know all possibilities of this application, see the file "OVERVIEW.txt"


Rquirements
-----------
Note that this application requires Python 2.3 or later, and Django 0.96 or later. You can obtain Python from http://www.python.org/ and Django from http://www.djangoproject.com/.


Quickstart
----------

1.- Register a model:

   from django.db import models
   import tagging
   from shop.apps.products.models import Widget

   class Widget(models.Model):
       name = models.CharField(max_length=50)

   tagging.register(Widget)

2.- Use it

   w = Widget.objects.get(...)

   from tagging.models import Tag, TaggedItem
   house_tag = Tag.objects.get(name='house')
   thing_tag = Tag.objects.get(name='thing')

    - Set tags for instance:
    w.tags = 'tag1 tag2'

    - Get tag for instance:
    w.tags
     [<Tag: tag1>, <Tag: tag2>]

    - Retrive instances with tag1 AND tag2
   TaggedItem.objects.get_by_model(Widget, [house_tag, thing_tag])
   [<Widget: pk=1>]

    - Retrieve filtered instances with 'tag1'
   TaggedItem.objects.get_by_model(Widget.objects.filter(price__lt=50), 'house')


    - Get all tags for a model:
   Widget.tags.all()
   [<Tag: tag1>, <Tag: tag2>>]

    - Get tags for a model with usage counts:
    Widget.tags.count()

    - Get related tags (retrieve tags used by model instances which are also tagged with tag1 and tag2)
    Widget.tags.related(['tag1', 'tag2'], counts=True, min_count=3)


Authors
-------

This application is based on the original code, written by:
    Jonathan Buchanan <jonathan.buchanan@gmail.com>

Enhanced by:
    Alexander Artemenko <svetlyak.40wt@gmail.com>
    Antti Kaihola <akaihol+django@ambitone.com>
    GW [http://gw.tnode.com/] <gw.2012@tnode.com>
    Concha Labra https://github.com/clabra

Sources
-------

Django-tagging-ng: http://github.com/svetlyak40wt/django-tagging-ng/
Django-tagging:    http://code.google.com/p/django-tagging/

