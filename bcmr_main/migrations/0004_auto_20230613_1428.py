# Generated by Django 3.1.6 on 2023-06-13 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcmr_main', '0003_identityoutput_identities'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identityoutput',
            name='identities',
            field=models.ManyToManyField(related_name='_identityoutput_identities_+', to='bcmr_main.IdentityOutput'),
        ),
    ]
