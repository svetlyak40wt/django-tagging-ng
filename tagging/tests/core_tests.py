# -*- coding: utf-8 -*-
import os
from pdb import set_trace
from unittest import TestCase
from django import forms
from django.db.models import Q
from tagging.forms import TagField
from tagging import settings
from tagging.models import Tag, TaggedItem
from tagging.tests.models import Article, Link, Perch, Parrot, FormTest
from tagging.utils import calculate_cloud, get_tag_list, get_tag, parse_tag_input
from tagging.utils import LINEAR

class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        Tag.objects.all().delete()

    def assertListsEqual(self, left, right):
        self.assertEqual(list(left), list(right))

class UtitlitiesTests(BaseTestCase):
    def testSimpleSpaceDelimitedTags(self):
        self.assertEqual([u'one'], parse_tag_input('one'))
        self.assertEqual([u'one', u'two'], parse_tag_input('one two'))
        self.assertEqual([u'one', u'three', u'two'], parse_tag_input('one two three'))
        self.assertEqual([u'one', u'two'], parse_tag_input('one one two two'))

    def testCommaDelimitedMultipleWords(self):
        """An unquoted comma in the input will trigger"""
        self.assertEqual([u'one'], parse_tag_input(',one'))
        self.assertEqual([u'one two'], parse_tag_input(',one two'))
        self.assertEqual([u'one two three'], parse_tag_input(',one two three'))
        self.assertEqual([u'a-one', u'a-two and a-three'], parse_tag_input('a-one, a-two and a-three'))

    def testDoubleQuotedMultipleWords(self):
        """A completed quote will trigger this. Unclosed quotes are ignored."""
        self.assertEqual([u'one'], parse_tag_input('"one'))
        self.assertEqual([u'one', u'two'], parse_tag_input('"one two'))
        self.assertEqual([u'one', u'three', u'two'], parse_tag_input('"one two three'))
        self.assertEqual([u'one two'], parse_tag_input('"one two"'))
        self.assertEqual([u'a-one', u'a-two and a-three'], parse_tag_input('a-one "a-two and a-three"'))

    def testNoLooseCommasSplitOnSpaces(self):
        self.assertEqual([u'one', u'thr,ee', u'two'], parse_tag_input('one two "thr,ee"'))

    def testLooseCommasSplitOnCommas(self):
        self.assertEqual([u'one', u'two three'], parse_tag_input('"one", two three'))

    def testDoubleQuotesCanContainCommas(self):
        self.assertEqual([u'a-one', u'a-two, and a-three'], parse_tag_input('a-one "a-two, and a-three"'))
        self.assertEqual([u'one', u'two'], parse_tag_input('"two", one, one, two, "one"'))

    def testBadUsersNaughtyUsers(self):
        self.assertEqual([], parse_tag_input(None))
        self.assertEqual([], parse_tag_input(''))
        self.assertEqual([], parse_tag_input('"'))
        self.assertEqual([], parse_tag_input('""'))
        self.assertEqual([], parse_tag_input('"' * 7))
        self.assertEqual([], parse_tag_input(',,,,,,'))
        self.assertEqual([u','], parse_tag_input('",",",",",",","'))
        self.assertEqual([u'a-one', u'a-three', u'a-two', u'and'], parse_tag_input('a-one "a-two" and "a-three'))

    def testNormalisedTagListInput(self):
        cheese = Tag.objects.create(name='cheese')
        toast = Tag.objects.create(name='toast')
        self.assertListsEqual([cheese], get_tag_list(cheese))
        self.assertListsEqual([cheese, toast], get_tag_list('cheese toast'))
        self.assertListsEqual([cheese, toast], get_tag_list('cheese,toast'))
        self.assertListsEqual([], get_tag_list([]))
        self.assertListsEqual([cheese, toast], get_tag_list(['cheese', 'toast']))
        self.assertListsEqual([cheese, toast], get_tag_list([cheese.id, toast.id]))
        self.assertListsEqual([cheese, toast], get_tag_list(['cheese', 'toast', 'ŠĐĆŽćžšđ']))
        self.assertListsEqual([cheese, toast], get_tag_list([cheese, toast]))
        self.assertEqual((cheese, toast), get_tag_list((cheese, toast)))
        self.assertListsEqual([cheese, toast], get_tag_list(Tag.objects.filter(name__in=['cheese', 'toast'])))
        self.assertRaises(ValueError, get_tag_list, ['cheese', toast])
        self.assertRaises(ValueError, get_tag_list, 29)

    def testNormalisedTagInput(self):
        cheese = Tag.objects.create(name='cheese')
        self.assertEqual(cheese, get_tag(cheese))
        self.assertEqual(cheese, get_tag('cheese'))
        self.assertEqual(cheese, get_tag(cheese.id))
        self.assertEqual(None, get_tag('mouse'))

    def testTagClouds(self):
        tags = []
        for line in open(os.path.join(os.path.dirname(__file__), 'tags.txt')).readlines():
            name, count = line.rstrip().split()
            tag = Tag(name=name)
            tag.count = int(count)
            tags.append(tag)

        sizes = {}
        for tag in calculate_cloud(tags, steps=5):
            sizes[tag.font_size] = sizes.get(tag.font_size, 0) + 1

        # This isn't a pre-calculated test, just making sure it's consistent
        self.assertEqual({1: 48, 2: 30, 3: 19, 4: 15, 5: 10}, sizes)

        sizes = {}
        for tag in calculate_cloud(tags, steps=5, distribution=LINEAR):
            sizes[tag.font_size] = sizes.get(tag.font_size, 0) + 1

        # This isn't a pre-calculated test, just making sure it's consistent
        self.assertEqual({1: 97, 2: 12, 3: 7, 4: 2, 5: 4}, sizes)

        self.assertRaises(ValueError, calculate_cloud, tags, steps=5, distribution='cheese')

