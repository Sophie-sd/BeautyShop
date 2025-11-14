from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='create'),
    path('success/', views.order_success, name='success'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('np/search-cities/', views.np_search_cities, name='np_search_cities'),
    path('np/get-warehouses/', views.np_get_warehouses, name='np_get_warehouses'),
    path('liqpay-pending/', views.liqpay_payment_pending, name='liqpay_payment_pending'),
    path('liqpay-return/', views.liqpay_return, name='liqpay_return'),
    path('liqpay/<int:order_id>/', views.liqpay_payment, name='liqpay_payment'),
    path('liqpay-callback/', views.liqpay_callback, name='liqpay_callback'),
]
