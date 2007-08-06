import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tagging.tests.settings'

from django.test.simple import run_tests
from django.conf import settings

failures = run_tests(None, verbosity=9)
if failures:
    sys.exit(failures)
