from django.contrib import admin
from .models import Drawing, Order, Material, Detail


@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "slug",
        "name",
        "file_path",
        "original_filename",
        "file_size",
        "uploaded_at",
        "description",
    ]
    exclude = ("original_filename", "file_size")
    prepopulated_fields = {"slug": ("name",)}


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
        "length",
        "width",
        "thickness",
        "quantity",
        "calculated_cost",
        "created_at",
        "updated_at",
    ]
    list_filter = ["material"]
