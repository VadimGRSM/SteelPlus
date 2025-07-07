import uuid
import os
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = settings.AUTH_USER_MODEL


class ProcessingType(models.Model):
    name = models.CharField(max_length=255)
    base_cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    cost_unit = models.CharField(max_length=50)
    unit_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип обробки"
        verbose_name_plural = "Типи обробки"


class Consumables(models.Model):
    class UnitChoices(models.TextChoices):
        PIECE = "шт", "Штука"
        SET = "комп", "Комплект"
        PAIR = "пара", "Пара"
        PACKAGE = "упак", "Упаковка"
        GRAM = "г", "Грам"
        KILOGRAM = "кг", "Кілограм"
        TON = "т", "Тонна"
        MILLIMETER = "мм", "Міліметр"
        CENTIMETER = "см", "Сантиметр"
        METER = "м", "Метр"
        KILOMETER = "км", "Кілометр"
        MILLILITER = "мл", "Мілілітр"
        LITER = "л", "Літр"
        CUBIC_CM = "см³", "Кубічний сантиметр"
        CUBIC_M = "м³", "Кубічний метр"
        SQUARE_MM = "мм²", "Квадратний міліметр"
        SQUARE_CM = "см²", "Квадратний сантиметр"
        SQUARE_M = "м²", "Квадратний метр"

    processing_type = models.ForeignKey(
        ProcessingType, on_delete=models.PROTECT, related_name="processes"
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    calculation_unit = models.CharField(max_length=50, choices=UnitChoices.choices)
    quantity_units = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Розхідні матеріали"
        verbose_name_plural = "Розхідний матеріал"


class Drawing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="drawings")
    processing_types = models.ManyToManyField(ProcessingType, related_name="drawings")
    name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to="drawings/%Y/%m/%d")
    original_filename = models.CharField(max_length=255, blank=True, editable=False)
    file_size = models.PositiveIntegerField(blank=True, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    length_of_cuts = models.FloatField(default=0)
    angles = models.JSONField(blank=True, null=True, default=list)
    layers = models.JSONField(blank=True, null=True, default=list)
    cutting_layers = models.JSONField(blank=True, null=True, default=list)
    bending_layers = models.JSONField(blank=True, null=True, default=list)
    configured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.file_path:
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file_path.name)
            if not self.file_size:
                self.file_size = self.file_path.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Креслення"
        verbose_name_plural = "Креслення"


def generate_order_number():
    return str(uuid.uuid4().hex[:8].upper())


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PENDING = "pending", "Очікує обробки"
        PROCESSING = "processing", "Обробляється"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Скасовано"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(
        max_length=50, unique=True, default=generate_order_number
    )
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT
    )
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.order_number

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        ordering = ["-created_at"]


class Material(models.Model):
    class MaterialTypeChoices(models.TextChoices):
        METAL = "metal", "Метал"
        PLASTIC = "plastic", "Пластик"
        COMPOSITES = "composites", "Композити"

    material_name = models.CharField(max_length=50, unique=True)
    material_type = models.CharField(
        max_length=20,
        choices=MaterialTypeChoices.choices,
        default=MaterialTypeChoices.METAL,
    )
    price_unit_area = models.DecimalField(max_digits=10, decimal_places=2)
    properties = models.TextField(blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.material_name

    class Meta:
        verbose_name = "Матеріал"
        verbose_name_plural = "Матеріали"


class Detail(models.Model):
    drawing = models.ForeignKey(
        Drawing, on_delete=models.PROTECT, related_name="details"
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="details")
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="details"
    )
    thickness = models.DecimalField(max_digits=10, decimal_places=3)
    quantity = models.PositiveIntegerField(default=1)
    calculated_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order: {self.order.order_number} - Drawing: {self.drawing.name}"

    class Meta:
        verbose_name = "Деталь"
        verbose_name_plural = "Деталі"
