from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


def validate_image(fieldfile_obj):
    try:
        filesize = fieldfile_obj.file.size
    except:
        filesize = fieldfile_obj.size
    megabyte_limit = 0.5
    if filesize > megabyte_limit * 1024 * 1024:
        raise ValidationError("Max file size is %sMB" % str(megabyte_limit))


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    birthday = models.DateField(null=True, blank=True)
    avatar = models.ImageField("Avatar",
                               upload_to='avatars',
                               validators=[validate_image],
                               blank=True,
                               null=True,
                               help_text='Maximum file size allowed is 500kb')
    avatar_rotated = models.BooleanField(default=False, blank=True)

    # Here I return the avatar or picture with an owl, if the avatar is not selected
    def get_avatar(self):
        if not self.avatar:
            return 'https://listimg.pinclipart.com/picdir/s/3-35953_svg-transparent-owl-images-at-getdrawings-great-gray.png'
        return self.avatar.url

    # method to create a fake table field in read only mode
    def avatar_tag(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % self.get_avatar())

    avatar_tag.short_description = 'Avatar'
