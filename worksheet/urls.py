from django.urls import path

from . import views

app_name = 'worksheet'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('worksheet/', views.CreateView.as_view(), name='create'),
    path('worksheet/<int:year>/<int:month>/<int:day>/', views.WorksheetView.as_view(), name='worksheet'),
    path('worksheet/<int:worksheet_id>/close', views.CloseAction.as_view(), name='close'),
    path('worksheet/<int:worksheet_id>/result/<int:result_id>/<str:field>', views.ResultAction.as_view(), name='result'),
]
