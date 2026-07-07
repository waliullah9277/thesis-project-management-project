from django.contrib import admin
from .models import Team, Project, ProjectDocument, ProjectFeedback

admin.site.register(Team)
admin.site.register(Project)
admin.site.register(ProjectDocument)
admin.site.register(ProjectFeedback)