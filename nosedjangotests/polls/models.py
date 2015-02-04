from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    poll = generic.GenericForeignKey('content_type', 'object_id')

    choice = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class PollPair(models.Model):
    first_poll = models.ForeignKey(
        Poll,
        related_name='first_pairs',
    )
    last_poll = models.ForeignKey(
        Poll,
        related_name='last_pairs',
    )
