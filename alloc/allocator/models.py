from django.contrib.auth.models import AbstractUser
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

# User model
class User(AbstractUser):
    email_id = models.EmailField(unique=True)  # Override to make email unique
    recovery_email_id = models.EmailField(null=True, blank=True)
    phone_no = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.username

# Student model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    academic_year = models.IntegerField()  # e.g., 2024
    branch = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.username} - {self.branch}'

# Faculty model
class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.abbreviation

# AllocationEvent model
class AllocationEvent(models.Model):
    event_name = models.CharField(max_length=255)
    status = models.CharField(max_length=6, choices=EventStatus.choices(), default='open')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
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
    list_of_students = models.ManyToManyField('Student', related_name='clashes')  # A many-to-many relationship with the Student model
    selected_student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f'Clash in {self.event.event_name} - Cluster {self.cluster_id}'
