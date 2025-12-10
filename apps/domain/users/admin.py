# """
# Company Admin Configuration
#
# Company 도메인 모델을 Django Admin에 등록합니다.
# """
# from django.contrib import admin
# from django.utils.html import format_html
# from apps.domain.company.models import Company, ContactPerson
#
#
# class ContactPersonInline(admin.TabularInline):
#     """
#     Company Admin에서 ContactPerson을 인라인으로 표시합니다.
#
#     TabularInline: 테이블 형식으로 표시 (간결함)
#     StackedInline: 세로로 쌓인 형식으로 표시 (더 많은 정보)
#     """
#     model = ContactPerson
#     extra = 1  # 기본으로 표시할 빈 폼 개수
#     fields = ['name', 'email', 'mobile', 'department_id', 'position_id', 'is_primary']
#     readonly_fields = ['created_at', 'updated_at']
#
#
# @admin.register(Company)
# class CompanyAdmin(admin.ModelAdmin):
#     """
#     Company 모델 Admin 설정
#
#     회사 정보를 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     # 리스트 페이지에 표시할 필드
#     list_display = [
#         'id',
#         'name',
#         'type',
#         'email',
#         'contact_number',
#         'is_deleted',  # 소프트 삭제 여부 표시
#         'created_at',
#     ]
#
#     # 필터 옵션 (사이드바에 표시)
#     list_filter = [
#         'type',
#         'created_at',
#         'updated_at',
#         'deleted_at',
#     ]
#
#     # 검색 필드
#     search_fields = [
#         'name',
#         'email',
#         'business_number',
#         'representative',
#         'contact_number',
#     ]
#
#     # 읽기 전용 필드 (수정 불가)
#     readonly_fields = [
#         'created_at',
#         'updated_at',
#         'deleted_at',
#         'is_deleted_display',  # 커스텀 메서드
#     ]
#
#     # 필드 그룹화 (상세 페이지)
#     fieldsets = (
#         ('기본 정보', {
#             'fields': ('name', 'type', 'email', 'contact_number')
#         }),
#         ('상세 정보', {
#             'fields': ('address', 'business_number', 'representative'),
#             'classes': ('collapse',)  # 접을 수 있게 설정
#         }),
#         ('소프트 삭제 정보', {
#             'fields': ('is_deleted_display', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#         ('타임스탬프', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     # 인라인으로 ContactPerson 표시
#     inlines = [ContactPersonInline]
#
#     # 정렬 기준
#     ordering = ['-created_at']
#
#     # 페이지당 표시할 항목 수
#     list_per_page = 25
#
#     def is_deleted_display(self, obj):
#         """
#         소프트 삭제 여부를 색상으로 표시합니다.
#
#         Args:
#             obj: Company 인스턴스
#
#         Returns:
#             HTML 형식의 삭제 여부 표시
#         """
#         if obj.is_deleted:
#             return format_html(
#                 '<span style="color: red;">✓ 삭제됨</span>'
#             )
#         return format_html(
#             '<span style="color: green;">✓ 활성</span>'
#         )
#
#     is_deleted_display.short_description = '삭제 상태'
#     is_deleted_display.allow_tags = True
#
#
# @admin.register(ContactPerson)
# class ContactPersonAdmin(admin.ModelAdmin):
#     """
#     ContactPerson 모델 Admin 설정
#
#     연락 담당자 정보를 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     # 리스트 페이지에 표시할 필드
#     list_display = [
#         'id',
#         'name',
#         'email',
#         'company',
#         'mobile',
#         'is_primary',
#         'is_deleted',
#         'created_at',
#     ]
#
#     # 필터 옵션
#     list_filter = [
#         'is_primary',
#         'company',
#         'created_at',
#         'deleted_at',
#     ]
#
#     # 검색 필드
#     search_fields = [
#         'name',
#         'email',
#         'mobile',
#         'company__name',  # 회사명으로도 검색 가능
#     ]
#
#     # 읽기 전용 필드
#     readonly_fields = [
#         'created_at',
#         'updated_at',
#         'deleted_at',
#         'is_deleted_display',
#     ]
#
#     # 필드 그룹화
#     fieldsets = (
#         ('기본 정보', {
#             'fields': ('name', 'email', 'mobile', 'company')
#         }),
#         ('소속 정보', {
#             'fields': ('department_id', 'position_id', 'is_primary')
#         }),
#         ('소프트 삭제 정보', {
#             'fields': ('is_deleted_display', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#         ('타임스탬프', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     # 정렬 기준
#     ordering = ['-created_at']
#
#     # 페이지당 표시할 항목 수
#     list_per_page = 25
#
#     def is_deleted_display(self, obj):
#         """소프트 삭제 여부를 색상으로 표시"""
#         if obj.is_deleted:
#             return format_html('<span style="color: red;">✓ 삭제됨</span>')
#         return format_html('<span style="color: green;">✓ 활성</span>')
#
#     is_deleted_display.short_description = '삭제 상태'