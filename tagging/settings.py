"""
Convenience module for access of custom tagging application settings,
which enforces default settings when the main settings module which has
been configured does not contain the appropriate settings.
"""
from django.conf import settings

# Whether to force all tags to lowercase before they are saved to the
# database. Default is False.
try:
    FORCE_LOWERCASE_TAGS = settings.FORCE_LOWERCASE_TAGS
except AttributeError:
    FORCE_LOWERCASE_TAGS = False
