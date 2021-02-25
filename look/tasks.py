# invitro/shop/tasks.py
from celery import shared_task
from core.celery import app
from PIL import Image
from django.core.mail import send_mail
from .models import User
from django.conf import settings
import datetime


@app.task
def image_rotate(user):
    print(user)
    user = User.objects.get(pk=user)
    if not user.avatar_rotated:
        path = settings.BASE_DIR + user.avatar.url
        im = Image.open(path)
        im.rotate(90).save(path)
        user.avatar_rotated = True
        user.save()

@app.task
def send_new_users():
    now = datetime.datetime.now()
    users = list(list(
        User.objects.filter(date_joined__gte=datetime.datetime.now() - datetime.timedelta(hours=24)).values_list(
            'username'))[0])
    new_users = ''
    for user in users:
        new_users+=user+'\n'
    send_mail(
        'New users',
		new_users,
        'oldsem1976@gmail.com',
        ['semeshko.o@novaposhta.ua'],
        fail_silently=False,
    )

