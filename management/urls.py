from django.urls import path

from management import views

urlpatterns = [
    path('', views.management_index),
    path('adminLogin', views.adminLogin),
    path('forgot_password', views.management_forgot_password),
    path('404', views.management_404),
    path('reqFig', views.reqFig),
    path('dateFig', views.dateFig),
    path('adminLogout',views.adminLogout),
    path('memberInfo',views.management_memberInfo),
    path('getMemAgesCountChart',views.getMemAgesCountChart),
    path('getMemGenCountChart',views.getMemGenCountChart),
    path('memberManage',views.management_member),
    path('memberBoard',views.management_board),
    path('delMember',views.delMember),

    # ------------- dump
    path('button', views.dump_button),
    path('card', views.dump_card),
]
