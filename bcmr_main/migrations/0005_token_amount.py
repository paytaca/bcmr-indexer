# Generated by Django 3.1.6 on 2023-06-13 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0004_auto_20230613_1428'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='amount',
            field=models.BigIntegerField(null=True),
        ),
    ]
