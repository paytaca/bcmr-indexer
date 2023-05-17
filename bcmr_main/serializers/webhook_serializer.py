from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):
    tx_hash = serializers.CharField(max_length=255)
