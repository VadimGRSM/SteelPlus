from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.hub, name='hub'),
    path('about/', views.about, name='about'),
    path('drawing/', views.drawing, name='drawing'),
    path('order/', views.order, name='order'),
    path('orders/create-order', views.create_order, name='create_order'),
    path('drawings/upload-drawing', views.upload_drawing, name='upload_drawing'),
    path('drawings/view-drawing', views.view_drawing, name='view_drawing'),
]
