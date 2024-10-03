from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Student, Role

import logging

logger = logging.getLogger('django')


@authorize_resource
def add_student(request):
    if request.method == "POST":
        username = request.POST["username"]
        edu_email = request.POST["edu_mail"]
        email = request.POST["email"]
        try:
            user = MyUser.objects.create_user(edu_email=edu_email, email=email, username=username)
            user.save()
        except IntegrityError as e:
            messages.error(request, "Roll number already exists.")
            return HttpResponseRedirect(reverse('add_student'))
        
        cgpa = request.POST["cgpa"]
        academic_year = request.POST["aca_year"]
        branch = request.POST["branch"] 
        has_backlog = request.POST.get("has_backlog") == 'true'
        new_student = Student(
            user = user,
            cgpa = cgpa,
            academic_year = academic_year,
            branch = branch,
            has_backlog = has_backlog
        )
        new_student.save()

        # Student.objects.create_student(user=user, cgpa=cgpa, academic_year=academic_year, branch=branch)
        logger.info(f"User: {user.username} added as Student")

        student_role, created = Role.objects.get_or_create(role_name="student")
        student_role.users.add(user)
        student_role.save()

        return HttpResponseRedirect(reverse('home'))

    else:
        new_student = MyUser.objects.exclude(student__isnull=False).exclude(faculty__isnull=False)
        return render(request, "allocator/add_student.html", {
            "users": new_student
        })
