from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=255)
    json_hash = serializers.CharField(max_length=100)
    bcmr_url_encoded = serializers.CharField(max_length=255)
