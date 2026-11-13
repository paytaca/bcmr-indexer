from __future__ import annotations
from dataclasses import asdict

from bcmr_main.models import IdentityOutput, Registry
from bcmr_main.utils import decode_bcmr_op_return_asm

def get_authchain(authbase: str, flatten: bool = True) -> list[str] | list[IdentityOutput]:
    identity_output = (
        IdentityOutput.objects.select_related("spender")
        .filter(txid=authbase)
        .first()
    )
    if not identity_output:
        return []

    authchain = []
    visited_ids = set()

    while identity_output and identity_output.id not in visited_ids:
        
        visited_ids.add(identity_output.id)
        if flatten:
            authchain.append(identity_output.txid)
        else:
            authchain.append(identity_output)

        if identity_output.spent:
            identity_output = identity_output.spender
        else:
            identity_output = None


    return authchain


def get_authhead(authbase: str) -> IdentityOutput:
    authchain = get_authchain(authbase, flatten=False)
    if not authchain:
        raise ValueError(f"Authbase: {authbase} not found")
    return authchain[-1]


def get_last_identity_claim(authbase: str) -> tuple[IdentityOutput, Registry] | None:
    authchain = get_authchain(authbase, flatten=False)
    if not authchain:
        return None

    txids = [output.txid for output in authchain]
    registries_by_txid = {
        reg.txid: reg
        for reg in Registry.objects.filter(txid__in=txids).order_by("-index")
    }

    for identity_output in reversed(authchain):
        registry = registries_by_txid.get(identity_output.txid)
        if registry:
            return (identity_output, registry)

    return None

class AuthchainIdentityClaimError(Exception):
    """Raised when an identity claim is missing its expected registry or op_return."""
    pass

def get_last_identity_claim_detail(authbase: str) -> dict | None:
    identity_claim = get_last_identity_claim(authbase)
    if not identity_claim:
        return None
    identity_output, registry = identity_claim
    if not registry.op_return:
        raise AuthchainIdentityClaimError(
            f"Registry {registry.id} (txid={registry.txid}) "
            f"for authbase={authbase} is missing op_return."
        )

    identity_claim_detail = decode_bcmr_op_return_asm(registry.op_return)
    if not identity_claim_detail:
        return None

    identity_claim_detail = asdict(identity_claim_detail)
    return {
        "txid": identity_output.txid,
        **identity_claim_detail,
    }


def get_latest_registry(authbase: str) -> dict | None:
    last_publication = get_last_identity_claim(authbase)
    if last_publication:
        _, registry = last_publication
        return registry.contents
    return None


def is_authhead(authbase: str, txid: str) -> bool:
    authhead = get_authhead(authbase)
    return authhead.txid == txid
