from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="interview/"), name="index"),
    path("interview/", include("interview.urls")),
    path("admission/", include("admission.urls")),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("api/", include("interview.api_urls")),
]
