"""Authchain traversal helpers backed by the local indexer database."""
from __future__ import annotations

import logging
from dataclasses import asdict

from bcmr_main.models import IdentityOutput, Registry
from bcmr_main.utils import decode_bcmr_op_return_asm

LOGGER = logging.getLogger(__name__)


def get_authchain(authbase: str, flatten: bool = True) -> list[str] | list[IdentityOutput]:
    """Return the authchain starting at ``authbase`` and following spenders.

    The chain runs from the authbase output to the current authhead. A
    visited-id guard prevents malformed data (a cycle in ``spender`` links)
    from looping forever.
    """
    identity_output = (
        IdentityOutput.objects.select_related("spender")
        .filter(txid=authbase)
        .first()
    )
    if not identity_output:
        return []

    authchain = []
    visited_ids = set()

    while identity_output:
        if identity_output.id in visited_ids:
            LOGGER.warning(
                "Cycle detected in authchain for authbase=%s at output=%s",
                authbase,
                identity_output.txid,
            )
            break

        visited_ids.add(identity_output.id)
        if flatten:
            authchain.append(identity_output.txid)
        else:
            authchain.append(identity_output)

        identity_output = identity_output.spender if identity_output.spent else None

    return authchain


def get_authhead(authbase: str) -> IdentityOutput:
    """Return the current authhead (the last output in the authchain)."""
    authchain = get_authchain(authbase, flatten=False)
    if not authchain:
        raise ValueError(f"Authbase: {authbase} not found")
    return authchain[-1]


def get_last_identity_claim(authbase: str) -> tuple[IdentityOutput, Registry] | None:
    """Return the newest identity output that has a Registry row.

    This is the raw lookup and does not validate the registry's ``op_return``;
    use ``get_last_identity_claim_detail`` when the decoded claim is needed.

    When a transaction has multiple Registry rows, the lowest output index is
    used: CHIP-BCMR treats the first (lowest-index) publication output as the
    definitive one.
    """
    authchain = get_authchain(authbase, flatten=False)
    if not authchain:
        return None

    txids = [output.txid for output in authchain]
    registries_by_txid = {}
    for registry in Registry.objects.filter(txid__in=txids).order_by("index"):
        registries_by_txid.setdefault(registry.txid, registry)

    for identity_output in reversed(authchain):
        registry = registries_by_txid.get(identity_output.txid)
        if registry:
            return (identity_output, registry)

    return None


class AuthchainIdentityClaimError(Exception):
    """Raised when an identity claim is missing or malformed."""
    pass


def get_last_identity_claim_detail(authbase: str) -> dict | None:
    """Return the decoded OP_RETURN publication for the newest identity claim.

    Returns ``None`` when the authchain has no publication at all. Raises
    ``AuthchainIdentityClaimError`` when a publication row exists but its
    OP_RETURN is missing or cannot be decoded.
    """
    identity_claim = get_last_identity_claim(authbase)
    if not identity_claim:
        return None
    identity_output, registry = identity_claim
    if not registry.op_return:
        raise AuthchainIdentityClaimError(
            f"Registry {registry.id} (txid={registry.txid}) "
            f"for authbase={authbase} is missing op_return."
        )

    decoded = decode_bcmr_op_return_asm(registry.op_return)
    if not decoded:
        raise AuthchainIdentityClaimError(
            f"Registry {registry.id} (txid={registry.txid}) "
            f"for authbase={authbase} has an invalid BCMR op_return."
        )

    payload = asdict(decoded)
    return {
        "txid": identity_output.txid,
        **payload,
    }


def get_latest_registry(authbase: str) -> dict | None:
    """Return the contents of the newest registry publication, if available.

    The stored contents are returned without re-validating the publication
    ``op_return``; use ``get_last_identity_claim_detail`` for the claim data.
    """
    last_publication = get_last_identity_claim(authbase)
    if last_publication:
        _, registry = last_publication
        return registry.contents
    return None


def is_local_authhead(authbase: str, txid: str) -> bool:
    """Return whether ``txid`` is the current authhead for ``authbase``.

    This is the database-backed counterpart to
    ``bcmr_main.utils.is_authhead`` (which queries Chaingraph).
    """
    authhead = get_authhead(authbase)
    return authhead.txid == txid
