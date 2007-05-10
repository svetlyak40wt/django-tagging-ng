import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tagging.tests.settings'

from django.test.simple import run_tests
from django.conf import settings
from django.db.models.loading import load_app

test_models = [load_app(app) for app in settings.INSTALLED_APPS]
failures = run_tests(test_models)
if failures:
    sys.exit(failures)