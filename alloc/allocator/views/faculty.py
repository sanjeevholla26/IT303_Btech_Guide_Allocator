from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Role, Faculty

import logging

logger = logging.getLogger('django')

@authorize_resource
def add_faculty(request):
    if request.method == "POST":
        edu_email = request.POST["edu_mail"]
        email = request.POST["email"]
        username = request.POST["username"]
        try:
            user = MyUser.objects.create_user(edu_email=edu_email, email=email, username=username)
            user.save()
        except IntegrityError as e:
            messages.error(request, "Employee ID already exists.")
            return HttpResponseRedirect(reverse('add_faculty'))
        
        abbreviation = request.POST["abbreviation"]

        Faculty.objects.create_faculty(user=user, abbreviation=abbreviation)

        logger.info(f"User: {user.username} added as Faculty")

        # new_faculty = Faculty(
        #     user = user,
        #     abbreviation = abbreviation
        # )
        # new_faculty.save()

        faculty_role, created = Role.objects.get_or_create(role_name="faculty")
        faculty_role.users.add(user)
        faculty_role.save()

        return HttpResponseRedirect(reverse('home'))

    else:
        new_faculty = MyUser.objects.exclude(faculty__isnull=False).exclude(student__isnull=False)
        return render(request, "allocator/add_faculty.html", {
            "users": new_faculty
        })
