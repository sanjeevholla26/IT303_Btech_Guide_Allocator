from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
# from django.contrib.auth.models import User, MyUser
from .models import MyUser, Role, Student, Faculty, AllocationEvent, ChoiceList, Clashes
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
import functools
import traceback
from django.contrib import messages

from .allocation_function import allocate

def authorize_resource(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to log in to access this page.")
            return HttpResponseRedirect(reverse(login_view))
        # Capture the name of the action (function name)
        action_name = func.__name__

        # Capture the app name from the module
        module_name = func.__module__  # This returns the full module path (e.g., 'allocator.views')
        app_name = module_name.split('.')[0]  # Extract the app name by splitting the module path
        all_actions = Role.get_all_permissions(request.user)
        if not app_name in all_actions or not action_name in all_actions[app_name]:
            messages.error(request, "You do not have permission to access this page.")
            return HttpResponseRedirect(reverse(home))
        # Call the original function
        return func(request, *args, **kwargs)

    return wrapper

def home(request) :
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse(login_view))
    else :
        return render(request, "allocator/home.html")

# @method_decorator(csrf_protect, name='dispatch')
@authorize_resource
def register(request):
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

        return HttpResponseRedirect(reverse(home))
    else:
        return render(request, "allocator/register.html")

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

@authorize_resource
def add_student(request):
    if request.method == "POST":
        user_id = request.POST["user_id"]
        user = MyUser.objects.get(id=user_id)
        cgpa = request.POST["cgpa"]
        academic_year = request.POST["aca_year"]
        branch = request.POST["branch"]

        new_student = Student(
            user = user,
            cgpa = cgpa,
            academic_year = academic_year,
            branch = branch
        )
        new_student.save()

        student_role, created = Role.objects.get_or_create(role_name="student")
        student_role.users.add(user)
        student_role.save()

        return HttpResponseRedirect(reverse(home))

    else:
        all_users = MyUser.objects.all()
        return render(request, "allocator/add_student.html", {
            "users": all_users
        })

@authorize_resource
def add_faculty(request):
    if request.method == "POST":
        user_id = request.POST["user_id"]
        user = MyUser.objects.get(id=user_id)
        abbreviation = request.POST["abbreviation"]

        new_faculty = Faculty(
            user = user,
            abbreviation = abbreviation
        )
        new_faculty.save()

        faculty_role, created = Role.objects.get_or_create(role_name="faculty")
        faculty_role.users.add(user)
        faculty_role.save()

        return HttpResponseRedirect(reverse(home))

    else:
        all_users = MyUser.objects.all()
        return render(request, "allocator/add_faculty.html", {
            "users": all_users
        })

@authorize_resource
def add_event(request):
    if request.method == "POST":
        user = request.user
        name = request.POST.get("name")
        start_datetime = request.POST.get("start_datetime")
        end_datetime = request.POST.get("end_datetime")
        batch = request.POST.get("batch")
        branch = request.POST.get("branch")
        faculties = request.POST.getlist("faculties")  # Use getlist to retrieve multiple selected IDs
        # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",faculties)
        # Create the new AllocationEvent instance
        new_event = AllocationEvent(
            owner=user,  # Set the owner to the current user
            event_name=name,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            eligible_batch=batch,
            eligible_branch=branch
        )

        new_event.save()  # Save the AllocationEvent instance first to get an ID

        # Now add the selected faculties to the ManyToMany field
        new_event.eligible_faculties.set(faculties)  # Set the ManyToMany relationship

        return HttpResponseRedirect(reverse('home'))  # Redirect after saving
    else:
        all_users = Faculty.objects.all()
        return render(request, "allocator/add_event.html", {
            "faculties": all_users
        })

@authorize_resource
def all_events(request):
    if request.method == "GET":
        active_events = AllocationEvent.active_events()
        user_branch = request.user.student.branch
        user_batch = request.user.student.academic_year

        eligible_events = active_events.filter(eligible_batch=user_batch, eligible_branch=user_branch)

        return render(request, "allocator/all_events.html", {
            "events" : eligible_events
        })
    else:
        return HttpResponseRedirect(reverse(home))