def get_tagcounts(query):
    return [(tag.name, getattr(tag, 'count', False)) for tag in query]

def get_tagnames(query):
    return [tag.name for tag in query]

class TaggingTests(BaseTestCase):
    def testBasicTagging(self):
        dead = Parrot.objects.create(state='dead')
        Tag.objects.update_tags(dead, 'foo,bar,"ter"')

        self.assertListsEqual(get_tag_list('bar foo ter'), Tag.objects.get_for_object(dead))

        Tag.objects.update_tags(dead, '"foo" bar "baz"')
        self.assertListsEqual(get_tag_list('bar baz foo'), Tag.objects.get_for_object(dead))

        Tag.objects.add_tag(dead, 'foo')
        self.assertListsEqual(get_tag_list('bar baz foo'), Tag.objects.get_for_object(dead))

        Tag.objects.add_tag(dead, 'zip')
        self.assertListsEqual(get_tag_list('bar baz foo zip'), Tag.objects.get_for_object(dead))

        self.assertRaises(AttributeError, Tag.objects.add_tag, dead, '    ')
        self.assertRaises(AttributeError, Tag.objects.add_tag, dead, 'one two')

        Tag.objects.update_tags(dead, 'ŠĐĆŽćžšđ')
        self.assertEqual(
            '[<Tag: \xc5\xa0\xc4\x90\xc4\x86\xc5\xbd\xc4\x87\xc5\xbe\xc5\xa1\xc4\x91>]',
            repr(Tag.objects.get_for_object(dead)))

        Tag.objects.update_tags(dead, None)
        self.assertListsEqual([], Tag.objects.get_for_object(dead))

    def testUsingAModelsTagField(self):
        f1 = FormTest.objects.create(tags=u'test3 test2 test1')
        self.assertListsEqual(get_tag_list('test1 test2 test3'), Tag.objects.get_for_object(f1))
        f1.tags = u'test4'
        f1.save()
        self.assertListsEqual(get_tag_list('test4'), Tag.objects.get_for_object(f1))
        f1.tags = ''
        f1.save()
        self.assertListsEqual([], Tag.objects.get_for_object(f1))

    def testForcingTagsToLowercase(self):
        settings.FORCE_LOWERCASE_TAGS = True

        dead = Parrot.objects.create(state='dead')
        Tag.objects.update_tags(dead, 'foO bAr Ter')
        self.assertListsEqual(get_tag_list('bar foo ter'), Tag.objects.get_for_object(dead))

        Tag.objects.update_tags(dead, 'foO bAr baZ')
        self.assertListsEqual(get_tag_list('bar baz foo'), Tag.objects.get_for_object(dead))

        Tag.objects.add_tag(dead, 'FOO')
        self.assertListsEqual(get_tag_list('bar baz foo'), Tag.objects.get_for_object(dead))

        Tag.objects.add_tag(dead, 'Zip')
        self.assertListsEqual(get_tag_list('bar baz foo zip'), Tag.objects.get_for_object(dead))

        Tag.objects.update_tags(dead, None)
        f1 = FormTest.objects.create(tags=u'test3 test2 test1')
        f1.tags = u'TEST5'
        f1.save()
        self.assertListsEqual(get_tag_list('test5'), Tag.objects.get_for_object(f1))
        self.assertEqual(u'test5', f1.tags)

