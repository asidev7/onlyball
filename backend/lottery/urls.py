from django.urls import path

from . import views

urlpatterns = [
    path("accounts/register", views.register_account),
    path("accounts/<str:address>", views.account_detail),
    path("rounds/current", views.current_round),
    path("tickets", views.tickets_list),
    path("tickets/buy", views.buy_ticket),
    path("results", views.results),
    path("affiliate/<str:address>", views.affiliate),
    path("holders", views.holders),
]
