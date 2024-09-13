from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
# from django.contrib.auth.models import User, MyUser
from .models import MyUser
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
import datetime
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login
import traceback

def home(request) :
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse(login))
    else :
        return render(request, "allocator/home.html")

# @method_decorator(csrf_protect, name='dispatch')

def register(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST["username"]
            eduMailID = request.POST["nitkMailID"]
            email = request.POST["email"]
            password = request.POST["password"]
            confirm_password = request.POST["confirm_password"]

            if password != confirm_password:
                return render(request, "allocator/register.html", {
                    "message": "Passwords do not match."
                })

            if not eduMailID.endswith("@nitk.edu.in"):
                return render(request, "allocator/register.html", {
                    "message": "Kindly enter your NITK edu mail ID."
                })
            try:
                user = MyUser.objects.create_user(eduMailID=eduMailID, email=email, username=username, password=password)
                user.save()
            except IntegrityError as e:
                print(traceback.format_exc())  # This will print the full traceback in the console
                return render(request, "allocator/register.html", {
                    "message": f"Integrity Error: {str(e)}. A user with that username or email already exists."
                })

            login(request, user)
            return HttpResponseRedirect(reverse(home))
        else:
            return render(request, "allocator/register.html")
    else:
        return HttpResponseRedirect(reverse(home))

def login_view(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            eduMailID = request.POST["nitkMailID"]
            password = request.POST["password"]
            user = authenticate(request, eduMailID=eduMailID, password=password)

            if user is not None :
                login(request, user)
                return HttpResponseRedirect(reverse(home))
            else :
                return render(request, "allocator/login.html", {
                    "message" : "Invalid username and/or password."
                })

        else :
            return render(request, "allocator/login.html")
    else :
        return HttpResponseRedirect(reverse(home))

def logout_view(request) :
    if request.user.is_authenticated:
            logout(request)
            return HttpResponseRedirect(reverse(login_view))
