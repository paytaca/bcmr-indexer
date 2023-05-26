from rest_framework import routers

from bcmr_main import views

from django.urls import path, re_path


app_name = "bcmr_main"

router = routers.DefaultRouter()

# router.register("tokens", views.TokenViewSet)


urlpatterns = router.urls
urlpatterns += [
#     path('create_ft/', views.create_ft),
    re_path(r"^tokens/(?P<category>[\w+:]+)/$", views.TokenView.as_view(), name='token-info'),
    re_path(r"^registries/(?P<category>[\w+:]+)/latest/$", views.RegistryView.as_view(), name='latest-token-registry'),
]
