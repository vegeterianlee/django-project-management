from django.contrib import admin
from django.utils.html import format_html

from apps.domain.tasks.models import Task, TaskAssignee


class TaskAssigneeInline(admin.TabularInline):
    """작업 담당자 인라인"""
    model = TaskAssignee
    extra = 1
    fields = ['user', 'is_primary', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task 관리자 설정"""
    list_display = [
        'id', 'title', 'project', 'phase', 'status', 'priority',
        'start_date', 'end_date', 'is_deleted', 'created_at',
    ]
    list_filter = ['status', 'priority', 'phase', 'project', 'start_date', 'end_date', 'created_at', 'deleted_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('project', 'title', 'description')}),
        ('작업 정보', {'fields': ('phase', 'status', 'priority', 'start_date', 'end_date')}),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [TaskAssigneeInline]
    ordering = ['-created_at']
    list_per_page = 25

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')

    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True


@admin.register(TaskAssignee)
class TaskAssigneeAdmin(admin.ModelAdmin):
    """TaskAssignee 관리자 설정"""
    list_display = [
        'id', 'task', 'user', 'is_primary', 'is_deleted', 'created_at',
    ]
    list_filter = ['is_primary', 'task', 'user', 'created_at', 'deleted_at']
    search_fields = ['task__title', 'user__name']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('task', 'user', 'is_primary')}),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ['-created_at']
    list_per_page = 25

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')

    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True