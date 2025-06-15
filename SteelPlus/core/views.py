from django.shortcuts import render, get_object_or_404
from .models import Material, Drawing, Order, Detail


def hub(request):
    return render(request, 'core/hub.html')


def about(request):
    return render(request, 'core/about.html')


def drawing(request):
    return render(request, 'core/drawing.html')


def order(request):
    return render(request, 'core/order.html')