from rest_framework import serializers
from .models import Team, Project, ProjectDocument, ProjectFeedback
from accounts.models import User


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "student_id",
            "email",
            "first_name",
            "last_name",
            "role",
        ]


class TeamSerializer(serializers.ModelSerializer):
    leader_details = SimpleUserSerializer(source="leader", read_only=True)
    members_details = SimpleUserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "leader",
            "leader_details",
            "members",
            "members_details",
            "created_at",
        ]
        read_only_fields = ["leader", "created_at"]

    def validate_members(self, members):
        for member in members:
            if member.role != "STUDENT":
                raise serializers.ValidationError("Only students can be team members.")
        return members

    def create(self, validated_data):
        request = self.context.get("request")
        members = validated_data.pop("members", [])

        team = Team.objects.create(
            leader=request.user,
            **validated_data
        )

        team.members.add(request.user)

        for member in members:
            team.members.add(member)

        return team


class ProjectSerializer(serializers.ModelSerializer):
    team_details = TeamSerializer(source="team", read_only=True)
    supervisor_details = SimpleUserSerializer(source="supervisor", read_only=True)
    submitted_by_details = SimpleUserSerializer(source="submitted_by", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "team",
            "team_details",
            "supervisor",
            "supervisor_details",
            "title",
            "project_type",
            "description",
            "technology_stack",
            "status",
            "submitted_by",
            "submitted_by_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "submitted_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")

        project = Project.objects.create(
            submitted_by=request.user,
            **validated_data
        )

        return project

class AssignSupervisorSerializer(serializers.Serializer):
    supervisor_id = serializers.IntegerField()

    def validate_supervisor_id(self, value):
        try:
            supervisor = User.objects.get(id=value, role="SUPERVISOR")
        except User.DoesNotExist:
            raise serializers.ValidationError("Valid supervisor not found.")

        return value


class ProjectStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["APPROVED", "REJECTED", "IN_PROGRESS", "COMPLETED"]
    )

class ProjectFeedbackSerializer(serializers.ModelSerializer):
    supervisor_details = SimpleUserSerializer(source="supervisor", read_only=True)

    class Meta:
        model = ProjectFeedback
        fields = [
            "id",
            "project",
            "supervisor",
            "supervisor_details",
            "comment",
            "created_at",
        ]
        read_only_fields = [
            "supervisor",
            "created_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")

        feedback = ProjectFeedback.objects.create(
            supervisor=request.user,
            **validated_data
        )

        return feedback