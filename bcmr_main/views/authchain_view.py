from bcmr_main.models import IdentityOutput
from rest_framework.views import APIView
from django.http import JsonResponse


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
