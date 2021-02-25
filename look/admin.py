
from django.contrib import admin
from django.db import models
from .models import User
from django.contrib.auth.admin import UserAdmin
from . import tasks


def save_model(self, *args, **kwargs):
    super(UserAdmin, self).save_model(*args, **kwargs)
    tasks.image_rotate.apply_async(args=[args[1].pk],countdown=2) 

UserAdmin.list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff','avatar_tag','birthday','avatar_rotated')
UserAdmin.fieldsets[2][1]['fields']=('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions','avatar','birthday')
UserAdmin.add_fieldsets[0][1]['fields'] = ('username', 'password1', 'password2','avatar','birthday')
UserAdmin.save_model = save_model

admin.site.register(User,UserAdmin)


	# Register your models here.
