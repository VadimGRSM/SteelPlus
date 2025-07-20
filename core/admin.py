from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Drawing, Order, Material, Detail, ProcessingType, Consumables
from django.utils.html import format_html
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

class DetailInline(admin.TabularInline):
    model = Detail
    extra = 0
    verbose_name = _("Деталь")
    verbose_name_plural = _("Деталі")

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
        "uploaded_at",
        "configured",
    ]
    search_fields = ["name", "user__username", "original_filename"]
    list_filter = ["processing_types", "uploaded_at", "configured"]
    readonly_fields = ["original_filename", "file_size", "uploaded_at"]
    inlines = [DetailInline]
    fieldsets = (
        (_("Основна інформація"), {
            "fields": ("user", "name", "description", "file_path", "original_filename", "file_size", "uploaded_at", "configured")
        }),
        (_("Обробка"), {
            "fields": ("processing_types", "length_of_cuts", "angles", "layers", "cutting_layers", "bending_layers")
        }),
    )

    def get_processing_types(self, obj):
        return ", ".join([pt.name for pt in obj.processing_types.all()])
    get_processing_types.short_description = _("Типи обробки")

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
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "user__username"]
    list_editable = ["status"]
    readonly_fields = ["order_number", "created_at", "updated_at", "total_cost"]
    fieldsets = (
        (_("Основна інформація"), {
            "fields": ("user", "order_number", "status", "total_cost", "created_at", "updated_at")
        }),
        (_("Додатково"), {
            "fields": ("notes",)
        }),
    )
    inlines = [DetailInline]

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        "material_name",
        "material_type",
        "density",
        "price_per_kg",
        "properties",
        "available",
    ]
    list_filter = ["available", "material_type"]
    search_fields = ["material_name"]
    list_editable = ["available"]
    fieldsets = (
        (_("Основна інформація"), {
            "fields": ("material_name", "material_type", "available")
        }),
        (_("Властивості"), {
            "fields": ("density", "price_per_kg", "properties")
        }),
    )

@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = [
        "drawing",
        "order",
        "material",
        "thickness",
        "quantity",
        "material_cost",
        "cutting_cost",
        "bending_cost",
    ]
    list_filter = ["material", "order"]
    search_fields = ["drawing__name", "order__order_number", "material__material_name"]
    readonly_fields = ["drawing_snapshot_pretty"]

    fieldsets = (
        (None, {
            "fields": (
                "drawing", "order", "material", "thickness", "quantity",
                "material_cost", "cutting_cost", "bending_cost", "drawing_snapshot_pretty"
            )
        }),
    )

    def drawing_snapshot_pretty(self, obj):
        import json
        if not obj.drawing_snapshot:
            return format_html("<span style='color: #f55;'>Немає зліпка (snapshot)!</span>")
        return format_html(
            "<pre style='font-family: monospace; font-size: 14px; background: #fff; color: #222; "
            "padding: 16px; border-radius: 8px; border: 1px solid #ddd; overflow-x: auto;'>{}</pre>",
            json.dumps(obj.drawing_snapshot, indent=2, ensure_ascii=False)
        )
    drawing_snapshot_pretty.short_description = "Зліпок креслення"
    drawing_snapshot_pretty.allow_tags = True

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
    list_filter = ["is_active"]
    search_fields = ["name"]

@admin.register(Consumables)
class ConsumablesAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "processing_type",
        "price",
        "calculation_unit",
        "quantity_units",
        "available",
    ]
    list_filter = ["processing_type", "available"]
    search_fields = ["name"]
    list_editable = ["available"]

try:
    from django_celery_results.models import TaskResult, GroupResult
    admin.site.unregister(TaskResult)
    admin.site.unregister(GroupResult)
except admin.sites.NotRegistered:
    pass
except ImportError:
    pass

try:
    from django_celery_beat.models import (
        PeriodicTask, IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule
    )
    admin.site.unregister(PeriodicTask)
    admin.site.unregister(IntervalSchedule)
    admin.site.unregister(CrontabSchedule)
    admin.site.unregister(SolarSchedule)
    admin.site.unregister(ClockedSchedule)
except admin.sites.NotRegistered:
    pass
except ImportError:
    pass

