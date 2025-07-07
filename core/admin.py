from django.contrib import admin
from .models import Drawing, Order, Material, Detail, ProcessingType


@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "get_processing_types",
        "name",
        "file_path",
        "original_filename",
        "file_size",
        "description",
    ]
    exclude = ("original_filename", "file_size")

    def get_processing_types(self, obj):
        return ", ".join([pt.name for pt in obj.processing_types.all()])

    get_processing_types.short_description = "Типи обробки"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "order_number",
        "status",
        "total_cost",
        "created_at",
        "updated_at",
        "notes",
    ]
    list_filter = ["order_number", "status"]
    list_editable = ["status"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        "material_name",
        "material_type",
        "price_unit_area",
        "properties",
        "available",
    ]
    list_filter = ["available", "material_type"]
    list_editable = ["available"]


@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = [
        "drawing",
        "order",
        "material",
        "thickness",
        "quantity",
        "calculated_cost",
    ]
    list_filter = ["material"]


@admin.register(ProcessingType)
class ProcessingTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "base_cost_per_unit",
        "cost_unit",
        "unit_name",
        "description",
        "is_active",
    ]
