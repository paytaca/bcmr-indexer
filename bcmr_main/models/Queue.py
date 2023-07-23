from django.db import models

from picklefield.fields import PickledObjectField


class QueuedTransaction(models.Model):
    txid = models.CharField(max_length=100, db_index=True, unique=True)
    details = PickledObjectField()

    class Meta:
        verbose_name_plural = 'Queued transactions'
        get_latest_by = 'date_created'
        indexes = [
            models.Index(
                fields=[
                    'txid'
                ]
            )
        ]
