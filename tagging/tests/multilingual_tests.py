# -*- coding: utf-8 -*-
from unittest import TestCase

from django.utils.translation import get_language
from multilingual.languages import set_default_language, get_default_language_code
from tagging.models import Tag, TaggedItem
from tagging.tests.models import Article, Link, Perch, Parrot, FormTest
from tagging import settings

if settings.MULTILINGUAL_TAGS:
    class MultilingualTests(TestCase):
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

