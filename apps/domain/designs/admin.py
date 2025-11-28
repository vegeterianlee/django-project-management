"""
Design Domain Admin

설계(Design) 관련 모델의 Django Admin 설정입니다.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.domain.designs.models import ProjectDesign, DesignVersion, DesignAssignee, DesignHistory


class DesignVersionInline(admin.TabularInline):
    """설계 버전 인라인"""
    model = DesignVersion
    extra = 1
    fields = ['name', 'status', 'submitted_date', 'construction_cost', 'created_at']
    readonly_fields = ['created_at']
    classes = ['collapse']  # 기본적으로 접혀있도록 설정


class DesignAssigneeInline(admin.TabularInline):
    """설계 담당자 인라인"""
    model = DesignAssignee
    extra = 1
    fields = ['user', 'is_primary', 'created_at']
    readonly_fields = ['created_at']


class DesignHistoryInline(admin.TabularInline):
    """설계 이력 인라인"""
    model = DesignHistory
    extra = 1
    fields = ['user', 'content', 'created_at']
    readonly_fields = ['created_at']
    classes = ['collapse']  # 기본적으로 접혀있도록 설정


@admin.register(ProjectDesign)
class ProjectDesignAdmin(admin.ModelAdmin):
    """ProjectDesign 관리자 설정"""
    list_display = [
        'id', 'project', 'design_start_date', 'design_folder_location',
        'is_deleted', 'created_at',
    ]
    list_filter = [
        'design_start_date', 'created_at', 'deleted_at'
    ]
    search_fields = ['project__name', 'project__project_code', 'design_folder_location']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('project',)}),
        ('설계 정보', {
            'fields': ('design_start_date', 'design_folder_location')
        }),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [DesignVersionInline, DesignAssigneeInline, DesignHistoryInline]
    ordering = ['-created_at']
    list_per_page = 25

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')

    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True


@admin.register(DesignVersion)
class DesignVersionAdmin(admin.ModelAdmin):
    """DesignVersion 관리자 설정"""
    list_display = [
        'id', 'design', 'name', 'status', 'submitted_date',
        'construction_cost', 'is_deleted', 'created_at',
    ]
    list_filter = [
        'status', 'submitted_date', 'design', 'created_at', 'deleted_at'
    ]
    search_fields = ['design__project__name', 'name']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('design', 'name', 'status')}),
        ('일정 정보', {'fields': ('submitted_date',)}),
        ('공사 정보', {
            'fields': (
                'construction_cost',
                'pile_quantity',
                'pile_length',
                'concrete_volume',
                'pc_length',
            )
        }),
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


@admin.register(DesignAssignee)
class DesignAssigneeAdmin(admin.ModelAdmin):
    """DesignAssignee 관리자 설정"""
    list_display = [
        'id', 'design', 'user', 'is_primary', 'is_deleted', 'created_at',
    ]
    list_filter = ['is_primary', 'design', 'user', 'created_at', 'deleted_at']
    search_fields = ['design__project__name', 'user__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('design', 'user', 'is_primary')}),
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


@admin.register(DesignHistory)
class DesignHistoryAdmin(admin.ModelAdmin):
    """DesignHistory 관리자 설정"""
    list_display = [
        'id', 'design', 'user', 'content_preview',
        'is_deleted', 'created_at',
    ]
    list_filter = ['design', 'user', 'created_at', 'deleted_at']
    search_fields = ['design__project__name', 'user__name', 'content']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('design', 'user')}),
        ('이력 내용', {'fields': ('content',)}),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ['-created_at']
    list_per_page = 25

    def content_preview(self, obj):
        """내용 미리보기 (최대 50자)"""
        if obj.content:
            preview = obj.content[:50]
            if len(obj.content) > 50:
                preview += '...'
            return preview
        return '-'

    content_preview.short_description = '내용 미리보기'

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')

    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True