from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from enum import Enum

# Enum for event status choices
class EventStatus(Enum):
    OPEN = 'open'
    LOCKED = 'locked'
    CLOSED = 'closed'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.capitalize()) for key in cls]

class CustomUserManager(BaseUserManager):
    def create_user(self, eduMailID, email, username, password=None, **extra_fields):
        if not eduMailID:
            raise ValueError('The eduMailID field must be set')
        if not eduMailID.endswith("@nitk.edu.in"):
            raise ValueError('The Email ID must be an NITK edu mail ID.')
        eduMailID = self.normalize_email(eduMailID)
        user = self.model(username=username.strip(), email=email, eduMailID=eduMailID, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, username, eduMailID, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(eduMailID, "default@gmail.com", username, password, **extra_fields)

class MyUser(AbstractUser):
    # email = models.EmailField(unique=True)  # Override the default email field to make it unique
    eduMailID = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=15)

    def __str__(self):
        return self.eduMailID

    objects = CustomUserManager()

    USERNAME_FIELD = 'eduMailID'
    REQUIRED_FIELDS = ['username']

# Student model
class Student(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, primary_key=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    academic_year = models.IntegerField()  # e.g., 2024
    branch = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.username} - {self.branch}'

# Faculty model
class Faculty(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, primary_key=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.abbreviation

# AllocationEvent model
class AllocationEvent(models.Model):
    event_name = models.CharField(max_length=255)
    status = models.CharField(max_length=6, choices=EventStatus.choices(), default='open')
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    eligible_batch = models.CharField(max_length=255)  # e.g., "2026"
    eligible_branch = models.CharField(max_length=255)  # e.g., "IT,AI"
    eligible_faculties = models.ManyToManyField(Faculty, related_name='eligible_faculty_events')

    def __str__(self):
        return self.event_name

# ChoiceList model
class ChoiceList(models.Model):
    event = models.ForeignKey(AllocationEvent, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    preference_list = models.JSONField()  # stores list of dictionaries e.g., [{"choiceNo": 1, "facultyAbbrv": "CS"}]
    current_allocation = models.ForeignKey(Faculty, null=True, blank=True, on_delete=models.SET_NULL, related_name='allocated_choices')
    current_index = models.IntegerField(default=1)
    cluster_number = models.IntegerField()

    def __str__(self):
        return f'{self.student.user.username} - {self.event.event_name}'

# Clashes model
class Clashes(models.Model):
    event = models.ForeignKey(AllocationEvent, on_delete=models.CASCADE)
    cluster_id = models.IntegerField()
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    preference_id = models.IntegerField()
    list_of_students = models.ManyToManyField('Student', related_name='clashing_students')  # A many-to-many relationship with the Student model
    selected_student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f'Clash in {self.event.event_name} - Cluster {self.cluster_id}'
