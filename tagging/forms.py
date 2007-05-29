from django import newforms as forms
from tagging.utils import get_tag_name_list
from tagging.validators import tag_list_re

class TagField(forms.CharField):
    def clean(self, value):
        """
        Validates that the input is a valid list of tag names,
        separated by a single comma, a single space or a comma
        followed by a space.
        """
        value = super(TagField, self).clean(value)
        if value == u'':
            return value
        if not tag_list_re.search(value):
            raise forms.ValidationError(u'Tag names must contain only unicode alphanumeric characters, numbers, underscores or hyphens, with a comma, space or comma followed by space used to separate each tag name.')
        tag_names = get_tag_name_list(value)
        for tag_name in tag_names:
            if len(tag_name) > 50:
                raise forms.ValidationError(u'Tag names must be no longer than 50 characters.')
        return value