# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-02 18:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_reg_form', '0002_auto_20190502_1421'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='extrainfo',
            name='instructor',
        ),
        migrations.AddField(
            model_name='extrainfo',
            name='usage',
            field=models.CharField(choices=[(b'student', b'Student'), (b'instructor', b'Instructor')], default=b'student', max_length=10, verbose_name=b'Usage'),
        ),
        migrations.AlterField(
            model_name='extrainfo',
            name='goals',
            field=models.CharField(default=b'', max_length=100, verbose_name=b'Goals'),
        ),
        migrations.AlterField(
            model_name='extrainfo',
            name='organization',
            field=models.CharField(default=b'', max_length=100, verbose_name=b'University or Organization'),
        ),
    ]
