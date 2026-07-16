from django.urls import path

from . import api_views

urlpatterns = [
    path('next-draw/', api_views.next_draw, name='api_next_draw'),
    path('me/tickets/', api_views.me_tickets, name='api_me_tickets'),
    path('wallet/nonce/', api_views.wallet_nonce, name='api_wallet_nonce'),
    path('wallet/verify/', api_views.wallet_verify, name='api_wallet_verify'),
    path('draws/<int:pk>/', api_views.draw_detail, name='api_draw_detail'),
    path('deposits/<int:pk>/status/', api_views.deposit_status, name='api_deposit_status'),
    path('webhooks/nowpayments/', api_views.nowpayments_webhook, name='api_nowpayments_webhook'),
]
