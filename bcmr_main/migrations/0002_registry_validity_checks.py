# Generated by Django 3.1.6 on 2023-06-13 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registry',
            name='validity_checks',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
