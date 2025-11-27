"""
Projects Domain Admin

프로젝트 관련 모델의 Django Admin 설정입니다.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.domain.projects.models import Project, ProjectCompanyLink, ProjectAssignee
from apps.domain.company.models import Company
from apps.domain.users.models import User


class ProjectCompanyLinkInline(admin.TabularInline):
    """프로젝트-회사 연결 인라인"""
    model = ProjectCompanyLink
    extra = 1
    fields = ['company', 'role', 'created_at']
    readonly_fields = ['created_at']


class ProjectAssigneeInline(admin.TabularInline):
    """프로젝트 담당자 인라인"""
    model = ProjectAssignee
    extra = 1
    fields = ['user', 'is_primary', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Project 관리자 설정"""
    list_display = [
        'id', 'project_code', 'name', 'status', 'start_date', 'end_date',
        'is_deleted', 'created_at',
    ]
    list_filter = ['status', 'start_date', 'end_date', 'created_at', 'deleted_at']
    search_fields = ['project_code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('project_code', 'name', 'description')}),
        ('프로젝트 정보', {'fields': ('status', 'method', 'start_date', 'end_date')}),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [ProjectCompanyLinkInline, ProjectAssigneeInline]
    ordering = ['-created_at']
    list_per_page = 25

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')
    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True


@admin.register(ProjectCompanyLink)
class ProjectCompanyLinkAdmin(admin.ModelAdmin):
    """ProjectCompanyLink 관리자 설정"""
    list_display = ['id', 'project', 'company', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['project__name', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25


@admin.register(ProjectAssignee)
class ProjectAssigneeAdmin(admin.ModelAdmin):
    """ProjectAssignee 관리자 설정"""
    list_display = ['id', 'project', 'user', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['project__name', 'user__name', 'user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 25