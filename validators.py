import re
from django.core.validators import ValidationError

tag_list_re = re.compile(r'^[- \w]+$')

def isTagList(field_data, all_data):
    if not tag_list_re.search(field_data):
        raise ValidationError, 'This value must contain only letters, numbers, underscores, hyphens or spaces.'
    tag_names = field_data.split()
    for tag_name in tag_names:
        if len(tag_name) > 50:
            raise ValidationError, 'Each tag name must be no longer than 50 characters.'