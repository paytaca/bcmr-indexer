# Generated by Django 3.2 on 2023-07-27 16:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0022_auto_20230727_1602'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ownership',
            unique_together={('token_id', 'txid', 'index')},
        ),
    ]