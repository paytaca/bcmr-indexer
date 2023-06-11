import pytest
from bcmr_main.models import Registry
from unittest.mock import MagicMock

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestRegistryExistence:
    pytestmark = pytest.mark.django_db

    def test_registry_existence(self):
        registry = Registry.objects.filter(txid='test_txid')
        assert registry.exists() == False


class TestWithMock:

    def test_mocking(self):
        thing = Registry()
        thing.save = MagicMock(return_value=3)
        thing.save('txid')
        thing.save.assert_called_with('txid')
