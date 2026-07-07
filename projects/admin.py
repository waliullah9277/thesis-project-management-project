from django.contrib import admin
from .models import Team, Project, ProjectDocument


admin.site.register(Team)
admin.site.register(Project)
admin.site.register(ProjectDocument)