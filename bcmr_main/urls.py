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
    re_path(r"^authchain/(?P<category>[\w+:]+)/head/$", views.AuthchainHeadView.as_view(), name='authchain-head'),
]
