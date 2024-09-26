from .models import MyUser, Role, Student, Faculty, AllocationEvent, ChoiceList, Clashes
from django.core.mail import send_mail
from django.conf import settings

def allocate(id):
    get_event = AllocationEvent.objects.get(id=id)
    prof_count = get_event.eligible_faculties.count()
    participating_profs = get_event.eligible_faculties.all()

    clashes = Clashes.objects.filter(event=get_event)
    student_pref_list = ChoiceList.objects.filter(event=get_event)

    for clusterID in range(1, get_event.cluster_count+1):
        choice_lists = []
        choice_lists = [s for s in student_pref_list if s.cluster_number==clusterID]

        unresolvedClashes = [c for c in clashes if not c.is_processed and c.cluster_id == clusterID and not c.selected_student]
        newlyResolvedClashes = [c for c in clashes if not c.is_processed and c.cluster_id == clusterID and c.selected_student]

        for c in newlyResolvedClashes:
            for s in choice_lists:
                if s.student in c.list_of_students.all():
                    if s.student == c.selected_student:
                        s.current_allocation = c.faculty
                        s.save()
                    else:
                        s.current_index += 1
                        s.save()
            c.is_processed = True
            c.save()

        profAllotted = {prof.user.id: [] for prof in participating_profs}
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

        if allotted == len(choice_lists)+1:
            continue

        for current_pref in range(lastPrefTaken, prof_count+1):
            tempProf = {prof.user.id: [] for prof in participating_profs}
            clashes_occured = []
            for choice in choice_lists:
                pref_prof = int(choice.preference_list[current_pref-1]["facultyID"])
                if choice.current_allocation or len(profAllotted[pref_prof])!=0:
                    continue
                tempProf[pref_prof].append(choice)
            for prof, students_choice in tempProf.items():
                get_fac = MyUser.objects.get(id = int(prof))
                if len(students_choice) > 1:
                    new_clash = Clashes.objects.create(
                    event = get_event,
                    cluster_id = clusterID,
                    faculty = Faculty.objects.get(user=get_fac),
                    preference_id = current_pref,
                    selected_student = None
                )
                    new_clash.list_of_students.set([c.student.user.id for c in students_choice])
                    new_clash.save()
                    clashes_occured.append(new_clash)
                elif len(students_choice) == 1:
                    students_choice[0].current_allocation = Faculty.objects.get(user=get_fac)
                    students_choice[0].save()
                    profAllotted[int(prof)].append(students_choice[0])
                    allotted += 1

            if allotted == len(choice_lists):
                break

            if len(clashes_occured)>0:
                prof_clash_handler(clashes_occured)
                break

def email_message(preferences, id):
    message = "Dear Sir/Madam,\nThe below students have clashes:\n"
    for p in preferences:
        message = f"{message} - {p[0]} with a CGPA {p[1]} has the choice list {p[2]}.\n"
    message = f"{message}\nKindly visit http://127.0.0.1:8000/resolve_clash/{id} to resolve the clash within 3 days.\n\nThank you,\nWith regards\nB.Tech Major Project Allocator Team"
    return message

def prof_clash_handler(clashes):
    for c in clashes:
        print(f"Sending a mail to {c.faculty}.")
        students = c.list_of_students.all()
        preferences = []
        for s in students:
            chList = ChoiceList.objects.get(event=c.event, student=s).printChoiceList()
            preferences.append([s.user.username, s.cgpa, chList])
        send_mail_page("nandanramesh.221it045@nitk.edu.in", "Clash", email_message(preferences, c.id))
        # send_mail_page(c.faculty.user.eduMailID, "Clash", email_message(preferences))

def send_mail_page(address, subject, message):
    context = {}
    if address and subject and message:
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
            context['result'] = 'Email sent successfully'
        except Exception as e:
            context['result'] = f'Error sending email: {e}'
    else:
        context['result'] = 'All fields are required'
    print(context)