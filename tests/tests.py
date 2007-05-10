r"""
>>> from tagging.models import Tag, TaggedItem
>>> from tagging.tests.models import Parrot

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
>>> Tag.objects.update_tags(dead, None)
>>> Tag.objects.get_for_object(dead)
[]

# Retrieving tags by Model ####################################################

>>> Tag.objects.usage_for_model(Parrot)
[]
>>> Tag.objects.update_tags(Parrot.objects.create(state='pining for the fjords'), 'foo bar')
>>> Tag.objects.update_tags(Parrot.objects.create(state='passed on'), 'bar baz ter')
>>> Tag.objects.update_tags(Parrot.objects.create(state='no more'), 'foo ter')
>>> Tag.objects.update_tags(Parrot.objects.create(state='late'), 'bar ter')
>>> [(tag.name, tag.count) for tag in Tag.objects.usage_for_model(Parrot, counts=True)]
[('bar', 3), ('baz', 1), ('foo', 2), ('ter', 3)]

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

# You can also pass a Tag QuerySet
>>> TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['foo', 'baz']))
[]
>>> TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['foo', 'bar']))
[<Parrot: pining for the fjords>]
>>> TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['bar', 'ter']))
[<Parrot: late>, <Parrot: passed on>]
"""