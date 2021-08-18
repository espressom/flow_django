from django.urls import path

from stock import views

urlpatterns = [
    path('company_code', views.company_code),
    path('getQuantChart', views.getQuantChart),
    path('load_stock_data', views.load_stock_data),
    path('like_cloud', views.like_cloud),
    path('make_chart', views.make_chart),
    path('make_treeMap', views.make_treeMap),
    path('make_company_asset_chart', views.make_company_asset_chart),
    path('make_sales_profit_chart', views.make_sales_profit_chart),
    path('predict_close', views.predict_close),
]
