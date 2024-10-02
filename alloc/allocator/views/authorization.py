from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Role
from django.db import IntegrityError
from django.contrib import messages
from ..email_sender import send_mail_page
from django.contrib.auth import authenticate, login, logout

import random

import logging

logger = logging.getLogger('django')


@authorize_resource
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        edu_email = request.POST["nitkMailID"]
        email = request.POST["email"]

        try:
            user = MyUser.objects.create_user(edu_email=edu_email, email=email, username=username)
            user.save()
            logger.info(f"User: {user.username} registered")
        except IntegrityError as e:
            logger.exception(f"User: {user.username} already registered")
            messages.error(request, "Roll number already exists.")
            return HttpResponseRedirect(reverse('register'))

        return HttpResponseRedirect(reverse('home'))
    else:
        return render(request, "allocator/register.html")

def generate_otp():
    return random.randint(100000, 999999)


def login_view(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            next = request.POST["next"]
            user = MyUser.objects.get(edu_email=edu_email)

            if user:
                admin_role = Role.objects.get(role_name='admin')
                if admin_role in user.roles.all():
                    return render(request, "allocator/login_password.html", {
                    "next": next,
                    "edu_email": edu_email
                    })
                else:
                    user.otp=None
                    user.save()
                    user.otp=generate_otp()
                    user.save()
                    send_mail_page(user.edu_email, 'Login OTP', f"Dear User,\nYour Login OTP(One Time Password) is {user.otp}. Kindly use this OTP to login.\nThank you.\nB.Tech Major Project Team.")
                    return render(request, "allocator/login_otp.html", {
                        "message" : "OTP has been sent to your email. Please enter it below.",
                        "next": next,
                        "edu_email": edu_email
                    })
            else :
                return render(request, "allocator/login.html", {
                    "message" : "Invalid username."
                })

        else :
            return render(request, "allocator/login.html")
    else :
        return HttpResponseRedirect(reverse('home'))

def otp(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            otp = request.POST["otp_entry"]
            next = request.POST["next"]
            user = MyUser.objects.get(edu_email=edu_email)

            print(user.otp)
            print(type(user.otp))

            if user and user.otp == otp:
                if user.is_registered:
                    return render(request, "allocator/login_password.html", {
                        "next": next,
                        "edu_email": edu_email
                    })
                else:
                    return render(request, "allocator/login_create_password.html", {
                        "next": next,
                        "edu_email": edu_email
                    })

            else :
                return render(request, "allocator/login.html", {
                    "message" : "Invalid OTP. Kindly restart the login.",
                    "next": next
                })

        else :
            return render(request, "allocator/login.html")
    else :
        return HttpResponseRedirect(reverse('home'))

def validatePassword(password):
    return True

def create_password(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            password = request.POST["password"]
            repassword = request.POST["repassword"]
            next_url = request.POST["next"]
            user = MyUser.objects.get(edu_email=edu_email)
            if password == repassword:
                if validatePassword(password):
                    user.otp=None
                    user.set_password(password)
                    user.is_registered = True
                    user.save()
                    return HttpResponseRedirect(next_url if next_url else reverse('home'))
                else:
                    return render(request, "allocator/login.html", {
                        "message" : "Invalid password format. Kindly read the rules and try again.",
                        "next": next_url
                    })
            else:
                return render(request, "allocator/login.html", {
                    "message" : "Passwords don't match. Kindly try again.",
                    "next": next_url
                })
        else :
            return render(request, "allocator/login.html")
    else :
        return HttpResponseRedirect(reverse('home'))

def complete_login(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            password = request.POST["password"]
            next_url = request.POST["next"]
            user = authenticate(request, edu_email=edu_email, password=password)

            if user is not None :
                login(request, user)
                user.otp=None
                user.save()
                logger.info(f"User: {user.username} logged in")
                return HttpResponseRedirect(next_url if next_url else reverse('home'))
                # if(next_url==''):
                #     return HttpResponseRedirect(reverse(home))
                # else:
                #     return HttpResponseRedirect(next_url)
            else:
                ############################## Need to change this #######################################
                logger.exception(f"IP: {request.META.get('REMOTE_ADDR')} failed to login")
                return render(request, "allocator/login.html", {
                    "message" : "Invalid login attempt. Kindly try again.",
                    "next": next_url
                })
                # messages.error(request, "Invalid login attempt. Kindly try again.")
                # return HttpResponseRedirect(reverse(login_view))

        else :
            return render(request, "allocator/login.html")
    else :
        return HttpResponseRedirect(reverse('home'))


def logout_view(request) :
    if request.user.is_authenticated:
            logger.info(f"User: {request.user.username} logged out")
            logout(request)
            return HttpResponseRedirect(reverse('login'))
