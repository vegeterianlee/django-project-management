from django.contrib import admin
from django.utils.html import format_html

from apps.domain.meetings.models import Meeting, MeetingAssignee


class MeetingAssigneeInline(admin.TabularInline):
    """회의 참석자 인라인"""
    model = MeetingAssignee
    extra = 1
    fields = ['user', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Meeting 관리자 설정"""
    list_display = [
        'id', 'title', 'project', 'phase', 'creator', 'meeting_date',
        'location', 'is_deleted', 'created_at',
    ]
    list_filter = ['phase', 'project', 'creator', 'meeting_date', 'created_at', 'deleted_at']
    search_fields = ['title', 'content', 'location']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('project', 'creator', 'title', 'phase')}),
        ('회의 정보', {'fields': ('meeting_date', 'location', 'content')}),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [MeetingAssigneeInline]
    ordering = ['-created_at']
    list_per_page = 25

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')

    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True


@admin.register(MeetingAssignee)
class MeetingAssigneeAdmin(admin.ModelAdmin):
    """MeetingAssignee 관리자 설정"""
    list_display = [
        'id', 'meeting', 'user', 'is_deleted', 'created_at',
    ]
    list_filter = ['meeting', 'user', 'created_at', 'deleted_at']
    search_fields = ['meeting__title', 'user__name']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('meeting', 'user')}),
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