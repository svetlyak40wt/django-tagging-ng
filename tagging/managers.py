"""
Custom managers for Django models registered with the tagging
application.
"""
from django.db import models

from tagging.models import TaggedItem

class ModelTaggedItemManager(models.Manager):
    """
    A manager for retrieving model instances based on their tags.
    """
    def related_to(self, obj):
        return TaggedItem.objects.get_related(obj, self.model)

    def with_all(self, tags):
        return TaggedItem.objects.get_by_model(self.model, tags)

    def with_any(self, tags):
        return TaggedItem.objects.get_union_by_model(self.model, tags)
