"""
Sales Domain Admin

영업(Sales) 관련 모델의 Django Admin 설정입니다.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.domain.sales.models import ProjectSales, SalesAssignee, SalesHistory


class SalesAssigneeInline(admin.TabularInline):
    """영업 담당자 인라인"""
    model = SalesAssignee
    extra = 1
    fields = ['user', 'is_primary', 'created_at']
    readonly_fields = ['created_at']


class SalesHistoryInline(admin.TabularInline):
    """영업 이력 인라인"""
    model = SalesHistory
    extra = 1
    fields = ['user', 'content', 'is_public', 'created_at']
    readonly_fields = ['created_at']
    classes = ['collapse']  # 기본적으로 접혀있도록 설정


@admin.register(ProjectSales)
class ProjectSalesAdmin(admin.ModelAdmin):
    """ProjectSales 관리자 설정"""
    list_display = [
        'id', 'project', 'sales_type', 'sales_received_date',
        'estimate_submit_date', 'estimate_amount', 'design_amount',
        'is_deleted', 'created_at',
    ]
    list_filter = [
        'sales_type', 'sales_received_date', 'estimate_submit_date',
        'created_at', 'deleted_at'
    ]
    search_fields = ['project__name', 'project__project_code']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('project', 'sales_type')}),
        ('영업 일정', {
            'fields': (
                'sales_received_date',
                'estimate_request_date',
                'estimate_expected_date',
                'estimate_submit_date',
            )
        }),
        ('금액 정보', {
            'fields': ('estimate_amount', 'design_amount')
        }),
        ('소프트 삭제 정보', {'fields': ('is_deleted_display', 'deleted_at'), 'classes': ('collapse',)}),
        ('타임스탬프', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [SalesAssigneeInline, SalesHistoryInline]
    ordering = ['-created_at']
    list_per_page = 25

    def is_deleted_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">✓ 삭제됨</span>')
        return format_html('<span style="color: green;">✓ 활성</span>')

    is_deleted_display.short_description = '삭제 상태'
    is_deleted_display.allow_tags = True


@admin.register(SalesAssignee)
class SalesAssigneeAdmin(admin.ModelAdmin):
    """SalesAssignee 관리자 설정"""
    list_display = [
        'id', 'sales', 'user', 'is_primary', 'is_deleted', 'created_at',
    ]
    list_filter = ['is_primary', 'sales', 'user', 'created_at', 'deleted_at']
    search_fields = ['sales__project__name', 'user__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('sales', 'user', 'is_primary')}),
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


@admin.register(SalesHistory)
class SalesHistoryAdmin(admin.ModelAdmin):
    """SalesHistory 관리자 설정"""
    list_display = [
        'id', 'sales', 'user', 'is_public', 'content_preview',
        'is_deleted', 'created_at',
    ]
    list_filter = ['is_public', 'sales', 'user', 'created_at', 'deleted_at']
    search_fields = ['sales__project__name', 'user__name', 'content']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_deleted_display']
    fieldsets = (
        ('기본 정보', {'fields': ('sales', 'user', 'is_public')}),
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