import pytest

@pytest.mark.django_db
class TestOne:

    def test_one(self):
        assert (1+1) == 2
