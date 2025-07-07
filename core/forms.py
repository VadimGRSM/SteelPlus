from django import forms
from django.forms import Textarea
from .models import Drawing


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
