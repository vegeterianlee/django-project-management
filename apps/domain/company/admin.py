# """
# Users Admin Configuration
#
# Users 도메인 모델을 Django Admin에 등록합니다.
# """
# from django.contrib import admin
# from django.utils.html import format_html
# from apps.domain.users.models import (
#     Department,
#     Position,
#     User,
#     UserPermission,
#     PhaseAccessRule,
# )
#
#
# @admin.register(Department)
# class DepartmentAdmin(admin.ModelAdmin):
#     """
#     Department 모델 Admin 설정
#
#     부서 정보를 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     list_display = ['id', 'name', 'description', 'user_count']
#     search_fields = ['name', 'description']
#     list_per_page = 25
#
#     def user_count(self, obj):
#         """
#         해당 부서에 소속된 사용자 수를 표시합니다.
#
#         Args:
#             obj: Department 인스턴스
#
#         Returns:
#             부서에 소속된 사용자 수
#         """
#         count = User.objects.filter(department_id=obj.id, deleted_at__isnull=True).count()
#         return count
#
#     user_count.short_description = '소속 사용자 수'
#
#
# @admin.register(Position)
# class PositionAdmin(admin.ModelAdmin):
#     """
#     Position 모델 Admin 설정
#
#     직급 정보를 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     list_display = [
#         'id',
#         'title',
#         'hierarchy_level',
#         'is_executive',
#         'description',
#         'user_count',
#     ]
#     list_filter = ['is_executive', 'hierarchy_level']
#     search_fields = ['title', 'description']
#     ordering = ['-hierarchy_level']  # 계층 레벨 높은 순으로 정렬
#     list_per_page = 25
#
#     fieldsets = (
#         ('기본 정보', {
#             'fields': ('title', 'description')
#         }),
#         ('직급 정보', {
#             'fields': ('hierarchy_level', 'is_executive')
#         }),
#     )
#
#     def user_count(self, obj):
#         """해당 직급의 사용자 수를 표시"""
#         count = User.objects.filter(position_id=obj.id, deleted_at__isnull=True).count()
#         return count
#
#     user_count.short_description = '소속 사용자 수'
#
#
# class UserPermissionInline(admin.TabularInline):
#     """
#     User Admin에서 UserPermission을 인라인으로 표시합니다.
#     """
#     model = UserPermission
#     extra = 1
#     fields = ['phase', 'permission_type']
#
#
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     """
#     User 모델 Admin 설정
#
#     사용자 정보를 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     list_display = [
#         'id',
#         'user_uid',
#         'name',
#         'email',
#         'company',
#         'department_display',
#         'position_display',
#         'account_locked',
#         'is_deleted',
#         'created_at',
#     ]
#
#     list_filter = [
#         'account_locked',
#         'company',
#         'created_at',
#         'deleted_at',
#     ]
#
#     search_fields = [
#         'user_uid',
#         'name',
#         'email',
#         'company__name',
#     ]
#
#     readonly_fields = [
#         'created_at',
#         'updated_at',
#         'deleted_at',
#         'is_deleted_display',
#         'password',  # 비밀번호는 읽기 전용 (해시되어 있음)
#     ]
#
#     fieldsets = (
#         ('기본 정보', {
#             'fields': ('user_uid', 'name', 'email', 'password')
#         }),
#         ('소속 정보', {
#             'fields': ('company', 'position')
#         }),
#         ('프로필', {
#             'fields': ('profile_url', 'color'),
#             'classes': ('collapse',)
#         }),
#         ('계정 보안', {
#             'fields': ('account_locked', 'login_attempts', 'lock_time')
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
#     # 인라인으로 UserPermission 표시
#     inlines = [UserPermissionInline]
#
#     ordering = ['-created_at']
#     list_per_page = 25
#
#     def department_display(self, obj):
#         """
#         부서 ID를 부서명으로 표시합니다.
#
#         Args:
#             obj: User 인스턴스
#
#         Returns:
#             부서명 또는 ID
#         """
#         try:
#             department = Department.objects.get(id=obj.department_id)
#             return department.name
#         except Department.DoesNotExist:
#             return f"ID: {obj.department_id}"
#
#     department_display.short_description = '부서'
#
#     def position_display(self, obj):
#         """
#         직급 ID를 직급명으로 표시합니다.
#
#         Args:
#             obj: User 인스턴스
#
#         Returns:
#             직급명 또는 ID
#         """
#         try:
#             position = Position.objects.get(id=obj.position_id)
#             return position.title
#         except Position.DoesNotExist:
#             return f"ID: {obj.position_id}"
#
#     position_display.short_description = '직급'
#
#     def is_deleted_display(self, obj):
#         """소프트 삭제 여부를 색상으로 표시"""
#         if obj.is_deleted:
#             return format_html('<span style="color: red;">✓ 삭제됨</span>')
#         return format_html('<span style="color: green;">✓ 활성</span>')
#
#     is_deleted_display.short_description = '삭제 상태'
#
#
# @admin.register(UserPermission)
# class UserPermissionAdmin(admin.ModelAdmin):
#     """
#     UserPermission 모델 Admin 설정
#
#     사용자 권한 정보를 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     list_display = [
#         'id',
#         'user',
#         'phase',
#         'permission_type',
#         'created_display',
#     ]
#
#     list_filter = [
#         'phase',
#         'permission_type',
#         'user',
#     ]
#
#     search_fields = [
#         'user__name',
#         'user__user_uid',
#         'user__email',
#         'phase',
#     ]
#
#     fieldsets = (
#         ('권한 정보', {
#             'fields': ('user', 'phase', 'permission_type')
#         }),
#     )
#
#     ordering = ['user', 'phase']
#     list_per_page = 25
#
#     def created_display(self, obj):
#         """생성 시간을 간단히 표시"""
#         if hasattr(obj, 'created_at'):
#             return obj.created_at.strftime('%Y-%m-%d %H:%M')
#         return '-'
#
#     created_display.short_description = '생성일'
#
#
# @admin.register(PhaseAccessRule)
# class PhaseAccessRuleAdmin(admin.ModelAdmin):
#     """
#     PhaseAccessRule 모델 Admin 설정
#
#     Phase별 접근 규칙을 관리하는 Admin 인터페이스를 제공합니다.
#     """
#     list_display = [
#         'id',
#         'phase',
#         'required_departments_display',
#         'department_count',
#     ]
#
#     list_filter = ['phase']
#
#     search_fields = ['phase']
#
#     fieldsets = (
#         ('Phase 접근 규칙', {
#             'fields': ('phase', 'required_departments')
#         }),
#     )
#
#     ordering = ['phase']
#     list_per_page = 25
#
#     def required_departments_display(self, obj):
#         """
#         필수 부서 목록을 읽기 쉽게 표시합니다.
#
#         Args:
#             obj: PhaseAccessRule 인스턴스
#
#         Returns:
#             부서명 목록 또는 "제한 없음"
#         """
#         if not obj.required_departments:
#             return format_html('<span style="color: gray;">제한 없음</span>')
#
#         # 부서 ID를 부서명으로 변환
#         department_names = []
#         for dept_id in obj.required_departments:
#             try:
#                 dept = Department.objects.get(id=dept_id)
#                 department_names.append(dept.name)
#             except Department.DoesNotExist:
#                 department_names.append(f"ID: {dept_id}")
#
#         return ', '.join(department_names)
#
#     required_departments_display.short_description = '필수 부서'
#
#     def department_count(self, obj):
#         """필수 부서 개수를 표시"""
#         if not obj.required_departments:
#             return 0
#         return len(obj.required_departments)
#
#     department_count.short_description = '부서 수'