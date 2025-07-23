import uuid
import os
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from .utils import get_details_area_m2  
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class ProcessingType(models.Model):
    name = models.CharField(
        max_length=255, unique=True,
        verbose_name=_("Назва")
    )
    base_cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name=_("Базова вартість за одиницю")
    )
    cost_unit = models.CharField(
        max_length=50,
        verbose_name=_("Одиниця виміру вартості")
    )
    unit_name = models.CharField(
        max_length=255,
        verbose_name=_("Назва одиниці")
    )
    description = models.TextField(
        blank=True, null=True,
        verbose_name=_("Опис")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активний")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Тип обробки")
        verbose_name_plural = _("Типи обробки")


class Consumables(models.Model):
    class UnitChoices(models.TextChoices):
        PIECE = "шт", _( "Штука")
        SET = "комп", _( "Комплект")
        PAIR = "пара", _( "Пара")
        PACKAGE = "упак", _( "Упаковка")
        GRAM = "г", _( "Грам")
        KILOGRAM = "кг", _( "Кілограм")
        TON = "т", _( "Тонна")
        MILLIMETER = "мм", _( "Міліметр")
        CENTIMETER = "см", _( "Сантиметр")
        METER = "м", _( "Метр")
        KILOMETER = "км", _( "Кілометр")
        MILLILITER = "мл", _( "Мілілітр")
        LITER = "л", _( "Літр")
        CUBIC_CM = "см³", _( "Кубічний сантиметр")
        CUBIC_M = "м³", _( "Кубічний метр")
        SQUARE_MM = "мм²", _( "Квадратний міліметр")
        SQUARE_CM = "см²", _( "Квадратний сантиметр")
        SQUARE_M = "м²", _( "Квадратний метр")

    processing_type = models.ForeignKey(
        ProcessingType, on_delete=models.PROTECT, related_name="processes",
        verbose_name=_("Тип обробки")
    )
    name = models.CharField(max_length=255, verbose_name=_("Назва"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Ціна"))
    calculation_unit = models.CharField(max_length=50, choices=UnitChoices.choices, verbose_name=_("Одиниця розрахунку"))
    quantity_units = models.PositiveIntegerField(default=0, verbose_name=_("Кількість одиниць"))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Ціна за одиницю"))
    available = models.BooleanField(default=True, verbose_name=_("Доступний"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _( "Розхідний матеріал")
        verbose_name_plural = _( "Розхідні матеріали")

    def clean(self):
        if self.quantity_units < 0:
            raise ValidationError("Quantity units must be non-negative")

    @property
    def unit_price(self):
        if self.quantity_units:
            return self.price / self.quantity_units
        return 0


class Drawing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="drawings", verbose_name=_("Користувач"))
    name = models.CharField(max_length=255, verbose_name=_("Назва"))
    file_path = models.FileField(upload_to="drawings/%Y/%m/%d", verbose_name=_("Файл креслення"))
    original_filename = models.CharField(max_length=255, blank=True, editable=False, verbose_name=_("Оригінальна назва файлу"))
    file_size = models.PositiveIntegerField(blank=True, editable=False, verbose_name=_("Розмір файлу (байт)"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата завантаження"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Опис"))
    layers = models.JSONField(blank=True, null=True, default=list, verbose_name=_("Шари"))
    process_settings = models.JSONField(default=dict, blank=True, null=True, verbose_name=_("Налаштування процесів"))
    configured = models.BooleanField(default=False, verbose_name=_("Налаштовано"))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.file_path:
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file_path.name)
            try:
                self.file_size = self.file_path.size
            except Exception:
                self.file_size = 0
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _( "Креслення")
        verbose_name_plural = _( "Креслення")


def generate_order_number():
    return str(uuid.uuid4().hex[:8].upper())


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", _( "Чернетка")
        PENDING = "pending", _( "Очікує обробки")
        PROCESSING = "processing", _( "Обробляється")
        COMPLETED = "completed", _( "Завершено")
        CANCELLED = "cancelled", _( "Скасовано")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders", verbose_name=_("Користувач"))
    order_number = models.CharField(
        max_length=50, unique=True, default=generate_order_number, verbose_name=_("Номер замовлення")
    )
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT, db_index=True, verbose_name=_("Статус")
    )
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Загальна вартість"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Дата створення"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата оновлення"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Примітки"))

    def __str__(self):
        return self.order_number

    class Meta:
        verbose_name = _( "Замовлення")
        verbose_name_plural = _( "Замовлення")
        ordering = ["-created_at"]


