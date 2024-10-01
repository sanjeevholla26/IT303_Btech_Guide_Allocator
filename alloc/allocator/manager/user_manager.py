from django.contrib.auth.models import BaseUserManager
from ..models.role import Role

class CustomUserManager(BaseUserManager):
    def create_user(self, edu_email, email, username, password=None, **extra_fields):
        if not edu_email:
            raise ValueError('The edu_email field must be set')
        if not edu_email.endswith("@nitk.edu.in"):
            raise ValueError('The Email ID must be an NITK edu mail ID.')
        edu_email = self.normalize_email(edu_email)
        user = self.model(username=username.strip(), email=email, edu_email=edu_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, edu_email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        created_user = self.create_user(edu_email, "default@gmail.com", username, password, **extra_fields)

        admin_role, created = Role.objects.get_or_create(role_name="admin")
        admin_role.users.add(created_user)
        admin_role.save()

        return created_user
