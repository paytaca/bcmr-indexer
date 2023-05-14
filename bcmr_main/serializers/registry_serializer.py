from rest_framework import serializers

from bcmr_main.serializers.token_serializer import TokenSerializer
from bcmr_main.models import Registry


class RegistrySerializer(serializers.ModelSerializer):
    latestRevision = serializers.SerializerMethodField()
    registryIdentity = serializers.SerializerMethodField()
    identities = serializers.SerializerMethodField()

    class Meta:
        model = Registry
        fields = (
            'version',
            'latestRevision',
            'registryIdentity',
            'identities',
        )

    def get_latestRevision(self, obj):
        return obj.latest_revision

    def get_registryIdentity(self, obj):
        return obj.registry_identity

    def get_identities(self, obj):
        key = obj.token.updated_at.isoformat()
        token = TokenSerializer(obj.token)
        return { 
            obj.token.category: {
                key: token.data
            }
        }
