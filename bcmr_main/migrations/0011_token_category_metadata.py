# Generated by Django 3.1.6 on 2023-06-17 02:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0010_auto_20230616_0923'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='category_metadata',
            field=models.BooleanField(default=False),
        ),
    ]
