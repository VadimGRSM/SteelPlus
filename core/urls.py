from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.hub, name="hub"),
    path("about/", views.about, name="about"),
    path("order/", views.order, name="order"),
    path("orders/create-order/", views.create_order, name="create_order"),
    path("orders/pay-order/", views.order_pay, name="order_pay"),
    path("drawing/", views.drawing, name="drawing"),
    path("drawing/delete/<int:pk>/", views.delete_drawing, name="delete_drawing"),
    path(
        "drawing/upload-drawing/", views.UploadDrawing.as_view(), name="upload_drawing"
    ),
    path("drawing/view-drawing/<int:pk>/", views.view_drawing, name="view_drawing"),
    path(
        "drawing/settings/<int:pk>/",
        views.SettingsDrawing.as_view(),
        name="settings_drawing",
    ),
    # htmx
    path("drawing/cutting-length", views.cutting_length, name="cutting_length"),
    path("drawing/bends_setting", views.bends_setting, name="bends_setting"),
]
