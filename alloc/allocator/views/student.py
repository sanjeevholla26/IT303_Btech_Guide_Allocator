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
        user_id = request.POST["user_id"]
        user = MyUser.objects.get(id=user_id)
        cgpa = request.POST["cgpa"]
        academic_year = request.POST["aca_year"]
        branch = request.POST["branch"]

        Student.objects.create_student(user=user, cgpa=cgpa, academic_year=academic_year, branch=branch)
        logger.info(f"User: {user.username} added as Student")
        # new_student = Student(
        #     user = user,
        #     cgpa = cgpa,
        #     academic_year = academic_year,
        #     branch = branch
        # )
        # new_student.save()

        student_role, created = Role.objects.get_or_create(role_name="student")
        student_role.users.add(user)
        student_role.save()

        return HttpResponseRedirect(reverse('home'))

    else:
        all_users = MyUser.objects.all()
        return render(request, "allocator/add_student.html", {
            "users": all_users
        })
