from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    email = models.EmailField(unique=True)


class AnonymousUser(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Anonymous User'
        verbose_name_plural = 'Anonymous Users'
        ordering = ['-last_active']
    
    def __str__(self):
        return f"Anonymous User {self.session_id}"
       