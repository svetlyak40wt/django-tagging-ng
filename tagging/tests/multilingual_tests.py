# -*- coding: utf-8 -*-
from unittest import TestCase
from pdb import set_trace

from django.utils.translation import get_language
from tagging.models import Tag, TaggedItem
from tagging.tests.models import Article, Link, Perch, Parrot, FormTest
from tagging import settings

if settings.MULTILINGUAL_TAGS:
    from multilingual.languages import set_default_language, get_default_language_code, get_language_code
    class MultilingualTests(TestCase):
        def setUp(self):
            super(MultilingualTests, self).setUp()
            Tag.objects.all().delete()

        def testDefaultLanguage(self):
            self.assertEqual('en-us', get_language())

        def testSetTagsForDifferentLanguages(self):
            set_default_language('en')
            self.assertEqual('en', get_default_language_code())

            en_name = u'apple'
            ru_name = u'яблоко'

            t = Tag.objects.create(name = en_name, name_ru = ru_name)
            self.assertEqual(en_name, t.name)
            self.assertEqual(ru_name, t.name_ru)

            set_default_language('ru')
            self.assertEqual(ru_name, t.name)
            self.assertEqual(en_name, t.name_en)

        def testDuplicateCreationRaisesError(self):
            from django.db import IntegrityError
            en_name = u'apple'
            ru_name = u'яблоко'
            Tag.objects.create(name = en_name, name_ru = ru_name)
            self.assertRaises(IntegrityError, Tag.objects.create, name = en_name)
            self.assertRaises(IntegrityError, Tag.objects.create, name_ru = ru_name)
            self.assertRaises(IntegrityError, Tag.objects.create, name = en_name, name_ru = ru_name)


        def testGetOrCreate(self):
            tag_name = u'test'

            tag, created = Tag.objects.get_or_create(name = tag_name)
            self.assertEqual(tag.name, tag_name)
            self.assertEqual(True, created)

            tag, created = Tag.objects.get_or_create(name = tag_name)
            self.assertEqual(tag.name, tag_name)
            self.assertEqual(False, created)

        def testFalbackToDefaultLanguage(self):
            set_default_language(settings.DEFAULT_LANGUAGE)

            default_name = u'apple'

            t = Tag.objects.create(name = default_name)
            self.assertEqual(default_name, t.name)
            self.assertEqual(default_name, t.name_en)
            self.assertEqual(None,         t.name_ru)

            set_default_language('ru')
            t = Tag.objects.get(id = t.id)
            self.assertEqual(default_name, t.name)
            self.assertEqual(default_name, t.name_en)
            self.assertEqual(None,         t.name_ru)

