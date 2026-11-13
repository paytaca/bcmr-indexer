from bcmr_main.models import IdentityOutput
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)

from bcmr_main.authchain import (
    get_authchain,
    get_authhead,
    get_last_identity_claim_detail,
    get_latest_registry,
    is_authhead,
    AuthchainIdentityClaimError
)

class AuthchainHeadView(APIView):
    def get(self, request, *args, **kwargs):
        category = kwargs.get('category', '')
        authhead_txid = None
        authhead_owner = None
        data = {}
        authhead_check = IdentityOutput.objects.filter(identities__contains='{' + category + '}', spent=False).last()
        if authhead_check:
            authhead_txid = authhead_check.txid
            authhead_owner = authhead_check.address
        else:
            data['error'] = 'category not found'

        if authhead_txid and authhead_owner:
            data = {
                'authchain_head': {
                    'txid': authhead_txid,
                    'owner': authhead_owner
                } 
            }
        return JsonResponse(data)


class AuthchainView(APIView):
    def get(self, request, authbase: str):
        authchain = get_authchain(authbase)
        if not authchain:
            return JsonResponse(
                {"detail": f"Authbase: {authbase} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return JsonResponse({"authbase": authbase, "authchain": authchain}, status=status.HTTP_200_OK)

class AuthchainAuthheadByAuthbase(APIView):
    """GET /authchain/<authbase>/head/"""

    def get(self, request, authbase: str):
        try:
            authhead = get_authhead(authbase)
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return JsonResponse(
            {
                "authbase": authbase,
                "authhead": {
                    "txid": authhead.txid,
                    "owner": authhead.address,
                    "block": authhead.block,
                },
            },
            status=status.HTTP_200_OK,
        )

class AuthchainIsAuthheadView(APIView):
    
    """GET /authchain/<authbase>/is-head/<txid>/"""
    def get(self, request, authbase: str, txid: str):
        try:
            result = is_authhead(authbase, txid)
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return JsonResponse(
            {"authbase": authbase, "txid": txid, "is_authhead": result},
            status=status.HTTP_200_OK,
        )

class AuthchainLastPublicationView(APIView):
    """GET /authchain/<authbase>/last-publication/"""
    def get(self, request, authbase: str):
        try:
            last_identity_claim = get_last_identity_claim_detail(authbase)
        except AuthchainIdentityClaimError as exc:
            logger.exception("Invalid identity claim for authbase=%s", authbase)
            return JsonResponse(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not last_identity_claim:
            return JsonResponse(
                {"detail": f"No publication found for authbase: {authbase}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return JsonResponse(last_identity_claim, status=status.HTTP_200_OK)

class AuthchainLatestRegistryView(APIView):
    """GET /authchain/<authbase>/latest-registry/"""

    def get(self, request, authbase: str):
        registry = get_latest_registry(authbase)
        if registry is None:
            return JsonResponse(
                {"detail": f"No registry found for authbase: {authbase}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return JsonResponse(registry, status=status.HTTP_200_OK, safe=False)

