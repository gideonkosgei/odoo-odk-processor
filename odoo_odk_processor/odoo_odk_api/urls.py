# pages/urls.py
from django.urls import path
from .views import WelcomeApiView, OdooApiView

urlpatterns = [
    path("", WelcomeApiView.as_view()),
    path('odk', OdooApiView.as_view()),

]

