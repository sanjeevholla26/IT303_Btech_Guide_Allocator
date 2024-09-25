from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register, name = "register"),
    path("home/", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("add_student/", views.add_student, name="add_student"),
    path("add_event/", views.add_event, name="add_event"),
    path("events/", views.all_events, name="events"),
    path("event/<int:id>", views.event, name="event"),
    path("create_cluster/<int:id>", views.create_cluster, name="create_cluster"),
    path("admin_all_events/", views.admin_all_events, name="admin_all_events"),
]
