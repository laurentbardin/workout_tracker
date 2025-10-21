from django.urls import path

from . import views

app_name = 'workout'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('workout/', views.Current.as_view(), name='current'),
    path('worksheet/<int:year>/<int:month>/<int:day>/', views.Archive.as_view(), name='archive'),
]
