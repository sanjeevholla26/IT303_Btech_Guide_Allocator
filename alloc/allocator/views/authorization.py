from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Role
from django.db import IntegrityError
from django.contrib import messages
from ..email_sender import send_mail_page
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.urls import reverse
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from alloc.settings import QUICK_LOGIN

import random

## Redundant Function which is not being used. Replaced by add_student and add_faculty
# @authorize_resource
# def register(request):
#     if request.method == "POST":
#         username = request.POST["username"]
#         edu_email = request.POST["nitkMailID"]
#         email = request.POST["email"]
#         try:
#             user = MyUser.objects.create_user(edu_email=edu_email, email=email, username=username)
#             user.save()
#         except IntegrityError as e:
#             messages.error(request, "Roll number already exists.")
#             return HttpResponseRedirect(reverse('register'))

#         return HttpResponseRedirect(reverse('home'))
#     else:
#         return render(request, "allocator/register.html")

def generate_otp():
    return random.randint(100000, 999999)

def generate_captcha():
    captcha_key = CaptchaStore.generate_key()
    captcha_image = captcha_image_url(captcha_key)
    result = ""
    if QUICK_LOGIN:
        result = CaptchaStore.objects.get(hashkey=captcha_key).response
    return [captcha_key, captcha_image, result]

def send_to_otp(request, user, next_url):
    user.otp = None
    user.save()
    user.otp = generate_otp()
    user.save()
    send_mail_page(user.edu_email, 'Login OTP', f"Dear User,\nYour Login OTP(One Time Password) is {user.otp}. Kindly use this OTP to login.\nThank you.\nB.Tech Major Project Team.")
    return render(request, "allocator/login_otp.html", {
            "message": "OTP has been sent to your email. Please enter it below.",
            "next": next_url,
            "edu_email": user.edu_email
        })

def login_view(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            edu_email = request.POST["edu_email"]
            next_url = request.POST.get("next", "")
            captcha_key = request.POST.get('captcha_key')
            captcha_response = request.POST.get('captcha')

            try:
                captcha = CaptchaStore.objects.get(hashkey=captcha_key)
                print(f"My resp:{captcha_response} Actual exp:{captcha.response}")
                if captcha.response == captcha_response:
                    try:
                        user = MyUser.objects.get(edu_email=edu_email)
                        if user:
                            if user.is_registered:
                                return render(request, "allocator/login_password.html", {
                                    "next": next_url,
                                    "edu_email": edu_email
                                })
                            else:
                                if QUICK_LOGIN:
                                    return render(request, "allocator/login_create_password.html", {
                                        "next": next_url,
                                        "edu_email": edu_email
                                    })
                                else:
                                    return send_to_otp(request, user, next_url)
                        else:
                            messages.error(request, "Invalid username.")
                            return HttpResponseRedirect(reverse(login_view))
                            
                    except MyUser.DoesNotExist:
                        messages.error(request, "User does not exist.")
                        return HttpResponseRedirect(reverse(login_view))
                        
                else:
                    messages.error(request, "Invalid captcha. Please try again.")
                    return HttpResponseRedirect(reverse(login_view))
                    
            except CaptchaStore.DoesNotExist:
                messages.error(request, "Captcha validation error. Please try again.")
                return HttpResponseRedirect(reverse(login_view))

        else:
            return render(request, "allocator/login.html", {
                'captcha': generate_captcha()
            })
    else:
        return HttpResponseRedirect(reverse('home'))
    

def otp(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            otp = request.POST["otp_entry"]
            next_url = request.POST["next"]
            user = MyUser.objects.get(edu_email=edu_email)

            if user and user.otp == otp:
                if user.is_registered:
                    login(request, user)
                    return HttpResponseRedirect(next_url if next_url else reverse('home'))
                else:
                    return render(request, "allocator/login_create_password.html", {
                        "next": next_url,
                        "edu_email": edu_email
                    })

            else :
                messages.error(request, "Invalid OTP. Kindly restart the login.")
                return HttpResponseRedirect(reverse(login_view))
        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

def validatePassword(password):
    # Perform regex checks on the password validity
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
                    authenticate(request, edu_email=edu_email, password=password)
                    login(request, user)
                    return HttpResponseRedirect(next_url if next_url else reverse('home'))
                else:
                    return render(request, "allocator/login_create_password.html", {
                        "message" : "Invalid password format. Kindly read the rules and try again.",
                        "next": next_url,
                        "edu_email": edu_email
                    })
            else:            
                return render(request, "allocator/login_create_password.html", {
                    "message" : "Passwords don't match.",
                    "next": next_url,
                    "edu_email": edu_email
                })
        else :
            return HttpResponseRedirect(reverse(login_view))
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
                admin_role = Role.objects.get(role_name='admin')
                if admin_role in user.roles.all() or QUICK_LOGIN:
                    login(request, user)
                    return HttpResponseRedirect(next_url if next_url else reverse('home'))
                else:
                    return send_to_otp(request, user, next_url)
            else:
                messages.error(request, "Wrong Password. Kindly try again.")
                return HttpResponseRedirect(reverse(login_view))

        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

@authorize_resource
def logout_view(request) :
    if request.user.is_authenticated:
            logout(request)
            return HttpResponseRedirect(reverse('login'))
