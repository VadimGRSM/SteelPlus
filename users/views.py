from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse, reverse_lazy

from .utils import send_email_for_verify, token_generator
from .form import (
    LoginUserForm,
    RegisterUserForm,
    ProfileUserForm,
    UserPasswordChangeForm,
)

User = get_user_model()


def invalid_verify(request):
    reason_code = request.GET.get("reason", "unknown")
    reasons = {
        "not_found": "Користувача не знайдено. Можливо, посилання пошкоджено.",
        "already_verified": "Пошту вже підтверджено. Ви можете увійти до облікового запису.",
        "expired": "Строк дії посилання закінчився. Будь ласка, зверніться до нового листа.",
        "unknown": "Сталася невідома помилка. Спробуйте пізніше.",
    }
    return render(
        request,
        "users/invalid_verify.html",
        {
            "reason": reasons.get(reason_code, reasons["unknown"]),
            "reason_code": reason_code,
        },
    )


def confirm_email(request):
    return render(request, "users/confirm_email.html")


class ConfirmEmailComplete(View):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if user is None:
            return redirect(f"{reverse('users:invalid_verify')}?reason=not_found")

        if user.email_verify:
            return redirect(
                f"{reverse('users:invalid_verify')}?reason=already_verified"
            )

        if token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
            login(request, user, backend="users.authentication.EmailAuthBackends")
            return render(request, "users/confirm_email_complete.html")

        return redirect(f"{reverse('users:invalid_verify')}?reason=expired")

    @staticmethod
    def get_user(uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            pk = int(uid)
            user = User.objects.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "users/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not user.email_verify:
            send_email_for_verify(self.request, user)
            return redirect("users:confirm_email")
        return super().form_valid(form)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse("core:hub"))


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:confirm_email")

    def form_valid(self, form):
        self.object = form.save()
        send_email_for_verify(self.request, self.object)
        return super().form_valid(form)


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = "users/profile.html"

    def get_success_url(self):
        return reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class UserPasswordChange(LoginRequiredMixin, PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")
    template_name = "users/password_change_form.html"
