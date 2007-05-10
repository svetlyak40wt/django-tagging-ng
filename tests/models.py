from django.db import models
from tagging.fields import TagField

class Parrot(models.Model):
    state = models.CharField(maxlength=50)

    def __str__(self):
        return self.state

    class Meta:
        ordering = ['state']