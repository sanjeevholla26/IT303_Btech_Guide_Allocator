from .models import MyUser, Role, Student, Faculty, AllocationEvent, ChoiceList, Clashes

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
            clashes_occured = False
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
                    clashes_occured=True
                elif len(students_choice) == 1:
                    students_choice[0].current_allocation = Faculty.objects.get(user=get_fac)
                    students_choice[0].save()
                    profAllotted[int(prof)].append(students_choice[0])
                    allotted += 1

            if allotted == len(choice_lists):
                break

            if clashes_occured:
                break


