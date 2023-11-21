from operator import itemgetter
from django.utils import timezone
import dateutil.parser
from dateutil.parser import parse as parse_datetime
from bcmr_main.models import *
import copy


def generate_token_metadata(registry_obj):
    # Parse the BCMR to get the associated identities and tokens
    if not registry_obj.contents:
        return

    publisher_identities = []
    if registry_obj.publisher:
        publisher_identities = registry_obj.publisher.identities
    try:
        matched_identities = set(registry_obj.contents['identities'].keys()).intersection(set(publisher_identities))
    except KeyError:
        return
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
            snapshot_keys = identity_records.keys()
            snapshots = []
            for snapshot_key in snapshot_keys:
                try:
                    snapshots.append([snapshot_key, parse_datetime(snapshot_key)])
                except dateutil.parser._parser.ParserError:
                    pass
            if snapshots:
                snapshots.sort(key=itemgetter(1))
                latest_key, history_date = snapshots[-1]
                token_data = registry_obj.contents['identities'][identity][latest_key]['token']
                token_check = Token.objects.filter(category=token_data['category'])
                if token_check.exists():
                    # Check if token is NFT
                    if token_check.filter(is_nft=True).exists():
                        _metadata = copy.deepcopy(registry_obj.contents['identities'][identity][latest_key])
                        # remove the 'nfts' key to be replaced later by metadata for each type
                        try:
                            del _metadata['token']['nfts']
                        except KeyError:
                            pass

                        if 'nfts' in token_data.keys():
                            # Deal with the nft types
                            nft_types = token_data['nfts']['parse']['types']
                            for nft_type_key in nft_types:
                                nft_token_check = Token.objects.filter(
                                    category=token_data['category'],
                                    # TODO: Refactor this later to support parseable NFTs. For now,
                                    # this only works for NFTs with type key equal to commitment.
                                    commitment=nft_type_key,
                                    capability='none'
                                )
                                if nft_token_check.exists():
                                    _metadata['type_metadata'] = token_data['nfts']['parse']['types'][nft_type_key]
                                    nft_token = nft_token_check.last()
                                    nft_token_metadata, _ = TokenMetadata.objects.get_or_create(
                                        token=nft_token,
                                        registry=registry_obj,
                                        identity=registry_obj.publisher,
                                        metadata_type='type'
                                    )
                                    nft_token_metadata.contents = _metadata
                                    nft_token_metadata.date_created = history_date
                                    nft_token_metadata.save()
                        # Save the generic NFT category metadata on the first token of this category ever created
                        try:
                            del _metadata['type_metadata']
                        except KeyError:
                            pass
                        token = token_check.filter(is_nft=True).order_by('date_created', 'id').last()
                        if token:
                            token_metadata, _ = TokenMetadata.objects.get_or_create(
                                token=token,
                                registry=registry_obj,
                                identity=registry_obj.publisher,
                                metadata_type='category'
                            )
                            token_metadata.contents = _metadata
                            token_metadata.date_created = history_date
                            token_metadata.save()
                    else:
                        try:
                            token = Token.objects.get(category=token_data['category'], is_nft=False)
                            _metadata = registry_obj.contents['identities'][identity][latest_key]
                            token_metadata, _ = TokenMetadata.objects.get_or_create(
                                token=token,
                                registry=registry_obj,
                                identity=registry_obj.publisher,
                                metadata_type='category'
                            )
                            token_metadata.contents = _metadata
                            token_metadata.date_created = history_date
                            token_metadata.save()
                        except Token.DoesNotExist:
                            pass
