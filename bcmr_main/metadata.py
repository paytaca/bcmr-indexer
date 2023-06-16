from operator import itemgetter
from django.utils import timezone
from dateutil.parser import parse as parse_datetime
from bcmr_main.models import Token, TokenMetadata, IdentityOutput


def generate_token_metadata(registry_obj):
    # Parse the BCMR to get the associated identities and tokens
    publisher_identities = []
    if registry_obj.publisher:
        publisher_identities = registry_obj.publisher.identities
    matched_identities = set(registry_obj.contents['identities'].keys()).intersection(set(publisher_identities))
    if matched_identities:
        validity_checks = registry_obj.validity_checks
        validity_checks['identities_match'] = True
        registry_obj.validity_checks = validity_checks
        registry_obj.save()

    # Parse and save metadata regardless if identities are valid or not
    for identity in list(matched_identities):
        # Get the latest non-future identity history record
        identity_records = registry_obj.contents['identities'][identity]
        if isinstance(identity_records, dict):
            histories_keys = identity_records.keys()
            histories = [
                (x, parse_datetime(x)) for x in histories_keys if parse_datetime(x) <= timezone.now()
            ]
            histories.sort(key=itemgetter(1))
            latest_key, history_date = histories[-1]
            token_data = registry_obj.contents['identities'][identity][latest_key]['token']
            token_check = Token.objects.filter(category=token_data['category'])
            if token_check.exists():
                token = token_check.last()
                if 'nfts' in token_data.keys():
                    nft_types = token_data['nfts']['parse']['types']
                    for nft_type_key in nft_types:
                        nft_token_check = Token.objects.filter(
                            category=token_data['category'],
                            # TODO: Refactor this later to support parseable NFTs. For now,
                            # this only works for NFTs with type key equal to commitment.
                            commitment=nft_type_key,
                            capability=None
                        )
                        if nft_token_check.exists():
                            nft_token = nft_token_check.last()
                            nft_token_metadata, _ = TokenMetadata.objects.get_or_create(
                                token=nft_token,
                                registry=registry_obj,
                                identity=IdentityOutput.objects.get(txid=identity)
                            )
                            nft_token_metadata.contents = token_data['nfts']['parse']['types'][nft_type_key],
                            nft_token_metadata.date_created = history_date
                            nft_token_metadata.save()
                else:
                    token_metadata, _ = TokenMetadata.objects.get_or_create(
                        token=token,
                        registry=registry_obj,
                        identity=IdentityOutput.objects.get(txid=identity)
                    )
                    token_metadata.contents=registry_obj.contents['identities'][identity][latest_key],
                    token_metadata.date_created=history_date
                    token_metadata.save()
