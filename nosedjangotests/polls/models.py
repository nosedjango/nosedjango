from django.db import models
try:
    from django.db.transaction import atomic
except ImportError:  # Django 1.4
    from django.db.transaction import commit_on_success as atomic
from django.contrib.contenttypes import generic


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
    poll = generic.GenericForeignKey('content_type', 'object_id')

    choice = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    @atomic
    def reset(self):
        self.votes = 0
        self.save()