class RetrivingTests(BaseTestCase):
    def setUp(self):
        super(RetrivingTests, self).setUp()

        self.assertEqual([], Tag.objects.usage_for_model(Parrot))
        parrot_details = (
            ('pining for the fjords', 9, True,  'foo bar'),
            ('passed on',             6, False, 'bar baz ter'),
            ('no more',               4, True,  'foo ter'),
            ('late',                  2, False, 'bar ter'),
        )

        for state, perch_size, perch_smelly, tags in parrot_details:
            perch = Perch.objects.create(size=perch_size, smelly=perch_smelly)
            parrot = Parrot.objects.create(state=state, perch=perch)
            Tag.objects.update_tags(parrot, tags)

        self.foo = Tag.objects.get(name='foo')
        self.bar = Tag.objects.get(name='bar')
        self.baz = Tag.objects.get(name='baz')
        self.ter = Tag.objects.get(name='ter')


    def testRetrievingTagsByModel(self):
        self.assertEqual(
            [(u'bar', 3), (u'baz', 1), (u'foo', 2), (u'ter', 3)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, counts=True)))
        self.assertEqual(
            [(u'bar', 3), (u'foo', 2), (u'ter', 3)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, min_count=2)))

    def testLimitingResultsToASubsetOfTheModel(self):
        self.assertEqual([(u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(state='no more'))))
        self.assertEqual([(u'bar', 2), (u'baz', 1), (u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(state__startswith='p'))))
        self.assertEqual([(u'bar', 2), (u'baz', 1), (u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(perch__size__gt=4))))
        self.assertEqual([(u'bar', 1), (u'foo', 2), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, counts=True, filters=dict(perch__smelly=True))))
        self.assertEqual([(u'foo', 2)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, min_count=2, filters=dict(perch__smelly=True))))
        self.assertEqual([(u'bar', False), (u'baz', False), (u'foo', False), (u'ter', False)],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, filters=dict(perch__size__gt=4))))
        self.assertEqual([],
            get_tagcounts(Tag.objects.usage_for_model(Parrot, filters=dict(perch__size__gt=99))))

    def testRelatedTags(self):
        self.assertEqual([(u'baz', 1), (u'foo', 1), (u'ter', 2)],
            get_tagcounts(Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar']), Parrot, counts=True)))
        self.assertEqual([(u'ter', 2)],
            get_tagcounts(Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar']), Parrot, min_count=2)))
        self.assertEqual([u'baz', u'foo', u'ter'],
            get_tagnames(Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar']), Parrot, counts=False)))
        self.assertEqual([(u'baz', 1)],
            get_tagcounts(Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar', 'ter']), Parrot, counts=True)))
        self.assertEqual([],
            get_tagcounts(Tag.objects.related_for_model(Tag.objects.filter(name__in=['bar', 'ter', 'baz']), Parrot, counts=True)))

    def testRelatesTagsWithStrings(self):
        self.assertEqual([(u'baz', 1), (u'foo', 1), (u'ter', 2)],
            get_tagcounts(Tag.objects.related_for_model('bar', Parrot, counts=True)))
        self.assertEqual([(u'ter', 2)],
            get_tagcounts(Tag.objects.related_for_model('bar', Parrot, min_count=2)))
        self.assertEqual([u'baz', u'foo', u'ter'],
            get_tagnames(Tag.objects.related_for_model('bar', Parrot, counts=False)))
        self.assertEqual([(u'baz', 1)],
            get_tagcounts(Tag.objects.related_for_model(['bar', 'ter'], Parrot, counts=True)))
        self.assertEqual([],
            get_tagcounts(Tag.objects.related_for_model(['bar', 'ter', 'baz'], Parrot, counts=True)))

    def testRetrievingTaggedObjectsByModel(self):
        self.assertEqual(
            '[<Parrot: no more>, <Parrot: pining for the fjords>]',
            repr(TaggedItem.objects.get_by_model(Parrot, self.foo)))
        self.assertEqual(
            '[<Parrot: late>, <Parrot: passed on>, <Parrot: pining for the fjords>]',
            repr(TaggedItem.objects.get_by_model(Parrot, self.bar)))


    def testIntersectionsAreSupported(self):
        self.assertListsEqual([], TaggedItem.objects.get_by_model(Parrot, [self.foo, self.baz]))
        self.assertEqual('[<Parrot: pining for the fjords>]', repr(TaggedItem.objects.get_by_model(Parrot, [self.foo, self.bar])))
        self.assertEqual('[<Parrot: late>, <Parrot: passed on>]', repr(TaggedItem.objects.get_by_model(Parrot, [self.bar, self.ter])))

    def testIssue114IntersectionWithNonExistantTags(self):
        self.assertListsEqual([], TaggedItem.objects.get_intersection_by_model(Parrot, []))

    def testYouCanAlsoPassTagQuerySets(self):
        self.assertListsEqual([], TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['foo', 'baz'])))
        self.assertEqual('[<Parrot: pining for the fjords>]',
            repr(TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['foo', 'bar']))))
        self.assertEqual('[<Parrot: late>, <Parrot: passed on>]',
            repr(TaggedItem.objects.get_by_model(Parrot, Tag.objects.filter(name__in=['bar', 'ter']))))

    def testYouCanAlsoPassStringsAndListsOfStrings(self):
        self.assertListsEqual([], TaggedItem.objects.get_by_model(Parrot, 'foo baz'))
        self.assertEqual('[<Parrot: pining for the fjords>]', repr(TaggedItem.objects.get_by_model(Parrot, 'foo bar')))
        self.assertEqual('[<Parrot: late>, <Parrot: passed on>]', repr(TaggedItem.objects.get_by_model(Parrot, 'bar ter')))
        self.assertListsEqual([], TaggedItem.objects.get_by_model(Parrot, ['foo', 'baz']))
        self.assertEqual('[<Parrot: pining for the fjords>]', repr(TaggedItem.objects.get_by_model(Parrot, ['foo', 'bar'])))
        self.assertEqual('[<Parrot: late>, <Parrot: passed on>]', repr(TaggedItem.objects.get_by_model(Parrot, ['bar', 'ter'])))

    def testIssue50GetByNonExistentTag(self):
        self.assertListsEqual([], TaggedItem.objects.get_by_model(Parrot, 'argatrons'))

    def testUnions(self):
        self.assertEqual('[<Parrot: late>, <Parrot: no more>, <Parrot: passed on>, <Parrot: pining for the fjords>]',
            repr(TaggedItem.objects.get_union_by_model(Parrot, ['foo', 'ter'])))
        self.assertEqual('[<Parrot: late>, <Parrot: passed on>, <Parrot: pining for the fjords>]',
            repr(TaggedItem.objects.get_union_by_model(Parrot, ['bar', 'baz'])))

    def testIssue114UnionWithNonExistantTags(self):
        self.assertListsEqual([], TaggedItem.objects.get_union_by_model(Parrot, []))

    def testLimitingResultsToAQueryset(self):
        self.assertEqual([(u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(state='no more'), counts=True)))
        self.assertEqual([(u'bar', 2), (u'baz', 1), (u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(state__startswith='p'), counts=True)))
        self.assertEqual([(u'bar', 2), (u'baz', 1), (u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(perch__size__gt=4), counts=True)))
        self.assertEqual([(u'bar', 1), (u'foo', 2), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(perch__smelly=True), counts=True)))
        self.assertEqual([(u'foo', 2)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(perch__smelly=True), min_count=2)))
        self.assertEqual([(u'bar', False), (u'baz', False), (u'foo', False), (u'ter', False)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(perch__size__gt=4))))
        self.assertEqual([],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(perch__size__gt=99))))
        self.assertEqual([(u'bar', 2), (u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(Q(perch__size__gt=6) | Q(state__startswith='l')), counts=True)))
        self.assertEqual([(u'bar', 2)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(Q(perch__size__gt=6) | Q(state__startswith='l')), min_count=2)))
        self.assertEqual([(u'bar', False), (u'foo', False), (u'ter', False)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.filter(Q(perch__size__gt=6) | Q(state__startswith='l')))))
        self.assertEqual([(u'bar', 2), (u'foo', 2), (u'ter', 2)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.exclude(state='passed on'), counts=True)))
        self.assertEqual([(u'ter', 2)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.exclude(state__startswith='p'), min_count=2)))
        self.assertEqual([(u'foo', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.exclude(Q(perch__size__gt=6) | Q(perch__smelly=False)), counts=True)))
        self.assertEqual([(u'bar', 1), (u'ter', 1)],
            get_tagcounts(Tag.objects.usage_for_queryset(Parrot.objects.exclude(perch__smelly=True).filter(state__startswith='l'), counts=True)))


