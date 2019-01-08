"""
Helper functions used by both content_type_gating and course_duration_limits.
"""

from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_COMMUNITY_TA,
    Role
)
from student.roles import (
    CourseBetaTesterRole,
    CourseInstructorRole,
    CourseStaffRole,
    OrgStaffRole,
    OrgInstructorRole,
    GlobalStaff
)
from xmodule.partitions.partitions import Group

CONTENT_TYPE_GATE_GROUP_IDS = {
    'limited_access': 1,
    'full_access': 2,
}
LIMITED_ACCESS = Group(CONTENT_TYPE_GATE_GROUP_IDS['limited_access'], 'Limited-access Users')
FULL_ACCESS = Group(CONTENT_TYPE_GATE_GROUP_IDS['full_access'], 'Full-access Users')


def has_staff_roles(user, course_key):
    """
    Disable feature based enrollments for the enrollment if a user has any of the following roles
    Staff, Instructor, Beta Tester, Forum Community TA, Forum Group Moderator, Forum Moderator, Forum Administrator
    """
    forum_roles = [FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_GROUP_MODERATOR,
                   FORUM_ROLE_MODERATOR, FORUM_ROLE_ADMINISTRATOR]
    is_staff = CourseStaffRole(course_key).has_user(user)
    is_instructor = CourseInstructorRole(course_key).has_user(user)
    is_beta_tester = CourseBetaTesterRole(course_key).has_user(user)
    is_org_staff = OrgStaffRole(course_key.org).has_user(user)
    is_org_instructor = OrgInstructorRole(course_key.org).has_user(user)
    is_global_staff = GlobalStaff().has_user(user)
    has_forum_role = Role.user_has_role_for_course(user, course_key, forum_roles)
    if any([is_staff, is_instructor, is_beta_tester, is_org_staff,
            is_org_instructor, is_global_staff, has_forum_role]):
        return True
    return False
