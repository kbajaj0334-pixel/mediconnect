from django.db import models
from django.conf import settings

class Hospital(models.Model):
    
    name = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
