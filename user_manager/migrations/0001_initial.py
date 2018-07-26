# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-18 13:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserManagerRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unregistered_manager_email', models.EmailField(help_text=b"The email address for a manager if they haven't currently registered for an account.", max_length=254)),
                ('manager_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='usermanagerrole',
            unique_together=set([('user', 'unregistered_manager_email'), ('user', 'manager_user')]),
        ),
    ]
