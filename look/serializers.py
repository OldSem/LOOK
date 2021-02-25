from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import ugettext_lazy as _
from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,
                               get_username_max_length)
from allauth.account.utils import setup_user_email
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from allauth.account.adapter import get_adapter
from . import tasks

# Get the UserModel
UserModel = get_user_model()

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = UserModel
        fields = ('pk', 'username', 'email', 'first_name', 'last_name','avatar','birthday')
        read_only_fields = ('email', )

    def save(self, *args, **kwargs):
        super(serializers.ModelSerializer, self).save(*args, **kwargs)
        tasks.image_rotate.apply_async(args=self.instance.pk,countdown=2)


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()

    password_reset_form_class = PasswordResetForm

    def get_email_options(self):
        """Override this method to change default e-mail options"""
        return {}

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return value


    def save(self):
        request = self.context.get('request')
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),

            ###### USE YOUR TEXT FILE ######
            'email_template_name': 'password_reset_email.html',

            'request': request,
        }
        self.reset_form.save(**opts)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=get_username_max_length(),
        min_length=allauth_settings.USERNAME_MIN_LENGTH,
        required=allauth_settings.USERNAME_REQUIRED
    )
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    avatar = serializers.ImageField()
    birthday = serializers.DateField()

    def validate_avatar(self, avatar):
        megabyte_limit=0.5
        if avatar.size > megabyte_limit*1024*1024:
            raise serializers.ValidationError("Max file size is %sMB" % str(megabyte_limit))
        return avatar


    def validate_username(self, username):
        username = get_adapter().clean_username(username)
        return username

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address."))
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data

    def custom_signup(self, request, user):
        pass

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'avatar': self.validated_data.get('avatar', ''),
            'birthday': self.validated_data.get('birthday', '')
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        if request.FILES['avatar']:
            avatar = request.FILES['avatar']
            user.avatar.save(avatar.name,avatar) 
        user.birthday =  self.cleaned_data.get("birthday")         
        user.save()
        tasks.image_rotate.apply_async(args=[user.pk],countdown=2)
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        return user