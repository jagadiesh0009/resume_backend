from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    email=models.EmailField(unique=True)
    phn = models.CharField(max_length=10, blank=True, null=True)
    dateofbirth=models.DateField(blank=True,null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # "user" or "model"
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return self.role


class Fruit(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)

    def __str__(self):
        return self.name
