from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


class ProfileUserForm(forms.ModelForm):
    email = forms.CharField(
        disabled=True,
        label="Email",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )

    phone_number = forms.CharField(
        disabled=True,
        label="Номер телефону",
        widget=forms.TextInput(attrs={"class": "form-input", "type": "tel"}),
    )

    date_joined = forms.DateTimeField(
        disabled=True,
        label="Дата та час реєстрації",
        widget=forms.DateTimeInput(attrs={"class": "form-input"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = get_user_model()
        fields = ["email", "phone_number", "first_name", "last_name", "date_joined"]
        labels = {
            "first_name": "Ім'я",
            "last_name": "Прізвище",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
        }


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Старий пароль", widget=forms.PasswordInput(attrs={"class": "form-input"})
    )
    new_password1 = forms.CharField(
        label="Новий пароль", widget=forms.PasswordInput(attrs={"class": "form-input"})
    )
    new_password2 = forms.CharField(
        label="Підтвердження пароля",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )


class LoginUserForm(AuthenticationForm):
    username = forms.EmailField(
        label="Електронна пошта",
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "placeholder": "your@email.com",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={
                "id": "loginPassword",
                "placeholder": "Введіть пароль",
            }
        ),
    )

    class Meta:
        model = get_user_model()
        fields = ["email", "password"]


class RegisterUserForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={
                "id": "registerPassword",
                "placeholder": "Створіть пароль",
            }
        ),
    )
    password2 = forms.CharField(
        label="Повтор пароля",
        widget=forms.PasswordInput(
            attrs={
                "id": "confirmPassword",
                "placeholder": "Повторить пароль",
            }
        ),
    )

    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name", "phone_number"]
        labels = {
            "email": "Email",
            "first_name": "Ім'я",
            "last_name": "Прізвище",
            "phone_number": "Номер телефону",
        }
        widgets = {
            "email": forms.TextInput(attrs={"placeholder": "your@email.com"}),
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "phone_number": forms.TextInput(
                attrs={"type": "tel", "pattern": r"^(\+380\d{9}|0\d{9})$"}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Користувач з таким Email вже існує!")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Паролі не співпадають.")

        try:
            validate_password(password1)
        except ValidationError as e:
            self.add_error("password1", e)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
