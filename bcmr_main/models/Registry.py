import json
from django.db import models
from django.db.models import ExpressionWrapper, CharField, F, Q

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

    def get_identities(self) -> [str]:

        query = f"""
            SELECT id, 
            jsonb_object_keys(contents->'identities') AS authbase 
            FROM bcmr_main_registry WHERE id=%s;""" % self.id
        
        return [i.authbase for i in Registry.objects.raw(query)]

    def get_identity_history(self, authbase:str = None):
        """
        Returns history of specific authbase, or all identities if authbase (authbase) isn't provided.
        """
        if authbase: 
            return {
                authbase: [i.timestamp for i in Registry.objects.raw("SELECT id, jsonb_object_keys(contents->'identities'->'%s') AS timestamp from bcmr_main_registry WHERE id=%s;" % (authbase, self.id))]
            }
        
        histories = {}
    
        for authbase in self.identities():
            histories[authbase] = [i.timestamp for i in Registry.objects.raw("SELECT id, jsonb_object_keys(contents->'identities'->'%s') AS timestamp from bcmr_main_registry WHERE id=%s;" % (authbase, self.id))]
    
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
                'meta': {
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
        query = f"""
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
                    jsonb_object_keys(contents -> 'identities') AS authbase,
                LATERAL jsonb_object_keys(contents->'identities'->authbase) AS identity_history
            ) AS subquery
            
            WHERE category = '"{category}"'
            ORDER BY id DESC LIMIT 1;
        """
        r = Registry.objects.raw(query)
        if r:
            return {
                'token': {
                    'symbol': r[0].symbol.replace('"',''),
                    'decimals': r[0].decimals,
                    'category': r[0].category.replace('"',''),
                },
                'meta': {
                    'registry_id': r[0].id,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                }
            }

    def get_identity_snapshot(self, category):
        """
        Return the basic TokenCategory details
        """
        # jsonb_object_keys(contents->'identities') AS identities,
        query = f"""
            SELECT 
                id, 
                authbase, 
                identity_history, 
                identity_snapshot
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history) AS identity_snapshot,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(contents -> 'identities') AS authbase,
                LATERAL jsonb_object_keys(contents->'identities'->authbase) AS identity_history
            ) AS subquery
            
            WHERE category = '"{category}"'
            ORDER BY id DESC LIMIT 1;
        """
        r = Registry.objects.raw(query)
        if r:
            identity_snapshot = r[0].identity_snapshot
            if identity_snapshot:
                identity_snapshot = json.loads(identity_snapshot)
            return {
                'identity_snapshot': identity_snapshot,
                'meta': {
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
        
        query = f"""
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
                    jsonb_object_keys(contents -> 'identities') AS authbase,
                    LATERAL jsonb_object_keys(contents->'identities'->authbase) AS identity_history
            ) AS subquery
            
            WHERE category = '"{category}"'
            ORDER BY id DESC LIMIT 1;
        """
        r = Registry.objects.raw(query)
        if r:
            nft_category = r[0].nft_category
            if nft_category and type(nft_category) == str:
                nft_category = json.loads(nft_category)
            return {
                'nfts': nft_category,
                'meta': {
                    'registry_id': r[0].id,
                    'category': r[0].category,
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                }
            }
        
    
    def get_nft_types(self, category, limit=10, offset=0):
        """
        Returns the NftType(s) of the SequentialNftCollection or ParsableNftCollection
        """
        # TODO: handle if registry does not contain NftCategory or NftType(s)
        query = f"""
            SELECT 
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
                    jsonb_object_keys(contents -> 'identities') AS authbase,
                    LATERAL jsonb_object_keys(contents->'identities'->authbase) AS identity_history,
                    LATERAL jsonb_object_keys(contents->'identities'->authbase->identity_history->'token'->'nfts'->'parse'->'types') AS commitment
            ) AS subquery
            
            WHERE category = '"{category}"'
            ORDER BY id DESC LIMIT {limit} OFFSET {offset};
        """ 
        r = Registry.objects.raw(query)
        nft_types = []
        for item in r:
            nft_type = item.nft
            commitment = item.commitment.replace('"','')
            if nft_type and type(nft_type) == str:
                nft_type = json.loads(nft_type)
            nft_types.append({
                commitment: nft_type,
                'meta': {
                    'registry_id': item.id,
                    'commitment': commitment,
                    'category': item.category.replace('"',''),
                    'authbase': item.authbase.replace('"',''),
                    'identity_history': item.identity_history.replace('"','')
                }
            })
        return nft_types    
        

    @staticmethod
    def find_registry_by_token_category(category):
        query = f"""
            SELECT 
                id, 
                authbase, 
                identity_history, 
                identities, 
                category
            FROM (
                SELECT
                    id,
                    authbase,
                    identity_history,
                    jsonb_object_keys(contents->'identities') AS identities,
                    jsonb_extract_path(contents, 'identities', authbase, identity_history, 'token', 'category') AS category
                FROM
                    bcmr_main_registry,
                    jsonb_object_keys(contents -> 'identities') AS authbase,
                LATERAL jsonb_object_keys(contents->'identities'->authbase) AS identity_history
            ) AS subquery
            
            WHERE category = '"{category}"'
            ORDER BY id DESC LIMIT 1;
        """

        r = Registry.objects.raw(query)
        if r:
            return {
                'registry_id': r[0].id,
                'meta': {
                    'category': r[0].category.replace('"',''),
                    'authbase': r[0].authbase.replace('"',''),
                    'identity_history': r[0].identity_history.replace('"',''),
                    'identities': r[0].identities
                }
            }


            


    class Meta:
        verbose_name_plural = 'Registries'
        ordering = ('-date_created', )
        # indexes = [
        #     models.Index(fields=[
        #         'txid',
        #         'index',
        #         'valid',
        #         'date_created',
        #         'generated_metadata'
        #     ])
        # ]
        unique_together = [
            'txid',
            'index',
            'publisher'
        ]
