# Generated by Django 3.2 on 2023-10-09 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0020_registry_allow_hash_mismatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='registry',
            name='watch_for_changes',
            field=models.BooleanField(default=False),
        ),
    ]
