from django.contrib import admin
from tagging.models import Tag, TaggedItem, Synonym
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from tagging import settings
from tagging.forms import TagAdminForm

admin.site.register(TaggedItem)

if settings.MULTILINGUAL_TAGS:
    import multilingual

    def _name(tag):
        return tag.name_any
    _name.short_description = _('name')

    def _synonyms(tag):
        return ', '.join(s.name for s in tag.synonyms.all())
    _synonyms.short_description = _('synonyms')

    class TagAdmin(multilingual.ModelAdmin):
        form = TagAdminForm
        list_display = (_name, _synonyms)

    _synonym_tag_name = 'name_any'
else:
    class TagAdmin(admin.ModelAdmin):
        form = TagAdminForm
        list_display = ('name',)

    _synonym_tag_name = 'name'


admin.site.register(Tag, TagAdmin)

def _tag_name(synonym):
    return '<a href="%s">%s</a>' % (
        reverse('admin_tagging_tag_change', args=(synonym.tag.id,)),
        getattr(synonym.tag, _synonym_tag_name)
    )
_tag_name.short_description = _('tag')
_tag_name.allow_tags = True

admin.site.register(Synonym,
    list_display = ('name', _tag_name),
)
