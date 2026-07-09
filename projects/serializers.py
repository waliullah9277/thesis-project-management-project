from rest_framework import serializers
from .models import Team, Project, ProjectDocument, ProjectFeedback, TeamMemberInfo
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


class TeamMemberInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMemberInfo
        fields = [
            "id",
            "team",
            "name",
            "student_id",
            "phone",
            "created_at",
        ]
        read_only_fields = ["team", "created_at"]

class TeamSerializer(serializers.ModelSerializer):
    leader_name = serializers.SerializerMethodField()
    members_info = serializers.SerializerMethodField()
    member_infos = TeamMemberInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "leader",
            "leader_name",
            "members",
            "members_info",
            "member_infos",
            "member_count",
            "created_at",
        ]
        read_only_fields = ["leader", "members", "created_at"]

    def validate_member_count(self, value):
        if value < 1:
            raise serializers.ValidationError("Minimum 1 member is required.")
        if value > 3:
            raise serializers.ValidationError("Maximum 3 members are allowed.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")

        team = Team.objects.create(
            name=validated_data["name"],
            leader=request.user,
            member_count=validated_data.get("member_count", 1)
        )

        team.members.add(request.user)
        return team

    def get_leader_name(self, obj):
        return f"{obj.leader.first_name} {obj.leader.last_name}".strip()

    def get_members_info(self, obj):
        return [
            {
                "id": member.id,
                "student_id": member.student_id,
                "name": f"{member.first_name} {member.last_name}".strip(),
                "email": member.email,
                "phone": member.phone,
            }
            for member in obj.members.all()
        ]


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
    

