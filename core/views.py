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
    get_bounding_box_area_m2,
)

from django.shortcuts import render, HttpResponseRedirect


@login_required
def drawing(request):
    user_drawings = request.user.drawings.all().order_by("-uploaded_at")
    for drawing in user_drawings:
        preview_filename = f"previews/preview_{drawing.pk}.png"
        if default_storage.exists(preview_filename):
            drawing.preview_url = default_storage.url(preview_filename)
        else:
            drawing.preview_url = None
    context = {"drawings": user_drawings}
    return render(request, "core/drawing.html", context)


@login_required
def delete_drawing(request, pk):
    drawing = get_object_or_404(Drawing, pk=pk, user=request.user)

    if drawing.details.exists():
        messages.error(request, "Неможливо видалити креслення, оскільки воно використовується в замовленнях.")
        return redirect("core:drawing")

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
        generate_preview_background.delay(self.object.pk, self.object.file_path.path)
        generate_layer_previews.delay(
            dxf_path=self.object.file_path.path, drawing_id=self.object.pk
        )

        return response


@login_required
def view_drawing(request, pk):
    drawing = get_object_or_404(Drawing, pk=pk, user=request.user)

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
        return reverse_lazy("core:drawing")

    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk")
        drawing, created = Drawing.objects.get_or_create(pk=pk, user=self.request.user)
        if not drawing.layers:
            drawing.layers = get_dxf_layers(drawing.file_path.path)
            drawing.save()
        return drawing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previews = []
        if self.object.layers:
            for layer in self.object.layers:
                preview_filename = f"previews/layer_{self.object.pk}_{layer}.png"
                if default_storage.exists(preview_filename):
                    previews.append((layer, default_storage.url(preview_filename)))

        context["layer_previews"] = previews
        context["all_processing_types"] = ProcessingType.objects.order_by('id') 
        context["process_settings"] = self.object.process_settings or {}
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        return kwargs

    def form_valid(self, form):
        process_settings = {}
        for pt in ProcessingType.objects.all():
            pid = str(pt.id)
            if pid in self.request.POST.getlist('processing_types'):
                if pt.id == 1:
                    process_settings[pid] = {
                        "type": "cutting",
                        "layers": self.request.POST.getlist("cutting"),
                        "length_of_cuts": self.request.POST.get("length_of_cuts"),
                    }
                elif pt.id == 2:
                    angles = self.request.POST.get("angles_2")
                    try:
                        angles = json.loads(angles) if angles else []
                    except Exception:
                        angles = []
                    process_settings[pid] = {
                        "type": "bending",
                        "layers": self.request.POST.getlist("bending"),
                        "angles": angles,
                    }
        self.object.process_settings = process_settings
        self.object.description = form.cleaned_data["description"]
        self.object.configured = True
        self.object.save()
        messages.success(self.request, f"Налаштування креслення {self.object.name} успішно збережено!")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


@login_required
def cutting_length(request):
    drawing_id = request.GET.get("drawing_id")
    if not drawing_id:
        return HttpResponse("<div class='info-label'>Помилка: не вказано ID чертежа</div>")
    
    drawing = get_object_or_404(Drawing, id=drawing_id, user=request.user)
    selected = request.GET.getlist("cutting")

    if not selected:
        return HttpResponse("<div class='info-label'>Оберіть шари для розрахунку</div>")

    length = 0
    for layer in selected:
        length += calculate_layer_cut_length(drawing.file_path.path, layer)
    
    text = f"<div class='info-label'>Довжина різу {round(length, 3)} mm</div>"
    return HttpResponse(text)


