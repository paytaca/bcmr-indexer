import json
import datetime
from django.db import models
from django.contrib.postgres.indexes import GinIndex


class Registry(models.Model):
    txid = models.CharField(max_length=100, db_index=True)
    index = models.IntegerField(db_index=True)
    publisher = models.ForeignKey(
        'IdentityOutput',
        related_name='registries',
        on_delete=models.CASCADE,
        null=True
    )
    contents = models.JSONField(null=True, blank=True)
    valid = models.BooleanField(default=False, db_index=True)
    op_return = models.TextField(default='')
    bcmr_url = models.TextField(default='')
    bcmr_request_status = models.IntegerField(null=True, blank=True)
    validity_checks = models.JSONField(null=True, blank=True)
    allow_hash_mismatch = models.BooleanField(default=False)
    watch_for_changes = models.BooleanField(default=False)
    date_created = models.DateTimeField(null=True, blank=True, db_index=True)
    generated_metadata = models.DateTimeField(null=True, blank=True, db_index=True)

    def get_identities(self):

        query = f"""
            SELECT id, 
            jsonb_object_keys(contents->'identities') AS authbase 
            FROM bcmr_main_registry WHERE id=%s;""" % self.id
        
        return [i.authbase for i in Registry.objects.raw(query)]

    def get_identity_history(self, authbase:str = None):
        """
        Returns history of specific authbase, or all identities if authbase (authbase) isn't provided.
        """
        query = """
            SELECT 
                id, 
                jsonb_object_keys(contents->'identities'->'%s') AS timestamp from bcmr_main_registry WHERE id=%s;
        """ % (authbase, self.id)

        if authbase: 
            return {
                authbase: [i.timestamp for i in Registry.objects.raw(query)]
            }
        
        histories = {}
    
        for authbase in self.get_identities():
            histories[authbase] = [i.timestamp for i in Registry.objects.raw(query)]
    
        return histories
    
    def get_parse_bytecode(self, authbase:str, identity_history_timestamp: str):
        query = f"""
                    SELECT id, 
                    jsonb_extract_path(contents, 'identities', '{authbase}', '{identity_history_timestamp}', 'token','category') AS category,
                    jsonb_extract_path(contents, 'identities', '{authbase}', '{identity_history_timestamp}', 'token', 'nfts', 'parse', 'bytecode') AS bytecode 
                    FROM bcmr_main_registry WHERE id = {self.id};
                """
        
        r = Registry.objects.raw(query)
        if len(r) > 0:
            bytecode = r[0].bytecode
            if bytecode and type(bytecode) == str:
                bytecode = json.loads(bytecode)
            return {
                'bytecode': bytecode,
                '_meta': {
                    'registry_id': r[0].id,
                    'authbase': authbase,
                    'identity_history': identity_history_timestamp,
                    'category': r[0].category.replace('"',''),
                }
            }

    def get_token_category_basic(self, category):
        """
        Return the basic TokenCategory details
        """
        query = """
            SELECT 
                id, 
                authbase, 
                identity_history, 
                symbol,
                decimals,
                category
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'symbol') AS symbol,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'decimal') AS decimals,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history
                ORDER BY id DESC
            ) AS subquery
            
            WHERE category = '"%s"' and identity_history <= '%s'
            ORDER BY identity_history DESC 
            LIMIT 1;
        """ % (category, datetime.datetime.utcnow().isoformat())
        r = Registry.objects.raw(query)
        if r:
            return {
                'token': {
                    'symbol': r[0].symbol.replace('"',''),
                    'decimals': r[0].decimals,
                    'category': r[0].category.replace('"',''),
                },
                '_meta': {
                    'registry_id': r[0].id,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                }
            }

    def get_identity_snapshot(self, category):
        """
        Return To
        """

        query = """
            SELECT 
                id, 
                authbase, 
                identity_history, 
                identity_snapshot,
                category
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history) AS identity_snapshot,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history
                ORDER BY id DESC
            ) AS subquery
            
            WHERE category = '"%s"' and identity_history <= '%s'
            ORDER BY identity_history DESC 
            LIMIT 1;
        """ % (category, datetime.datetime.utcnow().isoformat())

        r = Registry.objects.raw(query)
        if r:
            identity_snapshot = r[0].identity_snapshot
            if identity_snapshot:
                identity_snapshot = json.loads(identity_snapshot)
            return {
                'identity_snapshot': identity_snapshot,
                '_meta': {
                    'registry_id': r[0].id,
                    'category': category,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                }
            }
    
    def get_identity_snapshot_nft_type(self, category, nft_type_key):
        """
        Return To IdentitySnapshot of the particular NftType;s key. Where key is a commitment or bottomAltStackHex
        """

        query = """
            SELECT DISTINCT ON(nft_type_key) *
            FROM (
                SELECT 
                    id,
                    authbase,
                    identity_history,
                    nft_type_key,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'name') AS name,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'description') AS description,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'uris') AS uris,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'tags') AS tags,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'migrated') AS migrated,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'status') AS status,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'split_id') AS split_id,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'extensions') AS extensions,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'symbol') AS token_symbol,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS token_category,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'decimals') AS token_decimals,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts', 'parse', 'bytecode') AS nft_parse_bytecode,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts', 'parse', 'types', nft_type_key) AS nft_type

                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types') = 'object' 
                            THEN contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types'
                            ELSE '{}'::jsonb 
                        END
                    ) AS nft_type_key
                    WHERE nft_type_key = '%s'
            ) AS subquery
            
            WHERE category = '"%s"' and identity_history <= '%s' 
            ORDER BY nft_type_key, identity_history DESC 
        """ % (nft_type_key, category, datetime.datetime.utcnow().isoformat())


        r = Registry.objects.raw(query)
        if r and r[0]:
            identity_snapshot_fields = [
                'name',
                'description',
                'uris',
                'tags',
                'migrated',
                'status',
                'split_id',
                'extensions'
            ]

            identity_snapshot = {key: json.loads((getattr(r[0], key, None) or '""')) for key in identity_snapshot_fields if getattr(r[0], key, None) is not None}
            # token = {key.split('_')[1]: json.loads((getattr(r[0], key, None) or '""')) for key in token_fields if getattr(r[0], key, None) is not None}
            token = {
                'symbol': (getattr(r[0], 'token_symbol', '') or '').replace('"',''),
                'category': (getattr(r[0], 'token_category', '') or '').replace('"',''),
                'decimals': (getattr(r[0], 'token_decimals', '') or '').replace('"',''),
            }

            nft_type = getattr(r[0], 'nft_type', None)
            if nft_type:
                token['nfts'] = {
                    'parse': {
                        'bytecode': getattr(r[0], 'nft_parse_bytecode', None),
                        'types': {
                            r[0].nft_type_key: json.loads(getattr(r[0], 'nft_type', None))
                        }
                    }
                }

            identity_snapshot['token'] = token 

            return {
                **identity_snapshot,
                '_meta': {
                    'registry_id': r[0].id,
                    'category': category,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                    'nft_type_key': r[0].nft_type_key,

                }
            }
    

    def get_identity_snapshot_basic(self, category):
        """
        Return the basic IdentitySnapshot details without the token field. 
        The token field contains nfts.
        Omit <IdentitySnapshot, 'token'>
        """
        query = """
            SELECT 
                id, 
                authbase, 
                identity_history, 
                name,
                description,
                tags,
                migrated,
                status,
                split_id,
                uris,
                extensions,
                token_category,
                token_symbol,
                token_decimals,
                token_nfts_parse_bytecode
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'name') AS name,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'description') AS description,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'tags') AS tags,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'migrated') AS migrated,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'status') AS status,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'splitId') AS split_id,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'uris') AS uris,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'extensions') AS extensions,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS token_category,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'symbol') AS token_symbol,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'decimals') AS token_decimals,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts', 'parse', 'bytecode') AS token_nfts_parse_bytecode
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history
                ORDER BY id DESC
            ) AS subquery
            
            WHERE token_category = '"%s"' and identity_history <= '%s'
            ORDER BY identity_history DESC 
            LIMIT 1;
        """ % (category, datetime.datetime.utcnow().isoformat())
        r = Registry.objects.raw(query)
        if r:
            identity_snapshot = {
                'name': json.loads(r[0].name or '""')
            }
            if r[0].description:
                identity_snapshot['description'] = json.loads(r[0].description)
            if r[0].tags:
                identity_snapshot['tags'] = json.loads(r[0].tags)
            if r[0].migrated:
                identity_snapshot['migrated'] = json.loads(r[0].migrated)
            if r[0].status:
                identity_snapshot['status'] = json.loads(r[0].status)
            if r[0].split_id:
                identity_snapshot['splitId'] = json.loads(r[0].split_id)
            if r[0].uris:
                identity_snapshot['uris'] = json.loads(r[0].uris)
            if r[0].extensions:
                identity_snapshot['extensions'] = json.loads(r[0].extensions)
            if r[0].token_category:
                identity_snapshot['token'] = {
                    'category': json.loads(r[0].token_category)
                }
                if r[0].token_symbol:
                    identity_snapshot['token']['symbol'] = json.loads(r[0].token_symbol)
                if r[0].token_decimals:
                    identity_snapshot['token']['decimals'] = json.loads(r[0].token_decimals)
                if r[0].token_nfts_parse_bytecode:
                    identity_snapshot['token']['nfts'] = {
                        'parse': {
                            'bytecode': json.loads(r[0].token_nfts_parse_bytecode)
                        }
                    }
            return {
                **identity_snapshot,
                '_meta': {
                    'registry_id': r[0].id,
                    'category': category,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                }
            }

    def get_nfts(self, category):
        """
        Returns the NftCategory
        """
        
        query = """
            SELECT 
                id, 
                category,
                authbase, 
                identity_history, 
                nft_category
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts') AS nft_category,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history
                ORDER BY id DESC
            ) AS subquery
            
            WHERE category = '"%s"' and identity_history <= '%s'
            ORDER BY identity_history DESC 
            LIMIT 1;
        """ % (category, datetime.datetime.utcnow().isoformat())
        r = Registry.objects.raw(query)
        if r:
            nft_category = r[0].nft_category
            if nft_category and type(nft_category) == str:
                nft_category = json.loads(nft_category)
            return {
                'nfts': nft_category,
                '_meta': {
                    'registry_id': r[0].id,
                    'category': r[0].category,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                }
            }
        
    def _paginator(self, count, limit, offset, url):
        if count == 0:
            return {
            'count': 0,
            'limit': limit,
            'offset': offset,
            'previous': None,
            'next': None
            }
        
        previous_offset = None
        next_offset = None
        if offset > 0: 
            previous_offset = offset - limit
            previous_offset = 0 if offset < 0 or previous_offset < limit else previous_offset
        if count > limit:
            next_offset = offset + limit
            next_offset = None if next_offset > count - 1 else next_offset
        previous = None
        if offset == 0 or offset > count:
            previous = None
        else:
            previous  = f'{url}?paginated=true&limit={limit}' if previous_offset == 0 or previous_offset == None else f'{url}?paginated=true&limit={limit}&offset={previous_offset}'
        _next = f'{url}?paginated=true&limit={limit}&offset={next_offset}' if next_offset else None
        return {
            'count': count,
            'limit': limit,
            'offset': offset,
            'previous': previous,
            'next': _next
        }

    
    def _get_nft_types_paginated(self, category, limit=10, offset=0, request_url=''):
        query = """
            SELECT
                id, 
                category,
                authbase, 
                identity_history, 
                nft_category,
                commitment,
                nft,
                results_count
            FROM (
                SELECT 
                id, 
                category,
                authbase, 
                identity_history, 
                nft_category,
                commitment,
                nft,
                COUNT(*) OVER() as results_count
                FROM (
                    SELECT DISTINCT ON(commitment)
                        id, 
                        category,
                        authbase, 
                        identity_history, 
                        nft_category,
                        commitment,
                        nft
                    FROM (
                        SELECT
                            id,
                            authbase,
                            identity_history,
                            commitment,
                            jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts') AS nft_category,
                            jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts','parse','types', commitment) AS nft,
                            jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                        FROM
                            bcmr_main_registry,
                            jsonb_object_keys(
                                CASE 
                                    WHEN jsonb_typeof(contents->'identities') = 'object' 
                                    THEN contents->'identities' 
                                    ELSE '{}'::jsonb 
                                END
                            ) AS authbase,
                            LATERAL jsonb_object_keys(
                                CASE 
                                    WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                                    THEN contents->'identities'->authbase 
                                    ELSE '{}'::jsonb 
                                END
                            ) AS identity_history,                    
                            LATERAL jsonb_object_keys(
                                CASE 
                                    WHEN jsonb_typeof(contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types') = 'object' 
                                    THEN contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types'
                                    ELSE '{}'::jsonb 
                                END
                            ) AS commitment                
                        WHERE identity_history <= '%s'
                        ORDER BY identity_history DESC
                        
                        
                    ) AS subquery
                    
                    WHERE category = '"%s"'
                    ORDER BY commitment DESC   
                )AS unique_commitments
                LIMIT %s OFFSET %s
            ) AS result;

            """ % (datetime.datetime.utcnow().isoformat(), category, limit, offset)
        r = Registry.objects.raw(query)
        paginated = {
            'limit': limit,
            'offset': offset,
            'previous': None,
            'next': None,
            'results': []
        }
        
        if r and r[0]:
            paginated['count'] = r[0].results_count
            paginated = { **paginated, **self._paginator(paginated['count'], limit, offset, request_url)}
            
        
        for item in r:
            nft_type = item.nft
            commitment = item.commitment.replace('"','')
            if nft_type and type(nft_type) == str:
                nft_type = json.loads(nft_type)
            paginated['results'].append({
                commitment: nft_type,
                '_meta': {
                    'registry_id': item.id,
                    'commitment': commitment,
                    'category': item.category.replace('"',''),
                    'authbase': item.authbase.replace('"',''),
                    'identity_history': item.identity_history.replace('"','')
                }
            })
        return paginated
    
    def _get_nft_types(self, category, limit=10, offset=0):
        """
        Returns the NftType(s) of the SequentialNftCollection or ParsableNftCollection
        """
        # TODO: handle if registry does not contain NftCategory or NftType(s)
        query = """
            SELECT DISTINCT ON(commitment)
                id, 
                category,
                authbase, 
                identity_history, 
                nft_category,
                commitment,
                nft
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    commitment,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts') AS nft_category,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts','parse','types', commitment) AS nft,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history,                    
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types') = 'object' 
                            THEN contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types'
                            ELSE '{}'::jsonb 
                        END
                    ) AS commitment                
                WHERE identity_history <= '%s'
                ORDER BY identity_history DESC
            ) AS subquery
            
            WHERE category = '"%s"'
            ORDER BY commitment DESC 
            LIMIT %s OFFSET %s;
        """ % (datetime.datetime.utcnow().isoformat(), category, limit, offset)

        r = Registry.objects.raw(query)
        nft_types = []
        for item in r:
            nft_type = item.nft
            commitment = item.commitment.replace('"','')
            if nft_type and type(nft_type) == str:
                nft_type = json.loads(nft_type)
            nft_types.append({
                commitment: nft_type,
                '_meta': {
                    'registry_id': item.id,
                    'commitment': commitment,
                    'category': item.category.replace('"',''),
                    'authbase': item.authbase.replace('"',''),
                    'identity_history': item.identity_history.replace('"','')
                }
            })
        return nft_types
    
    def get_nft_types(self, category, limit=10, offset=0, paginated=False, request_url=''):
        if paginated:
            return self._get_nft_types_paginated(category, limit, offset, request_url)
        return self._get_nft_types(category, limit, offset)

        
    
    def get_nft_type(self, category, commitment):
        """
        Returns the NftType(s) of the SequentialNftCollection or ParsableNftCollection
        """
        # TODO: handle if registry does not contain NftCategory or NftType(s)
        query = """
            SELECT
                id, 
                category,
                authbase, 
                identity_history, 
                commitment,
                nft
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    commitment,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'nfts','parse','types', commitment) AS nft,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history,                    
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types') = 'object' 
                            THEN contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types'
                            ELSE '{}'::jsonb 
                        END
                    ) AS commitment                
                WHERE commitment = '%s'
                ORDER BY id DESC
            ) AS subquery
            
            WHERE category = '"%s"' and identity_history <= '%s'
            ORDER BY identity_history DESC 
            LIMIT 1;
        """ % (commitment, category, datetime.datetime.utcnow().isoformat())

        r = Registry.objects.raw(query)
        if r:
            item = r[0]
            nft_type = item.nft
            commitment = item.commitment.replace('"','')
            if nft_type and type(nft_type) == str:
                nft_type = json.loads(nft_type)
            return {
                commitment: nft_type,
                '_meta': {
                    'registry_id': item.id,
                    'commitment': commitment,
                    'category': item.category.replace('"',''),
                    'authbase': item.authbase.replace('"',''),
                    'identity_history': item.identity_history.replace('"','')
                }
            }
    
    @staticmethod
    def find_registry_id(category):
        query = """
            SELECT 
                id, 
                authbase, 
                identity_history, 
                category
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities') = 'object' 
                            THEN contents->'identities' 
                            ELSE '{}'::jsonb 
                        END
                    ) AS authbase,
                    LATERAL jsonb_object_keys(
                        CASE 
                            WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                            THEN contents->'identities'->authbase 
                            ELSE '{}'::jsonb 
                        END
                    ) AS identity_history              
            ) AS subquery
            WHERE category = '"%s"' and identity_history <= '%s'
            ORDER BY id DESC 
            LIMIT 1;
        """ % (category, datetime.datetime.utcnow().isoformat())

        r = Registry.objects.raw(query)
        if r:
            return {
                'registry_id': r[0].id,
                '_meta': {
                    'category': r[0].category.replace('"',''),
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"','')
                }
            }

    @staticmethod
    def find_registry(category, include_identities=False):

        select_identities = "identities," if include_identities else ''

        extract_identities = """
        jsonb_extract_path(contents, 'identities') AS identities, 
        """ if include_identities else ''

        query = """
        SELECT 
            id, 
            identity_history,
            authbase,
            schema,
            version,
            latest_revision,
            registry_identity,
            tags,
            default_chain,
            chains,
            license,
            locales,
            extensions,
            %s
            category
        FROM (
            SELECT
                id,
                jsonb_extract_path(contents, '$schema') AS schema,
                jsonb_extract_path(contents, 'version') AS version,
                jsonb_extract_path(contents, 'latestRevision') AS latest_revision,
                jsonb_extract_path(contents, 'registryIdentity') AS registry_identity,
                jsonb_extract_path(contents, 'tags') AS tags,
                jsonb_extract_path(contents, 'defaultChain') AS default_chain,
                jsonb_extract_path(contents, 'chains') AS chains,
                jsonb_extract_path(contents, 'license') AS license,
                jsonb_extract_path(contents, 'locales') AS locales,
                jsonb_extract_path(contents, 'extensions') AS extensions,
                %s
                authbase,
                identity_history,
                jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
            FROM
                bcmr_main_registry,
                jsonb_object_keys(
                    CASE 
                        WHEN jsonb_typeof(contents->'identities') = 'object' 
                        THEN contents->'identities' 
                        ELSE '{}'::jsonb 
                    END
                ) AS authbase,
                LATERAL jsonb_object_keys(
                    CASE 
                        WHEN jsonb_typeof(contents->'identities'->authbase) = 'object' 
                        THEN contents->'identities'->authbase 
                        ELSE '{}'::jsonb 
                    END
                ) AS identity_history              
        ) AS subquery

        WHERE category = '"%s"' and identity_history <= '%s'
        ORDER BY id DESC 
        LIMIT 1;
        """ % (select_identities, extract_identities, category, datetime.datetime.utcnow().isoformat())

        registry = Registry.objects.raw(query)
        if registry:
            bcmr = {key: value for key,value in registry[0].__dict__.items() if key in ['schema', 'version', 'latest_revision', 'registry_identity','tags','default_chain', 'chains', 'license', 'locales', 'extensions', 'identities']}
            bcmr = {key: json.loads(value) for key, value in bcmr.items() if value}
            bcmr['$schema'] = bcmr.pop('schema')
            bcmr['latestRevision'] = bcmr.pop('latest_revision')
            bcmr['registryIdentity'] = bcmr.pop('registry_identity')
            if bcmr.get('default_chain'):
                bcmr['defaultChain'] = bcmr.pop('default_chain', None) 
            return {
                    **bcmr,       
                    '_meta': {
                        'registry_id': registry[0].id,
                        'category': registry[0].category.replace('"',''),
                        'authbase': registry[0].authbase.replace('"',''),
                        'identity_history': registry[0].identity_history.replace('"','')
                    }
                }
    

    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
        indexes = [
            GinIndex('contents', name='contents_idx'),
            models.Index(models.F("contents__identities"), name="contents__identities_idx"),
        ]
        unique_together = [
            'txid',
            'index',
            'publisher'
        ]
