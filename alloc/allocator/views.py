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

def authorize_resource(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        # Capture the name of the action (function name)
        action_name = func.__name__

        # Capture the app name from the module
        module_name = func.__module__  # This returns the full module path (e.g., 'allocator.views')
        app_name = module_name.split('.')[0]  # Extract the app name by splitting the module path

        all_actions = Role.get_all_permissions(request.user)
        if not app_name in all_actions or not action_name in all_actions[app_name]:
            return HttpResponseRedirect(reverse(home))
        # Call the original function
        return func(request, *args, **kwargs)

    return wrapper

def home(request) :
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse(login))
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

        return HttpResponseRedirect(reverse(home))

    else:
        all_users = MyUser.objects.all()
        return render(request, "allocator/add_student.html", {
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
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",faculties)
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
                print("########################", faculty_id)
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
            return render(request, "allocator/event.html", {'event': e, 'preference_range': preference_range})

@authorize_resource
def create_cluster(request, id):
    get_event = AllocationEvent.objects.get(id=id)
    if request.method == "POST":
        # Use .count() to get the number of eligible faculties (many-to-many field)
        total_profs = get_event.eligible_faculties.count()

        # Get the list of ChoiceList objects sorted by student CGPA in descending order
        students_choice_list = ChoiceList.objects.filter(event=get_event).order_by('-student__cgpa')

        max_cluster_num = 0

        for i, choice in enumerate(students_choice_list):
            # Calculate the cluster number (integer division)
            cluster_no = (i // total_profs) + 1
            max_cluster_num = max(max_cluster_num, cluster_no)
            choice.cluster_number = cluster_no
            choice.save()

        get_event.cluster_count = max_cluster_num
        get_event.save()

        return HttpResponseRedirect(reverse(admin_all_events))
    else:
        return render(request, "allocator/create_cluster.html", {
            "event" : get_event
        })

@authorize_resource
def run_allocation(request, id):
    get_event = AllocationEvent.objects.get(id=id)
    if request.method == "POST":
        prof_count = get_event.eligible_faculties.count()
        participating_profs = get_event.eligible_faculties

        clashes = Clashes.objects.get(event=get_event)

        for clusterID in range(0, get_event.cluster_count+1):

            choice_lists = [s for s in get_event if s.cluster_number==clusterID]

            unresolvedClashes = [c for c in clashes if not c.is_processed and c.clusterID == clusterID and not c.selected_students]
            newlyResolvedClashes = [c for c in clashes if not c.is_processed and c.clusterID == clusterID and c.selected_students]

            for c in newlyResolvedClashes:
                for s in choice_lists:
                    if s.student in c.list_of_students:
                        if s.student == c.selected_student:
                            s.current_allocation = c.faculty
                        else:
                            s.current_index += 1

            profAllotted = {prof: [] for prof.user.id in participating_profs}
            lastPrefTaken = prof_count + 1
            allotted = 0
            for choice in choice_lists:
                if choice.current_allocation:
                    profAllotted[choice.current_allocation.user.id].append(choice)
                    allotted += 1
                else:
                    lastPrefTaken = min(lastPrefTaken, choice.current_index)

            if unresolvedClashes:
                continue
            
            if allotted == len(choice_lists):
                continue

            for current_pref in range(lastPrefTaken, prof_count):
                tempProf = {prof: [] for prof.user.id in participating_profs}
                clashes_occured = False
                for choice in choice_lists:
                    pref_prof = choice.preference_list[current_pref].facultyID
                    if choice.current_allocation or len(profAllotted[pref_prof])!=0:
                        continue
                    tempProf[pref_prof].append(choice)
                for prof, students in tempProf.items():
                    if len(students) > 1:
                        Clashes.objects.create(
                        event = get_event,
                        cluster_id = clusterID,
                        faculty = Faculty.objects.get(id=prof),
                        preference_id = current_pref,
                        list_of_students = students,
                        selected_student = None
                    )
                        clashes_occured=True
                    elif len(students) == 1:
                        students[0].current_allocation = prof
                        profAllotted[prof].append(students[0])
                        allotted += 1

                if allotted == len(choice_lists):
                    break

                if clashes_occured:
                    break

        return HttpResponseRedirect(reverse(admin_all_events))
    else:
        return render(request, "allocator/create_cluster.html", {
            "event" : get_event
        })


@authorize_resource
def admin_all_events(request):
    if request.method == "GET":
        all_events = AllocationEvent.objects.all()

        return render(request, "allocator/admin_all_events.html", {
            "events" : all_events,
        })
    else:
        return HttpResponseRedirect(reverse(home))
