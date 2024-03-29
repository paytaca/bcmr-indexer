# Generated by Django 3.1.6 on 2023-06-18 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0013_auto_20230617_1431'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='queuedtransaction',
            options={'get_latest_by': 'date_created', 'verbose_name_plural': 'Queued transactions'},
        ),
        migrations.AddIndex(
            model_name='queuedtransaction',
            index=models.Index(fields=['txid'], name='bcmr_main_q_txid_8ed8f2_idx'),
        ),
    ]
