from django.contrib import admin
from tagging.models import Tag, TaggedItem, Synonym
from django.utils.translation import ugettext as _
from tagging import settings

admin.site.register(TaggedItem)

if settings.MULTILINGUAL_TAGS:
    def _name(tag):
        return tag.name_any
    _name.short_description = _('name')

    def _synonyms(tag):
        return ', '.join(s.name for s in tag.synonyms.all())
    _synonyms.short_description = _('synonyms')

    _fields = (_name, _synonyms)
else:
    _fields = ('name',)


admin.site.register(Tag,
    list_display = _fields,
)
admin.site.register(Synonym)