class Material(models.Model):
    class MaterialTypeChoices(models.TextChoices):
        METAL = "metal", _( "Метал")
        PLASTIC = "plastic", _( "Пластик")
        COMPOSITES = "composites", _( "Композити")

    material_name = models.CharField(max_length=50, unique=True, verbose_name=_("Назва матеріалу"))
    material_type = models.CharField(
        max_length=20,
        choices=MaterialTypeChoices.choices,
        default=MaterialTypeChoices.METAL,
        verbose_name=_("Тип матеріалу")
    )
    density = models.PositiveIntegerField(default=0, verbose_name=_("Густина (кг/м³)"))
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Ціна за кг"))
    properties = models.TextField(blank=True, null=True, verbose_name=_("Властивості"))
    available = models.BooleanField(default=True, verbose_name=_("Доступний"))

    def __str__(self):
        return self.material_name

    class Meta:
        verbose_name = _( "Матеріал")
        verbose_name_plural = _( "Матеріали")

    def clean(self):
        if self.density < 0:
            raise ValidationError("Density must be non-negative")


class Detail(models.Model):
    drawing = models.ForeignKey(
        Drawing, on_delete=models.PROTECT, related_name="details", verbose_name=_("Креслення")
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="details", verbose_name=_("Замовлення"))
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="details", verbose_name=_("Матеріал")
    )
    thickness = models.DecimalField(max_digits=10, decimal_places=3, verbose_name=_("Товщина (мм)"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Кількість"))
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Вартість матеріалу"))
    cutting_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Вартість різання"))
    bending_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Вартість згинання"))
    drawing_snapshot = models.JSONField(blank=True, null=True, verbose_name=_("Зліпок креслення"))

    def __str__(self):
        return f"Order: {self.order.order_number} - Drawing: {self.drawing.name}"

    class Meta:
        verbose_name = _( "Деталь")
        verbose_name_plural = _( "Деталі")

    def clean(self):
        if self.thickness <= 0:
            raise ValidationError("Thickness must be positive")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")

    def get_detail_cost(self):
        return self.material_cost + self.cutting_cost + self.bending_cost

    def get_drawing_snapshot(self):
        drawing = self.drawing
        return {
            "name": drawing.name,
            "file_path": str(drawing.file_path),
            "original_filename": drawing.original_filename,
            "file_size": drawing.file_size,
            "description": drawing.description,
            "length_of_cuts": drawing.process_settings.get("1", {}).get("length_of_cuts", 0),
            "angles": drawing.process_settings.get("2", {}).get("angles", []),
            "layers": drawing.layers,
            "cutting_layers": drawing.process_settings.get("1", {}).get("layers", []),
            "bending_layers": drawing.process_settings.get("2", {}).get("layers", []),
            "configured": drawing.configured,
        }

    def save(self, *args, **kwargs):
        self.drawing_snapshot = self.get_drawing_snapshot()
        super().save(*args, **kwargs)

    def calculate_cost(self):
        material = self.material
        drawing = self.drawing

        total_area_m2 = get_details_area_m2(drawing.file_path.path)
        thickness_m = Decimal(self.thickness) / 1000

        volume_m3 = total_area_m2 * thickness_m
        mass_kg = volume_m3 * material.density

        material_cost = mass_kg * material.price_per_kg

        from .models import ProcessingType
        cutting_type = ProcessingType.objects.filter(id=1).first()
        cutting_settings = drawing.process_settings.get("1", {})
        length_of_cuts = Decimal(cutting_settings.get("length_of_cuts", 0) or 0)
        if cutting_type:
            cutting_cost = cutting_type.base_cost_per_unit * length_of_cuts
        else:
            cutting_cost = Decimal(0)

        bending_type = ProcessingType.objects.filter(id=2).first()
        price_per_degree = Decimal("0.2")
        bending_cost = Decimal(0)
        angles = drawing.process_settings.get("2", {}).get("angles", [])
        if angles and bending_type:
            degrees = [
                int(angle.get("degree", 0))
                for angle in angles
                    if angle.get("degree")
            ]
            for degree in degrees:
                if 0 < degree <= 180:
                    cost = bending_type.base_cost_per_unit + (price_per_degree * degree)
                    bending_cost += cost

        self.material_cost = material_cost.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.cutting_cost = cutting_cost.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.bending_cost = bending_cost.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
