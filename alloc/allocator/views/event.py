from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import AllocationEvent, Faculty
from django.shortcuts import get_object_or_404
from django.contrib import messages



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
        return HttpResponseRedirect(reverse('home'))


@authorize_resource
def admin_all_events(request):
    if request.method == "GET":
        all_events = AllocationEvent.objects.all()
        return render(request, "allocator/admin_all_events.html", {
            "events" : all_events,
        })
    else:
        return HttpResponseRedirect(reverse('home'))

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
        return HttpResponseRedirect(reverse('home'))

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
        return HttpResponseRedirect(reverse('home'))
