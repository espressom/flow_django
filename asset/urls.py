from django.urls import path

from asset import views

urlpatterns = [
    path('addcashflow',views.addcashflow),
    path('category_chart',views.category_chart),
    path('month_cash_chart',views.month_cash_chart),
    path('baseRate',views.baseRate_jsonp),
    path('load_category_data',views.load_category_data),
]