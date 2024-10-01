from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
# from django.contrib.auth.models import User, MyUser
from .models import MyUser, Role, Student, Faculty, AllocationEvent, ChoiceList, Clashes, Permission
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
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from io import BytesIO
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

from .allocation_function import allocate

from datetime import timedelta

CLASH_TIMEOUT = timedelta(days=3)

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
                next_url = request.POST.get('next')
                return HttpResponseRedirect(next_url if next_url else reverse('home'))
                # if(next_url==''):
                #     return HttpResponseRedirect(reverse(home))
                # else:
                #     return HttpResponseRedirect(next_url)
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
def add_permissions(request):
    if request.method == "POST":
        new_permissions = request.POST["permissions"]
        app_name = request.POST["app_name"]
        roles_list = request.POST.getlist("roles_list") 


        new_perms = Permission(actions=new_permissions, app_name=app_name)
        new_perms.save()

        new_perms.role.set(roles_list)

        return HttpResponseRedirect(reverse(home))

    else:
        all_roles = Role.objects.all()
        return render(request, "allocator/add_permissions.html", {
            "roles": all_roles
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
        faculties = request.POST.getlist("faculties")
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
def edit_event(request, id):
    event = get_object_or_404(AllocationEvent, id=id)  # Get the event instance
    if request.method == 'POST':
        # Handle form submission
        event.event_name = request.POST.get('name')
        event.start_datetime = request.POST.get('start_datetime')
        event.end_datetime = request.POST.get('end_datetime')
        event.eligible_batch = request.POST.get('batch')
        event.eligible_branch = request.POST.get('branch')
        faculty_ids = request.POST.getlist('faculties')
        event.eligible_faculties.set(faculty_ids)
        
        event.save()
        return redirect('home')  # Redirect to a success page or home
    else:
        # For GET request, render the form with existing values
        faculties = Faculty.objects.all()  # Retrieve all faculties
        return render(request, 'allocator/edit_event.html', {
            'event': event,
            'faculties': faculties
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
            action = request.POST.get('action')
            if action != 'lock':
                preference_list = []
                curr_student = Student.objects.get(user=request.user)
                for i in range(1, e.eligible_faculties.count() + 1):
                    faculty_id = request.POST.get(f'faculty_{i}')
                    if faculty_id:
                        preference_list.append({"choiceNo": i, "facultyID": faculty_id})
                try:
                    get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
                    get_prev_choice.preference_list = preference_list
                    get_prev_choice.save()
                except ChoiceList.DoesNotExist:
                    choice_list = ChoiceList.objects.create(
                        event=e,
                        student=request.user.student,
                        preference_list=preference_list,
                        cluster_number=1  # Set this based on your logic
                    )
                return HttpResponseRedirect(reverse(all_events))
            else:
                curr_student = Student.objects.get(user=request.user)
                get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
                get_prev_choice.is_locked=True
                get_prev_choice.save()
                return HttpResponseRedirect(reverse(all_events))
        else:
            preference_range = range(1, e.eligible_faculties.count() + 1)
            curr_student = Student.objects.get(user=request.user)
            try:
                get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
            except ChoiceList.DoesNotExist:
                get_prev_choice = None
                
            if get_prev_choice:
                locked = ChoiceList.objects.get(event=e, student=curr_student).is_locked
            else:
                locked = False
            preferences = {}
            if get_prev_choice:
                for pref in get_prev_choice.preference_list:
                    get_u = MyUser.objects.get(id=pref["facultyID"])
                    get_fac = Faculty.objects.get(user=get_u)
                    preferences[pref["choiceNo"]] = get_fac
            return render(request, "allocator/event.html", {'event': e, 'preference_range': preference_range, 'filled_preference': preferences, 'filled_choice': get_prev_choice,'locked':locked})

@authorize_resource
def create_cluster(request, id):
    get_event = AllocationEvent.objects.get(id=id)
    if request.method == "POST":
        # Use .count() to get the number of eligible faculties (many-to-many field)
        total_profs = get_event.eligible_faculties.count()

        # Get the list of ChoiceList objects sorted by student CGPA in descending order
        students_choice_list = ChoiceList.objects.filter(event=get_event).order_by('-student__cgpa', 'student__user__username')

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
        students_choice_list = ChoiceList.objects.filter(event=get_event).order_by('-student__cgpa', 'student__user__username')
        if get_event.cluster_count != 0:
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

@login_required
@authorize_resource
def resolve_clash(request, id):
    clash = Clashes.objects.get(id=id)
    students = clash.list_of_students.all()

    if(clash.faculty.user!=request.user):
        messages.error(request, "You cannot access this page.")
        return HttpResponseRedirect(reverse(show_all_clashes))

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

@authorize_resource
def admin_show_clash(request):
    if request.method == "GET":
         # Assuming CLASH_TIMEOUT is a timedelta object
        timeout_limit = now() - CLASH_TIMEOUT

        # Filter clashes that are unprocessed and created more than CLASH_TIMEOUT ago
        all_clashes = Clashes.objects.filter(selected_student=None, is_processed=False, created_datetime__lte=timeout_limit)

        return render(request, "allocator/admin_show_clash.html", {
            "clashes": all_clashes
        })

    else:
        return HttpResponseRedirect(reverse(home))

@authorize_resource
def admin_resolve_clash(request, id):
    clash = Clashes.objects.get(id=id)
    students = clash.list_of_students.all()

    selected_student = students.order_by('-cgpa').first()

    clash.selected_student = selected_student
    clash.save()
    allocate(clash.event.id)
    return HttpResponseRedirect(reverse(admin_show_clash))

@authorize_resource
def eligible_events(request):
    if request.method == "GET":
        fac = Faculty.objects.get(user=request.user)
        get_eligible_events = fac.eligible_faculty_events.all()

        return render(request, "allocator/eligible_events.html", {
            "eligible_events": get_eligible_events
        })
    else:
        messages.error(request, "Invalid request method")
        return HttpResponseRedirect(reverse(home))

@authorize_resource
def event_results(request, id):
    if request.method == "GET":
        event = AllocationEvent.objects.get(id=id)
        get_fac = Faculty.objects.get(user=request.user)
        allocated_choices = get_fac.allocated_choices.filter(event=event)

        return render(request, "allocator/event_result.html", {
            "allocated_choices": allocated_choices
        })
    else:
        messages.error(request, "Invalid request method")
        return HttpResponseRedirect(reverse(home))

    
@authorize_resource
def generate_pdf(request, id):
    # Fetch all students from the database
    allocations = ChoiceList.objects.all()

    for allocation in allocations:
        if allocation.event.id != id:
            continue

        # Create a PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Get the default stylesheet and customize heading
        styles = getSampleStyleSheet()
        heading_style = styles['Heading1']  # Use 'Heading1' style for large font
        heading_style.alignment = 1  # Center alignment
        heading_style.fontSize = 24  # Large font size
        heading_style.textColor = colors.HexColor("#2E8B57")  # Dark green heading color

        # Create the heading paragraph
        heading = Paragraph("PROJECT ALLOCATION DETAILS", heading_style)

        # Prepare the student details in two columns: field name and field value
        data = [
            ['Field', 'Details'],  # Table header
            ['Name', allocation.student.user.username],  # Student's name
            ['Professor', allocation.current_allocation.user.username],  # Professor name
            ['Email', allocation.student.user.email],  # Email address
            ['Date of Allocation', datetime.now().strftime("%Y-%m-%d")]  # Allocation date
        ]

        # Create the table with two columns (Field and Details)
        table = Table(data, colWidths=[2*inch, 4*inch])
        
        # Define table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)

        # Build the PDF with the heading and the table
        elements = []
        elements.append(heading)
        elements.append(Spacer(1, 0.5*inch))  # Add some space between heading and table
        elements.append(table)
        doc.build(elements)

        # Get the PDF content from the buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create the email for the specific student
        email = EmailMessage(
            subject='Your Project Allotment Details',
            body=f"Dear {data[1][1]},\n\nPlease find attached your project allotment details.",
            from_email='btechalloc@gmail.com',
            to=[data[3][1]],  # Send to the student's email
        )

        # Attach the personalized PDF
        email.attach('project_allotment.pdf', pdf, 'application/pdf')

        # Send the email
        email.send()

    # Return a response to confirm that emails have been sent

    
    messages.success(request, "Allocation reports have been sent successfully to all students."),
    return HttpResponseRedirect(reverse(create_cluster, args=(id,)))
    
