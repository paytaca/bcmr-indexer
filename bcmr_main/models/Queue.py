from django.db import models


class QueuedTransaction(models.Model):
    txid = models.CharField(max_length=70, db_index=True, unique=True)
    details = models.JSONField()
