from django.contrib import admin

from .models import MoodleCategory, MoodleCourse, MoodleGradeSnapshot, MoodleWritebackLog


@admin.register(MoodleCategory)
class MoodleCategoryAdmin(admin.ModelAdmin):
	list_display = ("moodle_category_id", "nome", "parent", "coursecount", "visible", "updated_at")
	search_fields = ("nome", "idnumber")


@admin.register(MoodleCourse)
class MoodleCourseAdmin(admin.ModelAdmin):
	list_display = ("moodle_course_id", "fullname", "categoria", "curso", "visible", "updated_at")
	search_fields = ("fullname", "shortname", "idnumber")
	list_filter = ("visible", "format")


@admin.register(MoodleGradeSnapshot)
class MoodleGradeSnapshotAdmin(admin.ModelAdmin):
	list_display = ("id", "snapshot_type", "wsfunction", "moodle_course_id", "moodle_user_id", "created_at")
	search_fields = ("wsfunction",)
	list_filter = ("snapshot_type",)


@admin.register(MoodleWritebackLog)
class MoodleWritebackLogAdmin(admin.ModelAdmin):
	list_display = ("id", "wsfunction", "status", "moodle_course_id", "moodle_assignment_id", "created_at")
	search_fields = ("wsfunction", "error_message")
	list_filter = ("status", "wsfunction")
