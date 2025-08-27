from rest_framework import routers

from bcmr_main import views

from django.urls import path, re_path


app_name = "bcmr_main"

router = routers.DefaultRouter()

# router.register("tokens", views.TokenViewSet)


urlpatterns = router.urls
urlpatterns += [
    re_path(r"^status/latest-block/$", views.LatestBlockView.as_view(), name='latest-block-info'),
    re_path(r"^tokens/(?P<category>[\w+:]+)/icon-symbol$", views.TokenIconSymbolView.as_view(), name='token-icon-symbol-info'),
    re_path(r"^tokens/(?P<category>[\w+:]+)/$", views.TokenView.as_view(), name='token-info'),
    re_path(r"^tokens/(?P<category>[\w+:]+)/(?P<type_key>[\w+:]+)/$", views.TokenView.as_view(), name='token-type-info'),
    re_path(r"^registries/(?P<category>[\w+:]+)/latest/$", views.RegistryView.as_view(), name='latest-token-registry'),
    re_path(r"^registries/(?P<txid>\w{64})\:(?P<vout>\d+)/$", views.RegistryTxoView.as_view(), name='token-registry'),
    re_path(r"^authchain/(?P<category>[\w+:]+)/head/$", views.AuthchainHeadView.as_view(), name='authchain-head'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/$", views.get_contents, name='bcmr-get-contents'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/token/$", views.get_token, name='bcmr-get-token'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/token/nfts/(?P<commitment>[\w+:]+)/$", views.get_token_nft, name='bcmr-get-token-nft'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/uris/$", views.get_uris, name='bcmr-get-uris'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/uris/icon$", views.get_icon_uri, name='bcmr-get-icon-uri'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/uris/published-url$", views.get_published_url, name='bcmr-get-published-uri'),
    re_path(r"^bcmr/(?P<category>[\w+:]+)/reindex/$", views.reindex_token, name='reindex-token-registry')
]
