import os
import json
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage

from .models import Material, Drawing, Order, Detail, ProcessingType
from .forms import DrawingForm, SettingsDrawingForm
from .utils import (
    generate_preview_background,
    get_dxf_layers,
    generate_layer_previews,
    calculate_layer_cut_length,
    extract_entities,
)

from django.shortcuts import render, HttpResponseRedirect


@login_required
def drawing(request):
    user_drawings = request.user.drawings.all().order_by("-uploaded_at")
    context = {"drawings": user_drawings}
    return render(request, "core/drawing.html", context)


@login_required
def delete_drawing(request, pk):
    drawing = get_object_or_404(Drawing, pk=pk, user=request.user)

    preview_filename = f"previews/preview_{drawing.pk}.png"
    if default_storage.exists(preview_filename):
        default_storage.delete(preview_filename)

    layers = get_dxf_layers(drawing.file_path.path)

    for layer in layers:
        preview_filename = f"previews/layer_{drawing.pk}_{layer}.png"
        if default_storage.exists(preview_filename):
            default_storage.delete(preview_filename)

    if drawing.file_path:
        drawing.file_path.delete(save=False)

    drawing.delete()
    return redirect("core:drawing")


class UploadDrawing(LoginRequiredMixin, CreateView):
    form_class = DrawingForm
    template_name = "drawings/upload_drawing.html"
    success_url = reverse_lazy("core:drawing")

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        processes_str = self.request.POST.get("processes", "")
        if not processes_str:
            form.add_error(None, "Потрібно вибрати хоча б один процес.")
            return self.form_invalid(form)
        if processes_str:
            process_ids = [
                int(pid) for pid in processes_str.split(",") if pid.isdigit()
            ]
            form.instance.processing_types.set(process_ids)
        else:
            form.instance.processing_types.clear()

        generate_preview_background.delay(drawing_id=self.object.pk)

        generate_layer_previews.delay(
            dxf_path=self.object.file_path.path, drawing_id=self.object.pk
        )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["process_types"] = ProcessingType.objects.all().order_by(
            "-is_active", "name"
        )
        return context


@login_required
def view_drawing(request, pk):
    drawing = get_object_or_404(Drawing, pk=pk)

    img = None
    preview_filename = f"previews/preview_{drawing.pk}.png"
    if default_storage.exists(preview_filename):
        img = default_storage.url(preview_filename)

    return render(
        request,
        "drawings/view_drawing.html",
        {
            "drawing": drawing,
            "img": img,
        },
    )


class SettingsDrawing(LoginRequiredMixin, UpdateView):
    model = Drawing
    form_class = SettingsDrawingForm
    template_name = "drawings/settings_drawing.html"

    def get_success_url(self):
        return reverse_lazy("core:settings_drawing", kwargs={"pk": self.object.pk})

    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk")
        drawing, created = Drawing.objects.get_or_create(pk=pk)
        if not drawing.layers:
            drawing.layers = get_dxf_layers(drawing.file_path.path)
            drawing.save()
        return drawing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previews = []
        for layer in self.object.layers:
            preview_filename = f"previews/layer_{self.object.pk}_{layer}.png"
            if default_storage.exists(preview_filename):
                previews.append((layer, default_storage.url(preview_filename)))

        context["layer_previews"] = previews
        context["saved_cutting_layers"] = self.object.cutting_layers or []
        context["saved_bending_layers"] = self.object.bending_layers or []
        context["saved_angles"] = self.object.angles or []
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        return kwargs

    def form_valid(self, form):
        cutting_layers = self.request.POST.getlist("cutting")
        bending_layers = self.request.POST.getlist("bending")

        validation_errors = []

        overlapping_layers = set(cutting_layers) & set(bending_layers)
        if overlapping_layers:
            validation_errors.append(
                f"Шари не можуть використовуватися одночасно для різання та згинання: {', '.join(overlapping_layers)}"
            )

        if bending_layers:
            angles_data = form.cleaned_data.get("angles", [])
            if not angles_data:
                validation_errors.append("Для шарів згинання необхідно налаштувати кути.")
            else:
                for i, angle in enumerate(angles_data):
                    point = angle.get("point", "").strip()
                    if (
                        not point
                        or point == "Обрати"
                        or "Клікніть на зображення" in point
                    ):
                        validation_errors.append(
                            f"Кут {i+1}: не вибрано крапку на зображенні."
                        )

                    try:
                        degree = float(angle.get("degree", 0))
                        if degree < 0 or degree > 360:
                            validation_errors.append(
                                f"Кут {i+1}: градус має бути від 0 до 360."
                            )
                    except (ValueError, TypeError):
                        validation_errors.append(
                            f"Кут {i+1}: некоректне значення градуса."
                        )

                    radius = angle.get("radius", "").strip()
                    if not radius or radius == "Обрати":
                        validation_errors.append(f"Кут {i+1}: не заданий радіус згинання.")

        if validation_errors:
            for error in validation_errors:
                messages.error(self.request, error)
            return self.form_invalid(form)

        self.object.cutting_layers = cutting_layers
        self.object.bending_layers = bending_layers
        self.object.description = form.cleaned_data["description"]
        self.object.length_of_cuts = form.cleaned_data["length_of_cuts"]

        angles_str = form.cleaned_data["angles"]
        if angles_str:
            if isinstance(angles_str, str):
                self.object.angles = json.loads(angles_str)
            else:
                self.object.angles = angles_str
        else:
            self.object.angles = []

        self.object.configured = True
        self.object.save()

        messages.success(self.request, "Налаштування креслення успішно збережено!")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

        return super().form_invalid(form)


def cutting_length(request):
    drawing = get_object_or_404(Drawing, id=request.GET.get("drawing_id"))
    selected = request.GET.getlist("cutting")

    length = 0
    for layer in selected:
        length += calculate_layer_cut_length(drawing.file_path.path, layer)
    text = "<div class='info-label'>Довжина різу " + str(round(length, 3)) + " mm</div>"
    return HttpResponse(text)


def bends_setting(request):
    drawing = get_object_or_404(Drawing, id=request.GET.get("drawing_id"))
    selected = request.GET.getlist("bending")

    if not selected:
        return HttpResponse(
            '<tr><td colspan="4" style="text-align: center;">Оберіть шари для подальшого налаштування!</td></tr>'
        )

    num_bends = 0
    for layer in selected:
        entities = extract_entities(drawing.file_path.path, layer)
        for entity in entities:
            if entity.dxftype() == "LINE":
                num_bends += 1

    rows = []
    for i in range(1, num_bends + 1):
        rows.append(
            f"<tr><td><button type='button' class='pick-point-btn'>Обрати</button></td>"
            f'<td><input type="text" class="corner-input" value="90"></td>'
            f'<td><input type="checkbox" checked class="corner-checkbox"></td>'
            f'<td><button type="button" class="action-button" onclick="openRadiusModal({i-1})">Обрати</button></td></tr>'
        )
    bends_html = "".join(rows)
    return HttpResponse(bends_html)


def hub(request):
    return render(request, "core/hub.html")


def about(request):
    return render(request, "core/about.html")


@login_required
def order(request):
    return render(request, "core/order.html")


@login_required
def order_pay(request):
    return render(request, "orders/order_pay.html")


@login_required
def create_order(request):
    return render(request, "orders/create_order.html")
