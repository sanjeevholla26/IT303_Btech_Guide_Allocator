from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
import datetime
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

def home(request) :
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse(register))
    else :
        return render(request, "allocator/home.html")

# @method_decorator(csrf_protect, name='dispatch')
def register(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            username = request.POST["username"]
            email = request.POST["email"]
            password = request.POST["password"]
            confirm_password = request.POST["confirm_password"]

            if password != confirm_password :
                return render(request, "allocator/register.html", {
                    "message" : "Password does not match"
                })

            try :
                user = User.objects.create_user(username, email, password)
                user.save()

            except IntegrityError:
                return render(request, "allocator/register.html", {
                    "message" : "A user with that username already exist"
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
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)

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
