# IT303_Btech_Guide_Allocator

## Permissions 

1. Roles - admin
   
   actions - login,home,register,add_student,add_event,edit_event,add_faculty,admin_all_events,create_cluster,run_allocation,reset_allocation,admin_show_clash,admin_resolve_clash,add_permissions,generate_pdf,event_results,logout_view

3. Roles - Student
   
   actions - all_events,event,logout_view

5. Roles - Faculty
   
   actions - show_all_clashes,resolve_clash,eligible_events,logout_view

app name - allocator (common for all)


Install Redis
   Remove comment from bind 127.0.0.1 in .conf file(redis.windows.config)
   Start redis server using config file in Redis installed directory [redis-server ./redis.windows.config]
   To start redis for out task(email): python -m celery -A alloc worker --pool=solo -l info
