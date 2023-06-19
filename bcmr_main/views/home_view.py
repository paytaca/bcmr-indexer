from django.shortcuts import render
from bcmr_main.models import *


def home_page(request):
    categories = Token.objects.all().order_by('category').distinct('category')
    tokens = Token.objects.all()
    token_metadata = TokenMetadata.objects.all().order_by('token_id').distinct('token_id')
    context = {
        'categories': categories.count(),
        'tokens': tokens.count(),
        'valid_tokens': token_metadata.count()
    }
    return render(request, 'bcmr_main/home.html', context)