@login_required
def bends_setting(request):
    drawing_id = request.GET.get("drawing_id")
    if not drawing_id:
        return HttpResponse(
            '<tr><td colspan="4" style="text-align: center;">Помилка: не вказано ID чертежа</td></tr>'
        )
    
    drawing = get_object_or_404(Drawing, id=drawing_id, user=request.user)
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

            if drawing_id or quantity or material_id or thickness:
                if not all([drawing_id, quantity, material_id, thickness]):
                    missing_fields = []
                    if not drawing_id:
                        missing_fields.append("креслення")
                    if not quantity:
                        missing_fields.append("кількість")
                    if not material_id:
                        missing_fields.append("матеріал")
                    if not thickness:
                        missing_fields.append("товщина")
                    missing_fields_str = ", ".join(missing_fields)
                    messages.error(
                        request,
                        f"Для деталі №{i + 1} не заповнено такі поля: {missing_fields_str}. Будь ласка, заповніть їх."
                    )
                    context = {
                        "drawings": Drawing.objects.filter(user=request.user, configured=True),
                        "material_type": Material.MaterialTypeChoices.choices,
                        "materials": Material.objects.filter(available=True),
                        "materials_json": json.dumps(list(Material.objects.filter(available=True).values("id", "material_name", "material_type")), cls=DjangoJSONEncoder),
                        "initial_data": request.POST,
                    }
                    return render(request, "orders/create_order.html", context)

            if all([drawing_id, quantity, material_id, thickness]):
                try:
                    details_to_create.append(
                        {
                            "drawing_id": int(drawing_id), 
                            "quantity": int(quantity),
                            "material_id": int(material_id),
                            "thickness": Decimal(thickness.replace(",", ".")),
                        }
                    )
                except (ValueError, TypeError):
                    messages.error(
                        request, f"Некоректні дані для деталі №{i + 1}."
                    )
                    context = {
                        "drawings": Drawing.objects.filter(user=request.user, configured=True),
                        "material_type": Material.MaterialTypeChoices.choices,
                        "materials": Material.objects.filter(available=True),
                        "materials_json": json.dumps(list(Material.objects.filter(available=True).values("id", "material_name", "material_type")), cls=DjangoJSONEncoder),
                        "initial_data": request.POST,
                    }
                    return render(request, "orders/create_order.html", context)

        if not details_to_create:
            messages.error(request, "Не додано жодної деталі для створення замовлення.")
            context = {
                "drawings": Drawing.objects.filter(user=request.user, configured=True),
                "material_type": Material.MaterialTypeChoices.choices,
                "materials": Material.objects.filter(available=True),
                "materials_json": json.dumps(list(Material.objects.filter(available=True).values("id", "material_name", "material_type")), cls=DjangoJSONEncoder),
                "initial_data": request.POST,
            }
            return render(request, "orders/create_order.html", context)

        drawing_ids = [d["drawing_id"] for d in details_to_create]
        material_ids = [d["material_id"] for d in details_to_create]
        
        drawings = {d.id: d for d in Drawing.objects.filter(id__in=drawing_ids)}
        materials = {m.id: m for m in Material.objects.filter(id__in=material_ids)}

        order_cost = 0
        order = Order.objects.create(user=request.user)
        
        for detail_data in details_to_create:
            drawing = drawings.get(detail_data["drawing_id"])
            material = materials.get(detail_data["material_id"])
            
            if not drawing or not material:
                messages.error(request, "Не знайдено креслення або матеріал.")
                order.delete()
                return redirect("core:create_order")
                
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

        messages.success(request, "Замовлення успішно створено!")
        return redirect("core:order")

    materials = Material.objects.filter(available=True)
    materials_data = list(materials.values("id", "material_name", "material_type"))
    materials_json = json.dumps(materials_data, cls=DjangoJSONEncoder)

    context = {
        "drawings": Drawing.objects.filter(user=request.user, configured=True),
        "material_type": Material.MaterialTypeChoices.choices,
        "materials": materials,
        "materials_json": materials_json,
        "initial_data": request.POST,
    }
    return render(request, "orders/create_order.html", context)


@login_required
def detail_price(request):
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

    if not all([drawing_id, material_id, thickness, quantity]):
        return HttpResponse(
            f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>Заповніть всі поля для розрахунку</div>"
        )

    try:
        if not drawing_id.isdigit() or not material_id.isdigit():
            raise ValueError("Некоректні ID чертежа або матеріалу")
            
        if not thickness or not quantity:
            raise ValueError("Відсутні дані про товщину або кількість")

        thickness_clean = thickness.replace(",", ".")
        if Decimal(thickness_clean) == 0:
            return HttpResponse(
                f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>Товщина повинна бути більше 0</div>"
            )

        drawing = get_object_or_404(Drawing, id=drawing_id, user=request.user)
        material = get_object_or_404(Material, id=material_id)

        thickness_m = Decimal(thickness_clean) / 1000
        total_area_m2 = get_bounding_box_area_m2(drawing.file_path.path)
        volume_m3 = total_area_m2 * thickness_m
        mass_kg = volume_m3 * material.density
        material_cost = mass_kg * material.price_per_kg

        PRICE_PER_DEGREE = Decimal("0.1")
        MAX_BEND_ANGLE = 180
        MIN_BEND_ANGLE = 0

        # Вместо drawing.processing_types используем прямой запрос к ProcessingType
        cutting_type = ProcessingType.objects.filter(id=1).first()
        cutting_settings = drawing.process_settings.get("1", {})
        length_of_cuts = Decimal(cutting_settings.get("length_of_cuts", 0) or 0)
        cutting_cost = Decimal(0)
        if cutting_type:
            cutting_cost = cutting_type.base_cost_per_unit * length_of_cuts

        bending_type = ProcessingType.objects.filter(id=2).first()
        bending_settings = drawing.process_settings.get("2", {})
        bending_cost = Decimal(0)
        angles = bending_settings.get("angles", [])
        if angles and bending_type:
            degrees = [
                int(angle.get("degree", 0))
                for angle in angles
                if angle.get("degree")
            ]
            for degree in degrees:
                if MIN_BEND_ANGLE < degree <= MAX_BEND_ANGLE:
                    cost = bending_type.base_cost_per_unit + (PRICE_PER_DEGREE * degree)
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

    except (ValueError, TypeError) as e:
        return HttpResponse(
            f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>Помилка: некоректні дані</div>"
        )
    except Exception as e:
        return HttpResponse(
            f"<div class='order-form-price-result' data-index='{index}' hx-get='{request.build_absolute_uri().split('?')[0]}?index={index}' hx-trigger='change from:select,input delay:300ms' hx-include='closest .order-drawing-block' hx-target='this' hx-swap='outerHTML'>Помилка: {str(e)}</div>"
        )
