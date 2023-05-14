from bcmr_main.models import *
from bcmr_main.forms import *

from django.shortcuts import render
from django.utils import timezone


def create_ft(request):
    submitted = False
    message = ''

    if request.method == 'POST':
        queryDict = request.POST
        data = dict(queryDict.lists())

        category = data['category'][0]
        name = data['name'][0]
        description = data['description'][0]
        symbol = data['symbol'][0]
        decimals = int(data['decimals'][0])
        icon = data['icon'][0]
        
        if Token.objects.filter(category=category).exists():
            message = 'Fungible Token category already exists!'
        else:
            now = timezone.now()
            token = Token(
                category=category,
                name=name,
                description=description,
                symbol=symbol,
                decimals=decimals,
                icon=icon,
                updated_at=now
            )
            token.save()

            registry_data = {
                'token': token,
                'latest_revision': now,
                'registry_identity': {
                    'name': f'{name}\'s Registry',
                    'description': f'{name}\'s CashToken Metadata'
                },
                'version': {
                    'major': 0,
                    'minor': 1,
                    'patch': 0
                }
            }
            Registry(**registry_data).save()
            message = 'Fungible Token added!'

        submitted = True

    context = {
        'form': FungibleTokenForm(),
        'submitted': submitted,
        'message': message
    }
    return render(request, 'bcmr_main/create_ft.html', context)
