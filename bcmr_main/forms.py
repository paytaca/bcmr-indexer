from django import forms

from bcmr_main.models import Token


class FungibleTokenForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = (
            'category',
            'name',
            'symbol',
            'decimals',
            'icon',
            'description',
        )
