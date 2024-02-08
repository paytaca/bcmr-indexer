# from django.db import models
# from bcmr.models import TimeStampedModel
# from bcmr_main.models import Registry


# class NftParsingInformation:

#   category = models.CharField(max_length=64, unique=True)
#   bytecode = models.CharField(default=None, max_length=255, null=True, blank=True)
#   registry = models.ForeignKey(Registry, on_delete=models.CASCADE)

#   @property
#   def nft_collection_type(self):
#     if self.bytecode:
#       return 'ParsableNftCollection'
#     return 'SequentialNftCollection'
