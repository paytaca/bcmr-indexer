# Generated by Django 3.2 on 2024-01-25 00:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0023_remove_registry_content'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='identityoutput',
            name='bcmr_main_i_txid_e88a5f_idx',
        ),
        migrations.RemoveIndex(
            model_name='ownership',
            name='bcmr_main_o_address_a7530f_idx',
        ),
        migrations.RemoveIndex(
            model_name='queuedtransaction',
            name='bcmr_main_q_txid_8ed8f2_idx',
        ),
        migrations.RemoveIndex(
            model_name='registry',
            name='bcmr_main_r_txid_49f468_idx',
        ),
        migrations.RemoveIndex(
            model_name='token',
            name='bcmr_main_t_categor_980116_idx',
        ),
        migrations.RemoveIndex(
            model_name='tokenmetadata',
            name='bcmr_main_t_metadat_8d3871_idx',
        ),
        migrations.AlterField(
            model_name='blockscan',
            name='height',
            field=models.IntegerField(db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='identityoutput',
            name='authbase',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='identityoutput',
            name='spent',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='identityoutput',
            name='txid',
            field=models.CharField(db_index=True, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='ownership',
            name='address',
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='ownership',
            name='burned',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='ownership',
            name='spent',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='registry',
            name='date_created',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='registry',
            name='generated_metadata',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='registry',
            name='index',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='registry',
            name='txid',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='registry',
            name='valid',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='token',
            name='capability',
            field=models.CharField(blank=True, choices=[('minting', 'Minting'), ('mutable', 'Mutable'), ('none', 'None')], db_index=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='token',
            name='category',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='token',
            name='commitment',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='token',
            name='is_nft',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='tokenmetadata',
            name='date_created',
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='tokenmetadata',
            name='metadata_type',
            field=models.CharField(blank=True, choices=[('category', 'Category'), ('type', 'Type')], db_index=True, max_length=20, null=True),
        ),
    ]
