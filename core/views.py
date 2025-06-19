from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Material, Drawing, Order, Detail


def hub(request):
    return render(request, 'core/hub.html')


def about(request):
    return render(request, 'core/about.html')


@login_required
def drawing(request):
    return render(request, 'core/drawing.html')


@login_required
def order(request):
    return render(request, 'core/order.html')

@login_required
def create_order(request):
    return render(request, 'orders/create_order.html')

@login_required
def upload_drawing(request):
    return render(request, 'drawings/upload_drawing.html')

@login_required
def view_drawing(request):
    return render(request, 'drawings/view_drawing.html')