class RelatedTests(BaseTestCase):
    def setUp(self):
        super(RelatedTests, self).setUp()

        self.l1 = Link.objects.create(name='link 1')
        Tag.objects.update_tags(self.l1, 'tag1 tag2 tag3 tag4 tag5')
        self.l2 = Link.objects.create(name='link 2')
        Tag.objects.update_tags(self.l2, 'tag1 tag2 tag3')
        self.l3 = Link.objects.create(name='link 3')
        Tag.objects.update_tags(self.l3, 'tag1')
        self.l4 = Link.objects.create(name='link 4')

    def testRelatedInstancesOfTheSameModel(self):
        self.assertEqual('[<Link: link 2>, <Link: link 3>]', repr(TaggedItem.objects.get_related(self.l1, Link)))
        self.assertEqual('[<Link: link 2>]', repr(TaggedItem.objects.get_related(self.l1, Link, num=1)))
        self.assertListsEqual([], TaggedItem.objects.get_related(self.l4, Link))

    def testLimitRelatedItems(self):
        self.assertEqual([self.l2], TaggedItem.objects.get_related(self.l1, Link.objects.exclude(name='link 3')))

    def testRelatedInstanceOfADifferentModel(self):
        a1 = Article.objects.create(name='article 1')
        Tag.objects.update_tags(a1, 'tag1 tag2 tag3 tag4')
        self.assertListsEqual([self.l1, self.l2, self.l3], TaggedItem.objects.get_related(a1, Link))
        Tag.objects.update_tags(a1, 'tag6')
        self.assertListsEqual([], TaggedItem.objects.get_related(a1, Link))

