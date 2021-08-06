from django.urls import path

from management import views

urlpatterns = [
    path('', views.management_index),
    path('login', views.management_login),
    path('forgot_password', views.management_forgot_password),
    path('404', views.management_404),

    # ------------- dump
    path('button', views.dump_button),
    path('card', views.dump_card),
]
