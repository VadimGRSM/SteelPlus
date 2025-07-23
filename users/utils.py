from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + user.email + str(timestamp) + str(user.is_active)
        )

token_generator = EmailVerificationTokenGenerator()


def send_email_for_verify(request, user):
    current_site = get_current_site(request)

    context = {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token_generator.make_token(user)
    }

    message = render_to_string('users/confirm_email_message.html', context=context)

    email = EmailMessage('Верифікація електронної пошти', message, to=[user.email])

    email.send()
