import os

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.conf import settings
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage

from .models import Material, Drawing, Order, Detail
from .forms import DrawingForm
from .utils import generate_dxf_preview, get_drawing_sizes


def hub(request):
    return render(request, "core/hub.html")


def about(request):
    return render(request, "core/about.html")


@login_required
def drawing(request):
    user_drawings = request.user.drawings.all().order_by("-uploaded_at")
    context = {"drawings": user_drawings}
    return render(request, "core/drawing.html", context)


@login_required
def delete_drawing(request, pk):
    drawing = get_object_or_404(Drawing, pk=pk, user=request.user)
    drawing.file_path.delete(save=False)
    drawing.delete()
    return redirect("core:drawing")


@login_required
def order(request):
    return render(request, "core/order.html")


@login_required
def create_order(request):
    return render(request, "orders/create_order.html")


class UploadDrawing(LoginRequiredMixin, CreateView):
    form_class = DrawingForm
    template_name = "drawings/upload_drawing.html"
    success_url = reverse_lazy("core:drawing")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@login_required
def view_drawing(request, pk):
    drawing = get_object_or_404(Drawing, pk=pk, user=request.user)

    svg_url = None
    if drawing.file_path.name.endswith(".dxf"):
        preview = generate_dxf_preview(drawing.file_path.path)
        if preview:
            temp_path = f"tmp_previews/{preview.name}"
            saved_path = default_storage.save(temp_path, preview)
            svg_url = default_storage.url(saved_path)

    sizes = get_drawing_sizes(drawing.file_path.path)

    context = {
        "drawing": drawing,
        "sizes": sizes,
        "img": svg_url,
    }

    return render(request, "drawings/view_drawing.html", context)
