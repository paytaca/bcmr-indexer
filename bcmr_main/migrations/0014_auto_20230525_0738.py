# Generated by Django 3.1.6 on 2023-05-25 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0013_auto_20230525_0625'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registry',
            name='url',
        ),
        migrations.AddField(
            model_name='token',
            name='bcmr_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]