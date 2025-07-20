from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = [
        'email_ua',
        'first_name_ua',
        'last_name_ua',
        'phone_number_ua',
        'email_verify_ua',
        'is_active_ua',
        'is_staff_ua',
        'is_superuser_ua',
        'last_login_ua',
        'date_joined_ua',
    ]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Персональна інформація'), {'fields': ('first_name', 'last_name', 'phone_number', 'email_verify')}),
        (_('Права доступу'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Важливі дати'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'phone_number'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'email_verify')

    def email_ua(self, obj):
        return obj.email
    email_ua.short_description = "Електронна пошта"

    def first_name_ua(self, obj):
        return obj.first_name
    first_name_ua.short_description = "Ім'я"

    def last_name_ua(self, obj):
        return obj.last_name
    last_name_ua.short_description = "Прізвище"

    def phone_number_ua(self, obj):
        return obj.phone_number
    phone_number_ua.short_description = "Номер телефону"

    def email_verify_ua(self, obj):
        return "Так" if obj.email_verify else "Ні"
    email_verify_ua.short_description = "Підтверджено email"

    def is_active_ua(self, obj):
        return "Так" if obj.is_active else "Ні"
    is_active_ua.short_description = "Активний"

    def is_staff_ua(self, obj):
        return "Так" if obj.is_staff else "Ні"
    is_staff_ua.short_description = "Персонал"

    def is_superuser_ua(self, obj):
        return "Так" if obj.is_superuser else "Ні"
    is_superuser_ua.short_description = "Суперкористувач"

    def last_login_ua(self, obj):
        return obj.last_login
    last_login_ua.short_description = "Останній вхід"

    def date_joined_ua(self, obj):
        return obj.date_joined
    date_joined_ua.short_description = "Дата реєстрації"
