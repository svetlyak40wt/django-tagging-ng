# -*- coding: utf-8 -*-
r"""
>>> import os
>>> from tagging.models import Tag, TaggedItem
>>> from tagging.tests.models import Article, Link, Perch, Parrot
>>> from tagging.utils import calculate_cloud, get_tag_name_list, get_tag_list, LINEAR
>>> from tagging.validators import isTagList, isTag
>>> from tagging.forms import TagField

#############
# Utilities #
#############

# Tag input ###################################################################

# Tag names
>>> get_tag_name_list(None)
[]
>>> get_tag_name_list('')
[]
>>> get_tag_name_list('foo')
['foo']
>>> get_tag_name_list('foo bar')
['foo', 'bar']
>>> get_tag_name_list('foo,bar')
['foo', 'bar']
>>> get_tag_name_list(',  , foo   ,   bar ,  ,baz, , ,')
['foo', 'bar', 'baz']
>>> get_tag_name_list('foo,ŠĐĆŽćžšđ')
['foo', '\xc5\xa0\xc4\x90\xc4\x86\xc5\xbd\xc4\x87\xc5\xbe\xc5\xa1\xc4\x91']

# Tag objects
>>> cheese = Tag.objects.create(name='cheese')
>>> toast = Tag.objects.create(name='toast')
>>> get_tag_list(cheese)
[<Tag: cheese>]
>>> get_tag_list('cheese toast')
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list(u'cheese toast')
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list([])
[]
>>> get_tag_list(['cheese',  'toast'])
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list([cheese.id,  toast.id])
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list(['cheese',  'toast', u'ŠĐĆŽćžšđ'])
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list([cheese,  toast])
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list((cheese,  toast))
(<Tag: cheese>, <Tag: toast>)
>>> get_tag_list(Tag.objects.filter(name__in=['cheese', 'toast']))
[<Tag: cheese>, <Tag: toast>]
>>> get_tag_list(['cheese', toast])
Traceback (most recent call last):
    ...
ValueError: If a list or tuple of tags is provided, they must all be tag names, Tag objects or Tag ids
>>> get_tag_list(29)
Traceback (most recent call last):
    ...
ValueError: The tag input given was invalid

# Tag clouds ##################################################################
>>> tags = []
>>> for line in open(os.path.join(os.path.dirname(__file__), 'tags.txt')).readlines():
...     name, count = line.rstrip().split()
...     tag = Tag(name=name)
...     tag.count = int(count)
...     tags.append(tag)

>>> sizes = {}
>>> for tag in calculate_cloud(tags, steps=5):
...     sizes[tag.font_size] = sizes.get(tag.font_size, 0) + 1

# This isn't a pre-calculated test, just making sure it's consistent
>>> sizes
{1: 48, 2: 20, 3: 24, 4: 19, 5: 11}

>>> sizes = {}
>>> for tag in calculate_cloud(tags, steps=5, distribution=LINEAR):
...     sizes[tag.font_size] = sizes.get(tag.font_size, 0) + 1

# This isn't a pre-calculated test, just making sure it's consistent
>>> sizes
{1: 97, 2: 12, 3: 7, 4: 2, 5: 4}

>>> calculate_cloud(tags, steps=5, distribution='cheese')
Traceback (most recent call last):
    ...
ValueError: Invalid font size distribution algorithm specified: cheese

##############
# Validators #
##############

>>> isTagList('foo', {})
>>> isTagList('foo bar baz', {})
>>> isTagList('foo,bar,baz', {})
>>> isTagList('foo, bar, baz', {})
>>> isTagList('foo, ŠĐĆŽćžšđ, baz', {})
>>> isTagList('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb bar', {})
>>> isTagList('', {})
Traceback (most recent call last):
    ...
ValidationError: ['Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> isTagList(' foo', {})
Traceback (most recent call last):
    ...
ValidationError: ['Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> isTagList('foo ', {})
Traceback (most recent call last):
    ...
ValidationError: ['Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> isTagList('foo  bar', {})
Traceback (most recent call last):
    ...
ValidationError: ['Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> isTagList('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbn bar', {})
Traceback (most recent call last):
    ...
ValidationError: ['Tag names must be no longer than 50 characters.']
>>> isTag('f-o_1o', {})
>>> isTag('ŠĐĆŽćžšđ', {})
>>> isTag('f o o', {})
Traceback (most recent call last):
    ...
ValidationError: ['Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens.']

###############
# Form Fields #
###############

>>> t = TagField()
>>> t.clean('foo')
u'foo'
>>> t.clean('foo bar baz')
u'foo bar baz'
>>> t.clean('foo,bar,baz')
u'foo,bar,baz'
>>> t.clean('foo, bar, baz')
u'foo, bar, baz'
>>> t.clean('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb bar')
u'foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb bar'
>>> t.clean(' foo')
Traceback (most recent call last):
    ...
ValidationError: [u'Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> t.clean('foo ')
Traceback (most recent call last):
    ...
ValidationError: [u'Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> t.clean('foo  bar')
Traceback (most recent call last):
    ...
ValidationError: [u'Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.']
>>> t.clean('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbn bar')
Traceback (most recent call last):
    ...
ValidationError: [u'Tag names must be no longer than 50 characters.']

###########
# Tagging #
###########

# Basic tagging ###############################################################

>>> dead = Parrot.objects.create(state='dead')
>>> Tag.objects.update_tags(dead, 'foo bar ter')
>>> Tag.objects.get_for_object(dead)
[<Tag: bar>, <Tag: foo>, <Tag: ter>]
>>> Tag.objects.update_tags(dead, 'foo bar baz')
>>> Tag.objects.get_for_object(dead)
[<Tag: bar>, <Tag: baz>, <Tag: foo>]

# Note that doctest in Python 2.4 (and maybe 2.5?) doesn't support non-ascii
# characters in output, so we're displaying the repr() here.
>>> Tag.objects.update_tags(dead, 'ŠĐĆŽćžšđ')
>>> repr(Tag.objects.get_for_object(dead))
'[<Tag: \xc5\xa0\xc4\x90\xc4\x86\xc5\xbd\xc4\x87\xc5\xbe\xc5\xa1\xc4\x91>]'

>>> Tag.objects.update_tags(dead, None)
>>> Tag.objects.get_for_object(dead)
[]

# Retrieving tags by Model ####################################################

>>> Tag.objects.usage_for_model(Parrot)
[]
>>> parrot_details = (
...     ('pining for the fjords', 9, 'foo bar'),
...     ('passed on', 6, 'bar baz ter'),
...     ('no more', 4, 'foo ter'),
...     ('late', 2, 'bar ter'),
... )

>>> for state, perch_size, tags in parrot_details:
...     perch = Perch.objects.create(size=perch_size)
...     parrot = Parrot.objects.create(state=state, perch=perch)
...     Tag.objects.update_tags(parrot, tags)

>>> [(tag.name, tag.count) for tag in Tag.objects.usage_for_model(Parrot, counts=True)]
[('bar', 3), ('baz', 1), ('foo', 2), ('ter', 3)]

# Limiting results to a subset of the model
>>> [(tag.name, tag.count) for tag in Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(state='no more'))]
[('foo', 1), ('ter', 1)]
>>> [(tag.name, tag.count) for tag in Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(state__startswith='p'))]
[('bar', 2), ('baz', 1), ('foo', 1), ('ter', 1)]
>>> [(tag.name, tag.count) for tag in Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(perch__size__gt=4))]
[('bar', 2), ('baz', 1), ('foo', 1), ('ter', 1)]
>>> [(tag.name, hasattr(tag, 'counts')) for tag in Tag.objects.usage_for_model(Parrot, filters=dict(perch__size__gt=4))]
[('bar', False), ('baz', False), ('foo', False), ('ter', False)]
>>> [(tag.name, hasattr(tag, 'counts')) for tag in Tag.objects.usage_for_model(Parrot, filters=dict(perch__size__gt=99))]
[]

# Related tags
>>> tags = Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar']), Parrot, counts=True)
>>> [(tag.name, tag.count) for tag in tags]
[('baz', 1), ('foo', 1), ('ter', 2)]
>>> tags = Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar']), Parrot, counts=False)
>>> [tag.name for tag in tags]
['baz', 'foo', 'ter']
>>> tags = Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar', 'ter']), Parrot, counts=True)
>>> [(tag.name, tag.count) for tag in tags]
[('baz', 1)]
>>> tags = Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar', 'ter', 'baz']), Parrot, counts=True)
>>> [(tag.name, tag.count) for tag in tags]
[]

# Once again, with feeling (strings)
>>> tags = Tag.objects.related_for_model('bar', Parrot, counts=True)
>>> [(tag.name, tag.count) for tag in tags]
[('baz', 1), ('foo', 1), ('ter', 2)]
>>> tags = Tag.objects.related_for_model('bar', Parrot, counts=False)
>>> [tag.name for tag in tags]
['baz', 'foo', 'ter']
>>> tags = Tag.objects.related_for_model(['bar', 'ter'], Parrot, counts=True)
>>> [(tag.name, tag.count) for tag in tags]
[('baz', 1)]
>>> tags = Tag.objects.related_for_model(['bar', 'ter', 'baz'], Parrot, counts=True)
>>> [(tag.name, tag.count) for tag in tags]
[]

# Retrieving tagged objects by Model ##########################################

>>> foo = Tag.objects.get(name='foo')
>>> bar = Tag.objects.get(name='bar')
>>> baz = Tag.objects.get(name='baz')
>>> ter = Tag.objects.get(name='ter')
>>> TaggedItem.objects.get_by_model(Parrot, foo)
[<Parrot: no more>, <Parrot: pining for the fjords>]
>>> TaggedItem.objects.get_by_model(Parrot, bar)
[<Parrot: late>, <Parrot: passed on>, <Parrot: pining for the fjords>]

# Intersections are supported
>>> TaggedItem.objects.get_by_model(Parrot, [foo, baz])
[]
>>> TaggedItem.objects.get_by_model(Parrot, [foo, bar])
[<Parrot: pining for the fjords>]
>>> TaggedItem.objects.get_by_model(Parrot, [bar, ter])
[<Parrot: late>, <Parrot: passed on>]

# You can also pass Tag QuerySets
>>> TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['foo', 'baz']))
[]
>>> TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['foo', 'bar']))
[<Parrot: pining for the fjords>]
>>> TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['bar', 'ter']))
[<Parrot: late>, <Parrot: passed on>]

# You can also pass strings and lists of strings
>>> TaggedItem.objects.get_by_model(Parrot, 'foo baz')
[]
>>> TaggedItem.objects.get_by_model(Parrot, 'foo bar')
[<Parrot: pining for the fjords>]
>>> TaggedItem.objects.get_by_model(Parrot, 'bar ter')
[<Parrot: late>, <Parrot: passed on>]
>>> TaggedItem.objects.get_by_model(Parrot, ['foo', 'baz'])
[]
>>> TaggedItem.objects.get_by_model(Parrot, ['foo', 'bar'])
[<Parrot: pining for the fjords>]
>>> TaggedItem.objects.get_by_model(Parrot, ['bar', 'ter'])
[<Parrot: late>, <Parrot: passed on>]

# Retrieving related objects by Model #########################################

# Related instances of the same Model
>>> l1 = Link.objects.create(name='link 1')
>>> Tag.objects.update_tags(l1, 'tag1 tag2 tag3 tag4 tag5')
>>> l2 = Link.objects.create(name='link 2')
>>> Tag.objects.update_tags(l2, 'tag1 tag2 tag3')
>>> l3 = Link.objects.create(name='link 3')
>>> Tag.objects.update_tags(l3, 'tag1')
>>> l4 = Link.objects.create(name='link 4')
>>> TaggedItem.objects.get_related(l1, Link)
[<Link: link 2>, <Link: link 3>]
>>> TaggedItem.objects.get_related(l1, Link, num=1)
[<Link: link 2>]
>>> TaggedItem.objects.get_related(l4, Link)
[]

# Related instance of a different Model
>>> a1 = Article.objects.create(name='article 1')
>>> Tag.objects.update_tags(a1, 'tag1 tag2 tag3 tag4')
>>> TaggedItem.objects.get_related(a1, Link)
[<Link: link 1>, <Link: link 2>, <Link: link 3>]
>>> Tag.objects.update_tags(a1, 'tag6')
>>> TaggedItem.objects.get_related(a1, Link)
[]
"""
