from django.db import models

class StudentManager(models.Manager):
    def create_student(self, user, cgpa, academic_year, branch):
        student = self.create(
            user=user,
            cgpa=cgpa,
            academic_year=academic_year,
            branch=branch
        )

        return student

    def update_student(self, user, cgpa=None, academic_year=None, branch=None):
        try:
            student = self.get(user=user)
        except self.model.DoesNotExist:
            raise ValueError(f"No student found with user {user}")

        if cgpa is not None:
            student.cgpa = cgpa

        if academic_year is not None:
            student.academic_year = academic_year

        if branch is not None:
            student.branch = branch

        student.save()
        return student
