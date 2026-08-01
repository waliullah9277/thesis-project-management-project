from django.urls import path

from .views import (
    AdminProjectDocumentListAPIView,
    AdminProjectListAPIView,
    AssignSupervisorAPIView,
    ProjectDetailAPIView,
    ProjectDocumentDeleteAPIView,
    ProjectDocumentDownloadAPIView,
    ProjectDocumentListCreateAPIView,
    ProjectDocumentReviewAPIView,
    ProjectDocumentVersionHistoryAPIView,
    ProjectFeedbackCreateAPIView,
    ProjectFeedbackListAPIView,
    ProjectLatestDocumentListAPIView,
    ProjectListCreateAPIView,
    ProjectStatusUpdateAPIView,
    SupervisorAssignedProjectListAPIView,
    SupervisorProjectReviewAPIView,
    TeamListCreateAPIView,
    TeamMemberInfoCreateAPIView,
    TeamMemberInfoUpdateDeleteAPIView,
    TeamMemberUpdateAPIView,
    TeamUpdateDeleteAPIView,
)


urlpatterns = [
    # =====================================================
    # TEAM ROUTES
    # =====================================================

    path(
        "teams/",
        TeamListCreateAPIView.as_view(),
        name="team-list-create",
    ),

    path(
        "teams/<int:team_id>/members/",
        TeamMemberUpdateAPIView.as_view(),
        name="team-member-update",
    ),

    path(
        "teams/<int:team_id>/update-delete/",
        TeamUpdateDeleteAPIView.as_view(),
        name="team-update-delete",
    ),

    path(
        "teams/<int:team_id>/members/add/",
        TeamMemberInfoCreateAPIView.as_view(),
        name="team-member-info-create",
    ),

    path(
        (
            "teams/members/"
            "<int:member_id>/update-delete/"
        ),
        TeamMemberInfoUpdateDeleteAPIView.as_view(),
        name="team-member-info-update-delete",
    ),

    # =====================================================
    # ADMIN ROUTES
    # =====================================================

    path(
        "admin/list/",
        AdminProjectListAPIView.as_view(),
        name="admin-project-list",
    ),

    path(
        "admin/documents/",
        AdminProjectDocumentListAPIView.as_view(),
        name="admin-project-document-list",
    ),

    # =====================================================
    # SUPERVISOR ROUTES
    # =====================================================

    path(
        "supervisor/assigned/",
        SupervisorAssignedProjectListAPIView.as_view(),
        name="supervisor-assigned-projects",
    ),

    path(
        "supervisor/review/<int:project_id>/",
        SupervisorProjectReviewAPIView.as_view(),
        name="supervisor-project-review",
    ),

    # =====================================================
    # PROJECT DOCUMENT ROUTES
    #
    # Keep these before the general project detail route.
    # =====================================================

    path(
        "<int:project_id>/documents/",
        ProjectDocumentListCreateAPIView.as_view(),
        name="project-document-list-create",
    ),

    path(
        "<int:project_id>/documents/latest/",
        ProjectLatestDocumentListAPIView.as_view(),
        name="project-latest-document-list",
    ),

    path(
        "documents/<int:document_id>/versions/",
        ProjectDocumentVersionHistoryAPIView.as_view(),
        name="project-document-version-history",
    ),

    path(
        "documents/<int:document_id>/delete/",
        ProjectDocumentDeleteAPIView.as_view(),
        name="project-document-delete",
    ),

    path(
        "documents/<int:document_id>/review/",
        ProjectDocumentReviewAPIView.as_view(),
        name="project-document-review",
    ),

    path(
        "documents/<int:document_id>/download/",
        ProjectDocumentDownloadAPIView.as_view(),
        name="project-document-download",
    ),

    # =====================================================
    # PROJECT FEEDBACK ROUTES
    # =====================================================

    path(
        "<int:project_id>/feedback/",
        ProjectFeedbackCreateAPIView.as_view(),
        name="project-feedback-create",
    ),

    path(
        "<int:project_id>/feedbacks/",
        ProjectFeedbackListAPIView.as_view(),
        name="project-feedback-list",
    ),

    # =====================================================
    # PROJECT MANAGEMENT ROUTES
    # =====================================================

    path(
        "<int:project_id>/assign-supervisor/",
        AssignSupervisorAPIView.as_view(),
        name="assign-supervisor",
    ),

    path(
        "<int:project_id>/status/",
        ProjectStatusUpdateAPIView.as_view(),
        name="project-status-update",
    ),

    path(
        "<int:project_id>/",
        ProjectDetailAPIView.as_view(),
        name="project-detail",
    ),

    path(
        "",
        ProjectListCreateAPIView.as_view(),
        name="project-list-create",
    ),
]