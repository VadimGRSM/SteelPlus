from django import forms
from .models import Drawing


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
            'file_path': forms.FileInput(
                attrs={
                    "class": "hidden-file-input",
                    "id": "id_file_path",
                    'accept': '.pdf,.dwg,.dxf',
                }
            ),
        }