class TagFieldTests(BaseTestCase):
    def testEnsureThatAutomaticallyCreatedFormsUseTagField(self):
        class TestForm(forms.ModelForm):
            class Meta:
                model = FormTest
        form = TestForm()
        self.assertEqual('TagField', form.fields['tags'].__class__.__name__)

    def testRecreatingStringRepresentaionsOfTagLists(self):
        plain = Tag.objects.create(name='plain')
        spaces = Tag.objects.create(name='spa ces')
        comma = Tag.objects.create(name='com,ma')

        from tagging.utils import edit_string_for_tags
        self.assertEqual(u'plain', edit_string_for_tags([plain]))
        self.assertEqual(u'plain, spa ces', edit_string_for_tags([plain, spaces]))
        self.assertEqual(u'plain, spa ces, "com,ma"', edit_string_for_tags([plain, spaces, comma]))
        self.assertEqual(u'plain "com,ma"', edit_string_for_tags([plain, comma]))
        self.assertEqual(u'"com,ma", spa ces', edit_string_for_tags([comma, spaces]))

    def testFormFields(self):
        from django.forms import ValidationError
        t = TagField()

        self.assertEqual(u'foo', t.clean('foo'))
        self.assertEqual(u'foo bar baz', t.clean('foo bar baz'))
        self.assertEqual(u'foo,bar,baz', t.clean('foo,bar,baz'))
        self.assertEqual(u'foo, bar, baz', t.clean('foo, bar, baz'))
        self.assertEqual(u'foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb bar',
                         t.clean('foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb bar'))
        self.assertRaises(ValidationError, t.clean, 'foo qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbn bar')
