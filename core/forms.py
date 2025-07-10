from django import forms
from django.forms import Textarea
from django.core.exceptions import ValidationError
from .models import Drawing
import json


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

    length_of_cuts = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
    )

    angles = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = Drawing
        fields = ["description", "length_of_cuts", "angles"]

    def clean_angles(self):
        angles_str = self.cleaned_data.get("angles")

        if not angles_str:
            return []

        try:
            angles_data = json.loads(angles_str)
        except json.JSONDecodeError:
            raise ValidationError("Некоректний формат кутів.")

        if not isinstance(angles_data, list):
            raise ValidationError("Дані кутів мають бути списком.")

        for i, angle in enumerate(angles_data):
            if not isinstance(angle, dict):
                raise ValidationError(f"Кут {i+1}: неправильний формат даних.")

            point = angle.get("point", "").strip()
            if not point or point == "Обрати" or "Клікніть на зображення" in point:
                raise ValidationError(f"Кут {i+1}: точка на зображенні не вибрана.")

            try:
                degree = float(angle.get("degree", 0))
                if degree < 0 or degree > 360:
                    raise ValidationError(f"Кут {i+1}: градус має бути від 0 до 360.")
            except (ValueError, TypeError):
                raise ValidationError(f"Кут {i+1}: некоректне значення градуса.")

            radius = angle.get("radius", "").strip()
            if not radius or radius == "Обрати":
                raise ValidationError(f"Кут {i+1}: не заданий радіус згинання.")

            try:
                radius_value = float(radius.replace("px", ""))
                if radius_value <= 0:
                    raise ValidationError(
                        f"Кут {i+1}: радіус має бути позитивним числом."
                    )
            except (ValueError, TypeError):
                raise ValidationError(f"Кут {i+1}: некоректне значення радіусу.")

        return angles_data

    def clean(self):
        cleaned_data = super().clean()

        cutting_layers = []
        bending_layers = []

        if hasattr(self, "data"):
            cutting_layers = (
                self.data.getlist("cutting") if hasattr(self.data, "getlist") else []
            )
            bending_layers = (
                self.data.getlist("bending") if hasattr(self.data, "getlist") else []
            )

        if cutting_layers and bending_layers:
            overlapping_layers = set(cutting_layers) & set(bending_layers)
            if overlapping_layers:
                raise ValidationError(
                    f"Шари не можуть використовуватися одночасно для різання та згинання: {', '.join(overlapping_layers)}"
                )

        if bending_layers:
            angles_data = cleaned_data.get("angles", [])
            if not angles_data:
                raise ValidationError("Для шарів згинання необхідно налаштувати кути.")

        return cleaned_data


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
