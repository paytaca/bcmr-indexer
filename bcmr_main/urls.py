from rest_framework import routers

from bcmr_main import views

from django.urls import path, re_path


app_name = "bcmr_main"

router = routers.DefaultRouter()

router.register("tokens", views.TokenViewSet)


urlpatterns = router.urls
urlpatterns += [
    path('create_ft/', views.create_ft),
    re_path(r"^registries/(?P<token_id>[\w+:]+)/latest/$", views.RegistryView.as_view(), name='latest-token-registry'),
]
