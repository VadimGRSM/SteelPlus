import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Drawing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drawings')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='drawings/%Y/%m/%d')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "Креслення"
        verbose_name_plural = "Креслення"


def generate_order_number():
    return str(uuid.uuid4().hex[:8].upper())


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', 'Чернетка'
        PENDING = 'pending', 'Очікує обробки'
        PROCESSING = 'processing', 'Обробляється'
        COMPLETED = 'completed', 'Завершено'
        CANCELLED = 'cancelled', 'Скасовано'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, default=generate_order_number)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.order_number

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"


class Material(models.Model):
    class MaterialTypeChoices(models.TextChoices):
        METAL = 'metal', 'Метал'
        PLASTIC = 'plastic', 'Пластик'
        COMPOSITES = 'composites', 'Композити'

    material_name = models.CharField(max_length=50, unique=True)
    material_type = models.CharField(
        max_length=20,
        choices=MaterialTypeChoices.choices,
        default=MaterialTypeChoices.METAL
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
    drawing = models.ForeignKey(Drawing, on_delete=models.PROTECT, related_name='details')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='details')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='details')
    length = models.DecimalField(max_digits=10, decimal_places=3)
    width = models.DecimalField(max_digits=10, decimal_places=3)
    thickness = models.DecimalField(max_digits=10, decimal_places=3)
    quantity = models.PositiveIntegerField(default=1)
    calculated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order: {self.order.order_number} - Drawing: {self.drawing.file_name}"

    class Meta:
        verbose_name = "Деталь"
        verbose_name_plural = "Деталі"
