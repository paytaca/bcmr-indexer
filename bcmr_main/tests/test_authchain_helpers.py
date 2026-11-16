import logging
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import include, path

from bcmr_main.authchain import (
    AuthchainIdentityClaimError,
    get_authchain,
    get_authhead,
    get_last_identity_claim,
    get_last_identity_claim_detail,
    get_latest_registry,
    is_local_authhead,
)
from bcmr_main.models import IdentityOutput, Registry
from bcmr_main.utils import decode_bcmr_op_return_asm


AUTHBASE = "a" * 64
MIDDLE = "b" * 64
HEAD = "c" * 64
MISSING = "f" * 64

NEW_HASH = "ab" * 32
LEGACY_HASH = "e51f03b9a1778ce6702ace247920121dca070e3e5afd0f30b5e089a0cc7c0065"

# The project URLconf pulls in `cts`, which the test settings do not install.
# These view tests only need the bcmr_main routes.
urlpatterns = [path("api/", include("bcmr_main.urls"))]


def _asm(payload_hex: str, uri: str | None = None, magic: str = "1380795202") -> str:
    tokens = ["OP_RETURN", magic, payload_hex]
    if uri is not None:
        tokens.append(uri.encode().hex())
    return " ".join(tokens)


class _FakeRedis:
    def keys(self, *_args, **_kwargs):
        return []

    def delete(self, *_args, **_kwargs):
        return 0


@pytest.fixture(autouse=True)
def _fake_redis():
    """Keep Registry post_save cache invalidation off the real Redis server."""
    with patch("bcmr_main.signals.get_redis_client", return_value=_FakeRedis()):
        yield


def _make_chain():
    head = IdentityOutput.objects.create(txid=HEAD)
    middle = IdentityOutput.objects.create(txid=MIDDLE, spent=True, spender=head)
    authbase = IdentityOutput.objects.create(txid=AUTHBASE, spent=True, spender=middle)
    return authbase, middle, head


class TestDecodeBcmrOpReturnAsm:
    def test_decimal_magic_with_uri(self):
        decoded = decode_bcmr_op_return_asm(_asm(NEW_HASH, "api.example.com"))

        assert decoded is not None
        assert decoded.content_hash == NEW_HASH
        assert decoded.uris == ["api.example.com"]

    @pytest.mark.parametrize("magic", ["42434d52", "42434D52", "0x42434d52"])
    def test_hex_magic(self, magic):
        decoded = decode_bcmr_op_return_asm(_asm(NEW_HASH, magic=magic))

        assert decoded is not None
        assert decoded.content_hash == NEW_HASH

    def test_hash_only_output_has_no_uris(self):
        decoded = decode_bcmr_op_return_asm(_asm(NEW_HASH))

        assert decoded is not None
        assert decoded.content_hash == NEW_HASH
        assert decoded.uris == []

    def test_legacy_ascii_hash_is_decoded(self):
        legacy_payload = LEGACY_HASH.encode().hex()
        decoded = decode_bcmr_op_return_asm(_asm(legacy_payload, "example.com"))

        assert decoded is not None
        assert decoded.content_hash == LEGACY_HASH
        assert decoded.uris == ["example.com"]

    @pytest.mark.parametrize(
        "asm",
        [
            "",
            "OP_RETURN 1380795202",
            "OP_RETURN 1234 " + NEW_HASH,
            "OP_RETURN -1380795202 " + NEW_HASH,
            "OP_RETURN 1380795202 not-hex",
            "OP_RETURN 1380795202 deadbeef",
            "OP_RETURN 1380795202 " + ("00" * 64),
        ],
    )
    def test_rejects_malformed_outputs(self, asm):
        assert decode_bcmr_op_return_asm(asm) is None

    def test_invalid_uri_is_skipped(self):
        decoded = decode_bcmr_op_return_asm(_asm(NEW_HASH) + " not-hex" + " " + b"example.com".hex())

        assert decoded is not None
        assert decoded.uris == ["example.com"]


@pytest.mark.django_db
class TestAuthchainTraversal:
    def test_returns_chain_from_authbase_to_head(self):
        _make_chain()

        assert get_authchain(AUTHBASE) == [AUTHBASE, MIDDLE, HEAD]

    def test_flatten_false_returns_identity_outputs(self):
        _make_chain()

        chain = get_authchain(AUTHBASE, flatten=False)

        assert [output.txid for output in chain] == [AUTHBASE, MIDDLE, HEAD]

    def test_missing_authbase_returns_empty_chain(self):
        assert get_authchain(MISSING) == []

    def test_get_authhead_returns_last_output(self):
        _, _, head = _make_chain()

        assert get_authhead(AUTHBASE) == head

    def test_get_authhead_raises_for_missing_authbase(self):
        with pytest.raises(ValueError, match="not found"):
            get_authhead(MISSING)

    def test_is_local_authhead(self):
        _make_chain()

        assert is_local_authhead(AUTHBASE, HEAD) is True
        assert is_local_authhead(AUTHBASE, MIDDLE) is False

    def test_cycle_is_cut_off_and_logged(self, caplog):
        authbase = IdentityOutput.objects.create(txid=AUTHBASE, spent=True)
        middle = IdentityOutput.objects.create(txid=MIDDLE, spent=True, spender=authbase)
        authbase.spender = middle
        authbase.save()

        with caplog.at_level(logging.WARNING):
            chain = get_authchain(AUTHBASE)

        assert chain == [AUTHBASE, MIDDLE]
        assert "Cycle detected" in caplog.text


