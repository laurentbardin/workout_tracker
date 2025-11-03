from django.urls import path

from . import views

app_name = 'workout'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('workout/', views.CreateView.as_view(), name='create'),
    path('workout/<int:year>/<int:month>/<int:day>/', views.WorkoutView.as_view(), name='workout'),
    path('workout/<int:worksheet_id>/close', views.CloseAction.as_view(), name='close'),
]
