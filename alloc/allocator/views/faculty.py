from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Role, Faculty

@authorize_resource
def add_faculty(request):
    if request.method == "POST":
        user_id = request.POST["user_id"]
        user = MyUser.objects.get(id=user_id)
        abbreviation = request.POST["abbreviation"]

        Faculty.objects.create_faculty(user=user, abbreviation=abbreviation)

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
        all_users = MyUser.objects.all()
        return render(request, "allocator/add_faculty.html", {
            "users": all_users
        })
