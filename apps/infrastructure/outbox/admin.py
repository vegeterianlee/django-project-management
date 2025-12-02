"""
Outbox Admin

Outbox 이벤트를 Django Admin에서 관리합니다.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.infrastructure.outbox.models import OutboxEvent


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    """OutboxEvent 관리자 설정"""
    list_display = [
        'id', 'event_type', 'aggregate_type', 'aggregate_id',
        'status_display', 'retry_count', 'created_at', 'processed_at'
    ]
    list_filter = [
        'status', 'event_type', 'aggregate_type', 'created_at', 'processed_at'
    ]
    search_fields = ['aggregate_type', 'aggregate_id', 'event_type']
    readonly_fields = [
        'id', 'created_at', 'published_at', 'processed_at',
        'last_error_at', 'status_display', 'event_data_preview'
    ]
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'event_type', 'aggregate_type', 'aggregate_id')
        }),
        ('이벤트 데이터', {
            'fields': ('event_data_preview',)
        }),
        ('상태 관리', {
            'fields': ('status_display', 'retry_count', 'max_retries', 'celery_task_id')
        }),
        ('에러 정보', {
            'fields': ('error_message', 'last_error_at'),
            'classes': ('collapse',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'published_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
    list_per_page = 50

    def status_display(self, obj):
        """상태 표시"""
        colors = {
            'PENDING': 'orange',
            'PUBLISHED': 'blue',
            'PROCESSED': 'green',
            'FAILED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = '상태'

    def event_data_preview(self, obj):
        """이벤트 데이터 미리보기"""
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.event_data, indent=2, ensure_ascii=False))
    event_data_preview.short_description = '이벤트 데이터'