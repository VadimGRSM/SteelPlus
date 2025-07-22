from django import forms
from django.forms import Textarea
from django.core.exceptions import ValidationError
from .models import Drawing, Material, Detail
import json


class DetailForm(forms.Form):
    drawing = forms.ModelChoiceField(queryset=Drawing.objects.all(), label="Креслення")
    quantity = forms.IntegerField(min_value=1, label="Кількість")
    material_type = forms.ChoiceField(
        choices=Material.MaterialTypeChoices.choices, label="Тип матеріалу"
    )
    material = forms.ModelChoiceField(
        queryset=Material.objects.none(), label="Матеріал"
    )
    thickness = forms.DecimalField(
        min_value=0.1, decimal_places=1, label="Товщина (мм)"
    )


class SettingsDrawingForm(forms.ModelForm):
    description = forms.CharField(
        widget=Textarea(
            attrs={
                "class": "description-textbox",
                "rows": 5,
                "placeholder": "Введіть загальний опис креслення...",
            }
        ),
        required=False,
    )

    class Meta:
        model = Drawing
        fields = ["description"]


class DrawingForm(forms.ModelForm):
    name = forms.CharField(
        label="Назва креслення",
        widget=forms.TextInput(
            attrs={"class": "text-field", "placeholder": "Введіть назву креслення"}
        ),
    )
    description = forms.CharField(
        label="Опис",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "text-field multiline-text-field",
                "placeholder": "Опис (необов'язково)",
            }
        ),
    )

    class Meta:
        model = Drawing
        fields = ["file_path", "name", "description"]
        widgets = {
            "file_path": forms.FileInput(
                attrs={
                    "class": "hidden-file-input",
                    "id": "id_file_path",
                    "accept": ".pdf,.dwg,.dxf",
                }
            ),
        }
