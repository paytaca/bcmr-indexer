# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from bcmr_main.models import IdentityOutput, Registry


# @receiver(post_save, sender=IdentityOutput)
# def update_identities_and_registries(sender, instance=None, created=False, **kwargs):
#     print('----obj:', instance)
#     identities = instance.get_identities()
#     print('----check:', identities)
#     for identity in identities:
#         identity_obj = IdentityOutput.objects.get(txid=identity)
#         instance.identities.add(identity_obj)

#     for identity in instance.identities.all():
#         print('--IDENTITY:', identity.txid)
