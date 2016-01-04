# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
try:
    from django.db import migrations
except ImportError:
    pass
else:
    class Migration(migrations.Migration):

        dependencies = [
            ('contenttypes', '0002_remove_content_type_name'),
        ]

        operations = [
            migrations.CreateModel(
                name='Choice',
                fields=[
                    ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                    ('object_id', models.PositiveIntegerField()),
                    ('choice', models.CharField(max_length=200)),
                    ('votes', models.IntegerField(default=0)),
                    ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ],
            ),
            migrations.CreateModel(
                name='Poll',
                fields=[
                    ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                    ('question', models.CharField(max_length=200)),
                    ('pub_date', models.DateTimeField(verbose_name=b'date published')),
                ],
            ),
        ]
