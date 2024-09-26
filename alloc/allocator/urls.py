from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register, name = "register"),
    path("home/", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("add_student/", views.add_student, name="add_student"),
    path("add_event/", views.add_event, name="add_event"),
    path("add_faculty/", views.add_faculty, name="add_faculty"),    
    path("events/", views.all_events, name="events"),
    path("event/<int:id>", views.event, name="event"),
    path("create_cluster/<int:id>", views.create_cluster, name="create_cluster"),
    path("admin_all_events/", views.admin_all_events, name="admin_all_events"),
    path("run_allocation/<int:id>/", views.run_allocation, name="run_allocation"),
    path("reset_allocation/<int:id>/", views.reset_allocation, name="reset_allocation"),    
    path("show_all_clashes/", views.show_all_clashes, name="show_all_clashes"),
    path("admin_show_clash/", views.admin_show_clash, name="admin_show_clash"),
    path("resolve_clash/<int:id>", views.resolve_clash, name="resolve_clash"),
    path("admin_resolve_clash/<int:id>", views.admin_resolve_clash, name="admin_resolve_clash"),
]