@authorize_resource
def event(request, id):
    e = AllocationEvent.objects.get(id=id)
    user_branch = request.user.student.branch
    user_batch = request.user.student.academic_year

    if not user_branch == e.eligible_branch or user_batch == e.eligible_batch:
        return HttpResponseRedirect(reverse(home))
    else:
        if request.method == "POST":
            preference_list = []
            for i in range(1, e.eligible_faculties.count() + 1):
                faculty_id = request.POST.get(f'faculty_{i}')
                if faculty_id:
                    preference_list.append({"choiceNo": i, "facultyID": faculty_id})
            choice_list = ChoiceList.objects.create(
                event=e,
                student=request.user.student,
                preference_list=preference_list,
                cluster_number=1  # Set this based on your logic
            )

            return HttpResponseRedirect(reverse(all_events))
        else:
            preference_range = range(1, e.eligible_faculties.count() + 1)
            curr_student = Student.objects.get(user=request.user)
            try:
                get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
            except ChoiceList.DoesNotExist:
                get_prev_choice = None
            preferences = {}
            if get_prev_choice:
                for pref in get_prev_choice.preference_list:
                    get_u = MyUser.objects.get(id=pref["facultyID"])
                    get_fac = Faculty.objects.get(user=get_u)
                    preferences[pref["choiceNo"]] = get_fac
            return render(request, "allocator/event.html", {'event': e, 'preference_range': preference_range, 'filled_preference': preferences, 'filled_choice': get_prev_choice})

@authorize_resource
def create_cluster(request, id):
    get_event = AllocationEvent.objects.get(id=id)
    if request.method == "POST":
        # Use .count() to get the number of eligible faculties (many-to-many field)
        total_profs = get_event.eligible_faculties.count()

        # Get the list of ChoiceList objects sorted by student CGPA in descending order
        students_choice_list = ChoiceList.objects.filter(event=get_event).order_by('-student__cgpa', '-student__user__username')

        max_cluster_num = 0

        for i, choice in enumerate(students_choice_list):
            # Calculate the cluster number (integer division)
            cluster_no = (i // total_profs) + 1
            max_cluster_num = max(max_cluster_num, cluster_no)
            choice.cluster_number = cluster_no
            choice.save()

        get_event.cluster_count = max_cluster_num
        get_event.save()

        # return HttpResponseRedirect(reverse(admin_all_events))
        return HttpResponseRedirect(reverse(create_cluster, args=(id, )))
    else:
        clusters = {}
        students_choice_list = ChoiceList.objects.filter(event=get_event)
        if get_event.cluster_count != 0:
            students_choice_list = ChoiceList.objects.filter(event=get_event)
            for choice in students_choice_list:
                cluster_no = choice.cluster_number
                if cluster_no not in clusters:
                    clusters[cluster_no] = []
                clusters[cluster_no].append(choice)
        return render(request, "allocator/create_cluster.html", {
            "event" : get_event,
            "clusters": clusters,
        })

@authorize_resource
def run_allocation(request, id):
    if request.method == "POST":
        allocate(id)
        return HttpResponseRedirect(reverse(create_cluster, args=(id, )))
    else:
        return HttpResponseRedirect(reverse(home))

@authorize_resource
def reset_allocation(request, id):
    if request.method == "POST":
        get_event = AllocationEvent.objects.get(id=id)
        students_choice_list = ChoiceList.objects.filter(event=get_event)
        for s in students_choice_list:
            s.current_allocation = None
            s.current_index = 1
            s.save()

        clashes = Clashes.objects.filter(event=get_event)
        for c in clashes:
            c.is_processed = True
            c.save()
        return HttpResponseRedirect(reverse(create_cluster, args=(id, )))
    else:
        return HttpResponseRedirect(reverse(home))

@authorize_resource
def admin_all_events(request):
    if request.method == "GET":
        all_events = AllocationEvent.objects.all()
        return render(request, "allocator/admin_all_events.html", {
            "events" : all_events,
        })
    else:
        return HttpResponseRedirect(reverse(home))


@authorize_resource
def show_all_clashes(request):
    if request.method == "GET":
        get_fac = Faculty.objects.get(user=request.user)
        all_clashes = Clashes.objects.filter(faculty=get_fac, selected_student=None, is_processed=False)

        return render(request, "allocator/all_clashes.html", {
            "clashes": all_clashes
        })

    else:
        return HttpResponseRedirect(reverse(home))

@authorize_resource
def resolve_clash(request, id):
    clash = Clashes.objects.get(id=id)
    students = clash.list_of_students.all()

    preferences = []

    for s in students:
        chList = ChoiceList.objects.get(event=clash.event, student=s).printChoiceList()
        preferences.append([s.user.username, s.cgpa, chList])

    if request.method == "GET":
        return render(request, "allocator/clash.html", {
            "clash": clash,
            "preferenceList": preferences
        })
    else:
        get_user_id = request.POST.get("student_id")
        user = MyUser.objects.get(id=get_user_id)
        selected_student = Student.objects.get(user=user)

        clash.selected_student = selected_student
        clash.save()
        allocate(clash.event.id)
        return HttpResponseRedirect(reverse(show_all_clashes))
