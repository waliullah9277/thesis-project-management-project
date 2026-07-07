from django.contrib import admin
from .models import User, StudentProfile, SupervisorProfile

admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(SupervisorProfile)
