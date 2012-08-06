"""
Convenience module for access of custom tagging application settings,
which enforces default settings when the main settings module does not
contain the appropriate settings.
"""
from django.conf import settings

# Whether to force all tags to lowercase before they are saved to the
# database.
FORCE_LOWERCASE_TAGS = getattr(settings, 'FORCE_LOWERCASE_TAGS', False)

# Force a delimiter string for tags.
FORCE_TAG_DELIMITER = getattr(settings, 'FORCE_TAG_DELIMITER', None)

# The maximum length of a tag's name.
MAX_TAG_LENGTH = getattr(settings, 'MAX_TAG_LENGTH', 50)

# Whether to use multilingual tags
MULTILINGUAL_TAGS = getattr(settings, 'MULTILINGUAL_TAGS', False)
if MULTILINGUAL_TAGS:
    DEFAULT_LANGUAGE = getattr(settings, 'DEFAULT_LANGUAGE')
    FALLBACK_LANGUAGE = getattr(settings, 'FALLBACK_LANGUAGE', DEFAULT_LANGUAGE)

