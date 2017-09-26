from django.db import models
try:
    from django.db.transaction import atomic
except ImportError:  # Django 1.4
    from django.db.transaction import commit_on_success as atomic
try:
    from django.contrib.contenttypes.generic import GenericForeignKey
except ImportError:  # Django 1.11
    from django.contrib.contenttypes.fields import GenericForeignKey


class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    @atomic
    def reset(self):
        self.question = ""
        self.save()


class Choice(models.Model):
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    poll = GenericForeignKey('content_type', 'object_id')

    choice = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    @atomic
    def reset(self):
        self.votes = 0
        self.save()
