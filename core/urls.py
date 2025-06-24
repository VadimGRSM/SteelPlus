from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.hub, name="hub"),
    path("about/", views.about, name="about"),

    path("drawing/", views.drawing, name="drawing"),
    path("drawing/delete/<int:pk>/", views.delete_drawing, name="delete_drawing"),
    path("drawing/upload-drawing/", views.UploadDrawing.as_view(), name="upload_drawing"),
    path("drawing/view-drawing/<int:pk>/", views.view_drawing, name="view_drawing"),

    path("order/", views.order, name="order"),
    path("orders/create-order/", views.create_order, name="create_order"),

    path('orders/pay-order/', views.order_pay, name='order_pay'),
]
