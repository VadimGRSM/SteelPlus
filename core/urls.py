from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.hub, name='hub'),
    path('about/', views.about, name='about'),
    path('drawing/', views.drawing, name='drawing'),
    path('order/', views.order, name='order'),
]
