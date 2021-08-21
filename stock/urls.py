from django.urls import path

from stock import views

urlpatterns = [
    path('company_code', views.company_code),
    path('getQuantChart', views.getQuantChart),
    path('load_stock_data', views.load_stock_data),
    path('like_cloud', views.like_cloud),
    path('make_chart', views.make_chart),
    path('make_treeMap', views.make_treeMap),
    path('similar', views.similar),
    path('make_company_asset_chart', views.make_company_asset_chart),
    path('make_sales_profit_chart', views.make_sales_profit_chart),
    path('makeCountryStockIndex',views.makeCountryStockIndex),
    path('predict_close', views.predict_close),
    path('get_company_figure', views.get_company_figure),
    path('myPortfolio',views.myPortfolioChart),
    path('effPortfolio',views.effPortfolio),
]
