from django.db import models
from django.contrib.contenttypes import generic


class Poll(models.Model):
    question = models.CharField(max_length=200, db_index=True)
    pub_date = models.DateTimeField('date published', db_index=True)


class Choice(models.Model):
    content_type = models.ForeignKey('contenttypes.ContentType', db_index=True)
    object_id = models.PositiveIntegerField(db_index=True)
    poll = generic.GenericForeignKey('content_type', 'object_id')

    choice = models.CharField(max_length=200, db_index=True)
    votes = models.IntegerField(default=0, db_index=True)
