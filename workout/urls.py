from django.urls import path

from . import views

app_name = 'workout'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('workout/', views.Current.as_view(), name='current'),
    path('workout/<int:year>/<int:month>/<int:day>/', views.Archive.as_view(), name='worksheet'),
    path('workout/<int:worksheet_id>/close', views.Close.as_view(), name='close'),
]
