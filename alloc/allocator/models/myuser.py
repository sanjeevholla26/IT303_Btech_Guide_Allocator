from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.models import BaseUserManager
from allocator.manager.user_manager import CustomUserManager


class MyUser(AbstractUser):
    # email = models.EmailField(unique=True)  # Override the default email field to make it unique
    edu_email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=15)
    otp = models.CharField(max_length=10, blank=True, null=True)
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.edu_email

    objects = CustomUserManager()

    USERNAME_FIELD = 'edu_email'
    REQUIRED_FIELDS = ['username']

    def has_permission(self, fun, app):
        roles = self.roles.all()
        all_actions = {}

        for role in roles:
            for perm in role.permissions.all():
                app_name = perm.app_name
                actions = perm.actions.split(',')

                if app_name in all_actions:
                    all_actions[app_name].extend(actions)
                else:
                    all_actions[app_name] = actions

        for app_name in all_actions:
            all_actions[app_name] = list(set(all_actions[app_name]))
        if not app in all_actions or not fun in all_actions[app] :
            return False

        return True
