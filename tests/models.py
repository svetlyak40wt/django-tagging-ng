from django.db import models

class Perch(models.Model):
    size = models.IntegerField()
    smelly = models.BooleanField(default=True)

class Parrot(models.Model):
    state = models.CharField(maxlength=50)
    perch = models.ForeignKey(Perch, null=True)

    def __str__(self):
        return self.state

    class Meta:
        ordering = ['state']

class Link(models.Model):
    name = models.CharField(maxlength=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Article(models.Model):
    name = models.CharField(maxlength=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
