# Generated by Django 3.2 on 2024-11-29 11:21

import django.contrib.postgres.indexes
from django.db import migrations
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0027_remove_registry_contents__identities_idx'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='identityoutput',
            index=django.contrib.postgres.indexes.GinIndex(django.db.models.expressions.F('identities'), name='identities_idx'),
        ),
    ]