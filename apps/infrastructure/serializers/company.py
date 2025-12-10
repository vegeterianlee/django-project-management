"""
Company Serializers

Company 도메인의 모델을 직렬화/역직렬화하는 Serializer입니다.
"""
from rest_framework import serializers
from apps.domain.company.models import Company, ContactPerson


class CompanyModelSerializer(serializers.ModelSerializer):
    """
    Company 모델의 Serializer

    Company 모델의 모든 필드를 직렬화/역직렬화합니다.
    """

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'type',
            'address',
            'business_number',
            'representative',
            'contact_number',
            'email',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

    def validate_type(self, value):
        """회사 타입 검증"""
        valid_types = [choice[0] for choice in Company.COMPANY_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"회사 타입은 {valid_types} 중 하나여야 합니다."
            )
        return value


class ContactPersonModelSerializer(serializers.ModelSerializer):
    """
    ContactPerson 모델의 Serializer

    ContactPerson 모델의 모든 필드를 직렬화/역직렬화합니다.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = ContactPerson
        fields = [
            'id',
            'name',
            'email',
            'mobile',
            'position',
            'position_title',
            'company',
            'company_name',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'company_name', 'position_title']