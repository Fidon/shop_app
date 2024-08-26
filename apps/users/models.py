from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
from datetime import timedelta


def dtime():
    return timezone.now() + timedelta(hours=3)

# custom user model
class CustomUserManager(BaseUserManager):
    def create_user(self, username, fullname, phone, password=None, is_admin=False):
        if not username:
            raise ValueError("The username field cannot be blank")
        if not fullname:
            raise ValueError("The fullname field canot be blank")
        
        user = self.model(
            username = username,
            fullname = fullname,
            phone = phone,
            is_admin = is_admin,
        )
        
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    def create_superuser(self, username, fullname, phone, password=None):
        user = self.create_user(
            username = username,
            fullname = fullname,
            phone = phone,
            password = password,
            is_admin = True,
        )
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key = True)
    regdate = models.DateTimeField(default=dtime)
    username = models.CharField(unique = True, max_length = 150)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, null=True, default=None)
    last_login = models.DateTimeField(null = True, default=None)
    blocked = models.BooleanField(default = False)
    comment = models.TextField(null=True, default=None)
    is_admin = models.BooleanField(default = False)
    deleted = models.BooleanField(default = False)
    groups = models.ManyToManyField(Group, blank = True, related_name = 'custom_users')
    user_permissions = models.ManyToManyField(Permission, blank = True, related_name = 'custom_users')
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fullname']
    
    def __str__(self):
        return str(self.fullname)