@pytest.mark.django_db
class TestIdentityClaims:
    def test_returns_newest_identity_output_with_registry(self):
        authbase, middle, _ = _make_chain()
        Registry.objects.create(
            txid=authbase.txid,
            index=0,
            publisher=authbase,
            op_return=_asm(NEW_HASH),
            contents={"old": True},
        )
        Registry.objects.create(
            txid=middle.txid,
            index=0,
            publisher=middle,
            op_return=_asm(NEW_HASH),
            contents={"new": True},
        )

        identity_output, registry = get_last_identity_claim(AUTHBASE)

        assert identity_output.txid == MIDDLE
        assert registry.contents == {"new": True}

    def test_lowest_index_is_the_definitive_publication(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=1,
            publisher=head,
            op_return=_asm(NEW_HASH),
            contents={"index": 1},
        )
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH),
            contents={"index": 0},
        )

        _, registry = get_last_identity_claim(AUTHBASE)

        assert registry.index == 0

    def test_returns_none_when_no_publication_exists(self):
        _make_chain()

        assert get_last_identity_claim(AUTHBASE) is None
        assert get_last_identity_claim(MISSING) is None

    def test_detail_decodes_current_format(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH, "api.example.com"),
        )

        detail = get_last_identity_claim_detail(AUTHBASE)

        assert detail == {
            "txid": HEAD,
            "content_hash": NEW_HASH,
            "uris": ["api.example.com"],
        }

    def test_detail_decodes_legacy_ascii_hash(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(LEGACY_HASH.encode().hex(), "example.com"),
        )

        detail = get_last_identity_claim_detail(AUTHBASE)

        assert detail["content_hash"] == LEGACY_HASH
        assert detail["uris"] == ["example.com"]

    def test_detail_returns_none_without_publication(self):
        _make_chain()

        assert get_last_identity_claim_detail(AUTHBASE) is None

    def test_detail_raises_for_empty_op_return(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return="",
            contents={},
        )

        with pytest.raises(AuthchainIdentityClaimError, match="missing op_return"):
            get_last_identity_claim_detail(AUTHBASE)

    def test_detail_raises_for_malformed_op_return(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return="OP_RETURN 1380795202 deadbeef",
            contents={},
        )

        with pytest.raises(AuthchainIdentityClaimError, match="invalid BCMR op_return"):
            get_last_identity_claim_detail(AUTHBASE)

    def test_latest_registry_returns_contents(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH),
            contents={"registry": "contents"},
        )

        assert get_latest_registry(AUTHBASE) == {"registry": "contents"}

    def test_latest_registry_returns_none_when_contents_unavailable(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH),
            contents=None,
        )

        assert get_latest_registry(AUTHBASE) is None

    def test_latest_registry_returns_none_without_publication(self):
        _make_chain()

        assert get_latest_registry(AUTHBASE) is None


@pytest.mark.django_db
@pytest.mark.urls(__name__)
class TestAuthchainViews:
    def test_authchain_endpoint(self):
        _make_chain()
        client = Client()

        response = client.get(f"/api/authchain/{AUTHBASE}/")

        assert response.status_code == 200
        assert response.json() == {
            "authbase": AUTHBASE,
            "authchain": [AUTHBASE, MIDDLE, HEAD],
        }

    def test_authchain_endpoint_returns_404_for_missing_authbase(self):
        response = Client().get(f"/api/authchain/{MISSING}/")

        assert response.status_code == 404

    def test_authhead_endpoint(self):
        _make_chain()

        response = Client().get(f"/api/authchain/{AUTHBASE}/authhead/")

        assert response.status_code == 200
        assert response.json()["authhead"]["txid"] == HEAD

    def test_authhead_endpoint_returns_404_for_missing_authbase(self):
        response = Client().get(f"/api/authchain/{MISSING}/authhead/")

        assert response.status_code == 404

    def test_is_authhead_endpoint(self):
        _make_chain()
        client = Client()

        head_response = client.get(f"/api/authchain/{AUTHBASE}/is-authhead/{HEAD}/")
        middle_response = client.get(f"/api/authchain/{AUTHBASE}/is-authhead/{MIDDLE}/")

        assert head_response.status_code == 200
        assert head_response.json()["is_authhead"] is True
        assert middle_response.status_code == 200
        assert middle_response.json()["is_authhead"] is False

    def test_is_authhead_endpoint_returns_200_false_for_garbage_txid(self):
        _make_chain()

        response = Client().get(f"/api/authchain/{AUTHBASE}/is-authhead/zzzz/")

        assert response.status_code == 200
        assert response.json()["is_authhead"] is False

    def test_last_publication_endpoint(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH, "api.example.com"),
        )

        response = Client().get(f"/api/authchain/{AUTHBASE}/last-publication/")

        assert response.status_code == 200
        assert response.json() == {
            "txid": HEAD,
            "content_hash": NEW_HASH,
            "uris": ["api.example.com"],
        }

    def test_last_publication_endpoint_returns_404_without_publication(self):
        _make_chain()

        response = Client().get(f"/api/authchain/{AUTHBASE}/last-publication/")

        assert response.status_code == 404

    def test_last_publication_endpoint_maps_data_errors_to_422(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return="",
            contents={},
        )

        response = Client().get(f"/api/authchain/{AUTHBASE}/last-publication/")

        assert response.status_code == 422

    def test_latest_registry_endpoint(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH),
            contents={"registry": "contents"},
        )

        response = Client().get(f"/api/authchain/{AUTHBASE}/latest-registry/")

        assert response.status_code == 200
        assert response.json() == {"registry": "contents"}

    def test_latest_registry_endpoint_returns_404_when_contents_unavailable(self):
        _, _, head = _make_chain()
        Registry.objects.create(
            txid=head.txid,
            index=0,
            publisher=head,
            op_return=_asm(NEW_HASH),
            contents=None,
        )

        response = Client().get(f"/api/authchain/{AUTHBASE}/latest-registry/")

        assert response.status_code == 404
