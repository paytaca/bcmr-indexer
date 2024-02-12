from celery import shared_task

@shared_task()
def set_category_nfttype_cache(category, nfttype):
  # cache the nft type
  pass 

@shared_task()
def set_category_nfttypes_cache(category, nfttype, page=1):
  # cache the nfttypes page
  pass 