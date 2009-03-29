# -*- coding: utf-8 -*-
import unittest
from pdb import set_trace
from StringIO import StringIO

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode

from tagging.fields import TagField
from tagging.models import Tag, TaggedItem, Synonym
from tagging.utils import replace_synonyms
from multilingual.languages import set_default_language

class TestItem( models.Model ):
    title = models.CharField( _('Title'), max_length = 30)
    tags = TagField()

    def __unicode__(self):
        return self.title


def create_synonyms(tag_name):
    from django.template.defaultfilters import slugify
    return [slugify(tag_name)]

class TestItemWithCallback( models.Model ):
    title = models.CharField( _('Title'), max_length = 30)
    tags = TagField(create_synonyms = create_synonyms)

    def __unicode__(self):
        return self.title

class TaggingTestCase(unittest.TestCase):
    def setUp(self):
        TestItem.objects.all().delete()
        Tag.objects.all().delete()
        TaggedItem.objects.all().delete()
        Synonym.objects.all().delete()

        self.first = TestItem(title = 'first')
        self.second = TestItem(title = 'second')
        self.third = TestItem(title = 'third')
        self.four = TestItem(title = 'four')

    def saveAll(self):
        self.first.save()
        self.second.save()
        self.third.save()
        self.four.save()

    def testJoining(self):
        self.first.tags = 'hello, world'
        self.second.tags = 'aloha'
        self.third.tags = 'bla'
        self.saveAll()

        # renaming
        aloha = Tag.objects.get(name = 'aloha')
        hello = Tag.objects.get(name = 'hello')
        Tag.objects.join([aloha, hello])

        all_tags = Tag.objects.all()
        self.assertEquals(3, len(all_tags))

        self.assertEquals(0, len(Tag.objects.filter(name = 'hello')))
        self.assertEquals(1, len(Tag.objects.filter(name = 'world')))
        self.assertEquals(1, len(Tag.objects.filter(name = 'bla')))

        tags = Tag.objects.filter(name = 'aloha')
        self.assertEquals(1, len(tags))
        objs = TaggedItem.objects.get_by_model(TestItem, tags)

        self.assertEquals(2, len(objs))
        self.assertTrue(self.first in objs)
        self.assertTrue(self.second in objs)

    def testJoiningMultiple(self):
        self.first.tags = 'hello, world'
        self.second.tags = 'aloha'
        self.third.tags = 'bla'
        self.saveAll()

        # renaming
        aloha = Tag.objects.get(name = 'aloha')
        hello = Tag.objects.get(name = 'hello')
        bla   = Tag.objects.get(name = 'bla')
        Tag.objects.join([aloha, hello, bla])

        all_tags = Tag.objects.all()
        self.assertEquals(2, len(all_tags))

        self.assertEquals(0, len(Tag.objects.filter(name = 'hello')))
        self.assertEquals(0, len(Tag.objects.filter(name = 'bla')))
        self.assertEquals(1, len(Tag.objects.filter(name = 'world')))
        self.assertEquals(1, len(Tag.objects.filter(name = 'aloha')))

        tags = Tag.objects.filter(name = 'aloha')
        self.assertEquals(1, len(tags))
        objs = TaggedItem.objects.get_by_model(TestItem, tags)

        self.assertEquals(3, len(objs))
        self.assertTrue(self.first in objs)
        self.assertTrue(self.second in objs)
        self.assertTrue(self.third in objs)

    def testJoiningTagsFromOneObject(self):
        self.first.tags = 'fruit, apple'
        self.saveAll()

        # renaming
        Tag.objects.join(\
                Tag.objects.filter(name__in = ('fruit', 'apple')))

        all_tags = Tag.objects.all()
        self.assertEquals(1, len(all_tags))

        self.assertEquals(1, len(Tag.objects.filter(name = 'apple')))
        self.assertEquals(0, len(Tag.objects.filter(name = 'fruit')))

    def testJoinUsingTextFormat(self):
        self.first.tags = 'hello, world'
        self.second.tags = 'aloha'
        self.third.tags = 'bla'
        self.saveAll()

        # renaming
        Tag.objects.process_rules(' first-non-existent = hello = aloha = second-non-existent = bla = non-existed')

        all_tags = Tag.objects.all()
        self.assertEquals(2, len(all_tags))

        self.assertEquals(1, len(Tag.objects.filter(name = 'hello')))
        self.assertEquals(1, len(Tag.objects.filter(name = 'world')))

        tags = Tag.objects.filter(name = 'hello')
        self.assertEquals(1, len(tags))
        objs = TaggedItem.objects.get_by_model(TestItem, tags)

        self.assertEquals(3, len(objs))
        self.assertTrue(self.first in objs)
        self.assertTrue(self.second in objs)
        self.assertTrue(self.third in objs)

    def testRenameUsingTextFormat(self):
        self.first.tags = 'hello-world'
        self.saveAll()

        Tag.objects.process_rules( \
                u'''hello-world: hello; ru: Привет;
                    hello; en: Hello;
                    non-existent: normal''')

        tag = Tag.objects.get(name='Hello')
        self.assertEquals(u'Привет', tag.name_ru)
        self.assertEquals(u'Hello', tag.name_en)

    def testDumpTagsAsText(self):
        set_default_language('en')

        hello = Tag.objects.create(name='hello')
        syn = Synonym.objects.create(name='aloha', tag=hello)

        self.first.tags = 'hello, world'
        self.second.tags = 'aloha'
        self.saveAll()

        self.assertEquals( \
u'''hello == aloha
hello; en: hello
world; en: world''', Tag.objects.dumpAsText())

        hello.name_ru = u'Привет'
        hello.name_en = u'Hello'
        hello.save()

        self.assertEquals( \
u'''Hello == aloha
Hello; en: Hello; ru: Привет
world; en: world''', Tag.objects.dumpAsText())

    def testTagRenameChangesObjectsProperties(self):
        self.first.tags = 'hello, world'
        self.saveAll()

        hello = Tag.objects.get(name='hello')
        hello.name = u'Привет'
        hello.save()

        self.first = TestItem.objects.get(id=self.first.id)
        self.assertEquals(u'world Привет', self.first.tags)

    def testTagJoinChangesObjectsProperties(self):
        self.first.tags = 'hello, world'
        self.saveAll()

        Tag.objects.join( \
                Tag.objects.filter(name__in = ('hello', 'world')))

        self.first = TestItem.objects.get(id=self.first.id)
        self.assertEquals('hello', self.first.tags)

    def testTagRemoveChangesObjectsProperties(self):
        self.first.tags = 'hello, world'
        self.saveAll()

        Tag.objects.get(name = 'world').delete()

        self.first = TestItem.objects.get(id=self.first.id)
        self.assertEquals('hello', self.first.tags)

    def testTagSynonym(self):
        tag = Tag.objects.create(name='hello')
        syn = Synonym.objects.create(name='aloha', tag=tag)

        self.first.tags = 'aloha, world'
        self.saveAll()

        self.first = TestItem.objects.get(id=self.first.id)
        self.assertEquals('hello world', self.first.tags)

    def testCreatingSynonymUsingTextFormat(self):
        self.first.tags = 'hello, world'
        self.second.tags = 'aloha'
        self.saveAll()

        # renaming
        self.assertEquals(3, Tag.objects.count())
        Tag.objects.process_rules('hello == aloha == privet')
        self.assertEquals(2, Tag.objects.count())

        self.assertEquals(1, len(Tag.objects.filter(name = 'hello')))
        self.assertEquals(1, len(Tag.objects.filter(name = 'world')))

        hello = Tag.objects.get(name = 'hello')
        self.assertEquals(2, len(hello.synonyms.all()))
        self.assertTrue('aloha', hello.synonyms.all()[0].name)
        self.assertTrue('privet', hello.synonyms.all()[1].name)

        objs = TaggedItem.objects.get_by_model(TestItem, [hello,])

        self.assertEquals(2, len(objs))
        self.assertTrue(self.first in objs)
        self.assertTrue(self.second in objs)

    def testExistingSynonymsAreIgnored(self):
        self.first.tags = 'hello, world'
        self.saveAll()
        Tag.objects.process_rules('hello == aloha == privet')
        self.assert_(Tag.objects.process_rules('hello == aloha == privet'))

    def testReplaceSynonyms(self):
        tag = Tag.objects.create(name='hello')
        Synonym.objects.create(name='aloha', tag=tag)
        self.assertEquals(['hello', 'world'], replace_synonyms(['aloha', 'world']))

    def testCreateSynonymUsingFieldCallback(self):
        tag = Tag.objects.create(name='hello')
        Synonym.objects.create(name='aloha', tag=tag)
        self.assertEquals(['hello', 'world'], replace_synonyms(['aloha', 'world']))

        Synonym.objects.all().delete()
        self.assertEqual(0, len(Synonym.objects.all()))
        test_item = TestItemWithCallback(title='Test callbacks', tags='Test, Create Callbacks')
        test_item.save()
        second_item = TestItemWithCallback(title='Another test', tags='Test')
        second_item.save()

        synonyms = Synonym.objects.all()
        self.assertEqual(2, len(synonyms))
        self.assertEqual('create-callbacks', synonyms[0].name)
        self.assertEqual('test', synonyms[1].name)

        objs = TaggedItem.objects.get_by_model(TestItemWithCallback, ['create-callbacks'])
        self.assertEqual(1, len(objs))
        self.assertEqual('Test callbacks', objs[0].title)

