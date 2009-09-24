from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from tagging.models import Tag, TaggedItem, Synonym
from tagging.utils import merge, get_tag
from tagging.tests.synonym_tests import TestItem, TestItemWithCallback

def with_tag(tag, cls = TestItem):
    return TaggedItem.objects.get_by_model(cls, [tag])

def model_to_ctype(model):
    return ContentType._default_manager.get_for_model(model)

class Merge(TestCase):
    def testMergeTagsDeletesSecondTagIfNoMoreTaggedItems(self):
        self.assertEqual(0, Tag.objects.count())
        self.assertEqual(0, TaggedItem.objects.count())
        self.assertEqual(0, Synonym.objects.count())

        first = TestItem(title = 'first', tags = 'one, two')
        first.save()
        second = TestItem(title = 'second', tags = 'second')
        second.save()

        self.assertEqual(1, len(with_tag('one')))
        self.assertEqual(1, len(with_tag('two')))
        self.assertEqual(1, len(with_tag('second')))

        ctype = model_to_ctype(TestItem)
        merge('two', 'second', ctype)

        self.assertEqual(1, len(with_tag('one')))
        self.assertEqual(2, len(with_tag('two')))
        self.assertRaises(Tag.DoesNotExist, Tag.objects.get, name = 'second')

    def testMergeTagsNotDeletesSecondTag(self):
        self.assertEqual(0, Tag.objects.count())
        self.assertEqual(0, TaggedItem.objects.count())
        self.assertEqual(0, Synonym.objects.count())

        first = TestItem(title = 'first', tags = 'one, two')
        first.save()
        second = TestItem(title = 'second', tags = 'second')
        second.save()
        third = TestItemWithCallback(title = 'third', tags = 'second')
        third.save()

        self.assertEqual(1, len(with_tag('second')))
        self.assertEqual(1, len(with_tag('second', TestItemWithCallback)))

        ctype = model_to_ctype(TestItem)
        merge('two', 'second', ctype)

        self.assertEqual(0, len(with_tag('second')))
        self.assertEqual(1, len(with_tag('second', TestItemWithCallback)))
        self.assert_(Tag.objects.get(name = 'second'))

    def testMergeTagsCreatesSynonyms(self):
        first = TestItem(title = 'first', tags = 'one, two')
        first.save()
        second = TestItem(title = 'second', tags = 'second')
        second.save()

        self.assertEqual([], [s.name for s in get_tag('two').synonyms.all()])

        ctype = model_to_ctype(TestItem)
        merge('two', 'second', ctype)

        self.assertEqual(['second'], [s.name for s in get_tag('two').synonyms.all()])

    def testMergeTagsWhenSynonymAlreadyExists(self):
        first = TestItem(title = 'first', tags = 'one, two, blah')
        first.save()
        second = TestItem(title = 'second', tags = 'second')
        second.save()
        blah = get_tag('blah')
        blah.synonyms.create(name='second')

        self.assertEqual([], [s.name for s in get_tag('two').synonyms.all()])

        ctype = model_to_ctype(TestItem)
        merge('two', 'second', ctype)

        self.assertEqual([], [s.name for s in get_tag('two').synonyms.all()])
        self.assertEqual(['second'], [s.name for s in get_tag('blah').synonyms.all()])

