from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),

    path('deposit/', views.deposit_view, name='deposit'),
    path('buy/', views.buy_view, name='buy'),
    path('account/', views.account_view, name='account'),
    path('account/self-exclude/', views.self_exclude_view, name='self_exclude'),
    path('account/deposit-cap/', views.set_deposit_cap_view, name='set_deposit_cap'),
    path('account/payout-address/', views.set_payout_address_view, name='set_payout_address'),
    path('withdraw/', views.withdraw_view, name='withdraw'),

    path('draws/', views.draws_list_view, name='draws'),
    path('draws/<int:pk>/', views.draw_detail_view, name='draw_detail'),
    path('fair/', views.fair_view, name='fair'),
    path('legal/', views.legal_view, name='legal'),
]
