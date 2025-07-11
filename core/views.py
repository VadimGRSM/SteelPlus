import os
import json
from decimal import Decimal
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
from django.core.serializers.json import DjangoJSONEncoder

from .models import Material, Drawing, Order, Detail, ProcessingType
from .forms import DrawingForm, SettingsDrawingForm
from .utils import (
    generate_preview_background,
    get_dxf_layers,
    generate_layer_previews,
    calculate_layer_cut_length,
    extract_entities,
    get_drawing_area_m2,
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

        generate_preview_background.delay(self.object.pk, self.object.file_path.path)

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
                validation_errors.append(
                    "Для шарів згинання необхідно налаштувати кути."
                )
            else:
                for i, angle in enumerate(angles_data):
                    point = angle.get("point", "").strip()
                    if (
                        not point
                        or point == "Обрати"
                        or "Клікніть на зображення" in point
                    ):
                        validation_errors.append(
                            f"Кут {i + 1}: не вибрано крапку на зображенні."
                        )

                    try:
                        degree = float(angle.get("degree", 0))
                        if degree < 0 or degree > 360:
                            validation_errors.append(
                                f"Кут {i + 1}: градус має бути від 0 до 360."
                            )
                    except (ValueError, TypeError):
                        validation_errors.append(
                            f"Кут {i + 1}: некоректне значення градуса."
                        )

                    radius = angle.get("radius", "").strip()
                    if not radius or radius == "Обрати":
                        validation_errors.append(
                            f"Кут {i + 1}: не заданий радіус згинання."
                        )

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
            f'<td><button type="button" class="action-button" onclick="openRadiusModal({i - 1})">Обрати</button></td></tr>'
        )
    bends_html = "".join(rows)
    return HttpResponse(bends_html)


def hub(request):
    return render(request, "core/hub.html")


def about(request):
    return render(request, "core/about.html")
@login_required
def order(request):
    user_orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("details", "details__drawing", "details__material")
        .order_by("-created_at")
    )
    detail_cost = {}
    for order_obj in user_orders:
        for detail in order_obj.details.all():
            detail_cost[detail] = detail.get_detail_cost()

    context = {
        "user_orders": user_orders,
        "detail_cost": detail_cost
    }

    return render(request, "core/order.html", context=context)




@login_required
def order_pay(request):
    return render(request, "orders/order_pay.html")


@login_required
def create_order(request):
    if request.method == "POST":
        total_forms = int(request.POST.get("form-TOTAL_FORMS", 0))

        details_to_create = []
        for i in range(total_forms):
            drawing_id = request.POST.get(f"form-{i}-drawing")
            quantity = request.POST.get(f"form-{i}-quantity")
            material_id = request.POST.get(f"form-{i}-material")
            thickness = request.POST.get(f"form-{i}-thickness")

            if any([drawing_id, quantity, material_id, thickness]):
                if not all([drawing_id, quantity, material_id, thickness]):
                    messages.error(
                        request, f"Будь ласка, заповніть усі поля для деталі №{i + 1}."
                    )
                    return redirect("core:create_order")

            if all([drawing_id, quantity, material_id, thickness]):
                details_to_create.append(
                    {
                        "drawing_id": drawing_id,
                        "quantity": int(quantity),
                        "material_id": material_id,
                        "thickness": Decimal(thickness),
                    }
                )

        if not details_to_create:
            messages.error(request, "Не додано жодної деталі для створення замовлення.")
            return redirect("core:create_order")

        order_cost = 0
        order = Order.objects.create(user=request.user)
        for detail_data in details_to_create:
            drawing = Drawing.objects.get(id=detail_data["drawing_id"])
            material = Material.objects.get(id=detail_data["material_id"])
            detail = Detail.objects.create(
                drawing=drawing,
                order=order,
                material=material,
                quantity=detail_data["quantity"],
                thickness=detail_data["thickness"],
                material_cost=0,
                cutting_cost=0,
                bending_cost=0,
            )
            detail.calculate_cost()
            detail.save()

            order_cost += (
                detail.material_cost + detail.cutting_cost + detail.bending_cost
            ) * detail_data["quantity"]
            order.total_cost = order_cost
            order.save()

        messages.success(request, "Замовлення успішн створено!")
        return redirect("core:order")

    materials = Material.objects.filter(available=True)
    materials_data = list(materials.values("id", "material_name", "material_type"))
    materials_json = json.dumps(materials_data, cls=DjangoJSONEncoder)

    context = {
        "drawings": Drawing.objects.filter(user=request.user, configured=True),
        "material_type": Material.MaterialTypeChoices.choices,
        "materials": materials,
        "materials_json": materials_json,
    }
    return render(request, "orders/create_order.html", context)


def detail_price(request):
    print("GET parameters:", request.GET)
    index = request.GET.get("index")
    if not index:
        for key in request.GET.keys():
            if key.startswith("form-") and key.endswith("-drawing"):
                index = key.split("-")[1]
                break

    if not index:
        return HttpResponse(
            "<div class='order-form-price-result'>Помилка: не знайдено індекс</div>"
        )

    drawing_id = request.GET.get(f"form-{index}-drawing")
    material_id = request.GET.get(f"form-{index}-material")
    thickness = request.GET.get(f"form-{index}-thickness")
    quantity = request.GET.get(f"form-{index}-quantity")

    if thickness:
        thickness = thickness.replace(",", ".")

    if not all([drawing_id, material_id, thickness, quantity]):
        return HttpResponse(
            f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>Заповніть всі поля для розрахунку</div>"
        )

    try:
        drawing = get_object_or_404(Drawing, id=drawing_id)
        material = get_object_or_404(Material, id=material_id)

        total_area_m2 = get_drawing_area_m2(drawing.file_path.path)
        thickness_m = Decimal(thickness) / 1000

        volume_m3 = total_area_m2 * thickness_m
        mass_kg = volume_m3 * material.density

        material_cost = mass_kg * material.price_per_kg

        cutting_type = drawing.processing_types.filter(name="Лазерне різання").first()
        if cutting_type:
            cutting_cost = cutting_type.base_cost_per_unit * Decimal(
                drawing.length_of_cuts
            )
        else:
            cutting_cost = Decimal(0)

        bending_type = drawing.processing_types.filter(name="Згинання").first()
        price_per_degree = Decimal("0.1")
        bending_cost = Decimal(0)
        if drawing.angles and bending_type:
            degrees = [
                int(angle.get("degree", 0))
                for angle in drawing.angles
                if angle.get("degree")
            ]
            for degree in degrees:
                if 0 < degree <= 180:
                    cost = bending_type.base_cost_per_unit + (price_per_degree * degree)
                    bending_cost += cost

        quantity = int(quantity)

        total_per_piece = material_cost + cutting_cost + bending_cost

        total = total_per_piece * quantity

        price_html = (
            f"<div>"
            f"  <div class='price-line'>Ціна за одну деталь: {total_per_piece:.2f} грн</div>"
            f"  <div class='price-line'>Загальна ціна: {total:.2f} грн</div>"
            f"</div>"
        )
        response_html = f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>{price_html}</div>"
        return HttpResponse(response_html)

    except Exception as e:
        return HttpResponse(
            f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>Помилка: {str(e)}</div>"
        )
