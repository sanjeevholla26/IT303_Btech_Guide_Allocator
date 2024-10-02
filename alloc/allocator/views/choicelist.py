from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import AllocationEvent, Faculty, Student, ChoiceList, MyUser
from ..email_sender import send_mail_page

def choice_locking_message(choice):
    message = "Dear student,\n"
    preferences = ""
    for pref in choice.preference_list:
        get_u = MyUser.objects.get(id=pref["facultyID"])
        get_fac = Faculty.objects.get(user=get_u)
        preferences = preferences + f"{pref['choiceNo']} : {get_fac}\n"
    message = message + f"\nYou have successfully locked the below choices for the event {choice.event.event_name}:\n{preferences}\nWe wish you the best for your allocations."
    message = message + "\nThank you,\nBTech Major Project Allocation Team"
    return message
    

# @authorize_resource
def create_or_edit_choicelist(request, id):
    e = AllocationEvent.objects.get(id=id)
    user_branch = request.user.student.branch
    user_batch = request.user.student.academic_year

    if not user_branch == e.eligible_branch or user_batch == e.eligible_batch:
        return HttpResponseRedirect(reverse('home'))
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
                return HttpResponseRedirect(reverse('events'))
            else:
                curr_student = Student.objects.get(user=request.user)
                get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
                get_prev_choice.is_locked=True
                get_prev_choice.save()
                send_mail_page(curr_student.user.edu_email, "Choice Locking", choice_locking_message(get_prev_choice))
                return HttpResponseRedirect(reverse('events'))
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
