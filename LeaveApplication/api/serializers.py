from rest_framework import serializers
from .models import Employee
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
import re


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=Employee.objects.all())]
    )
    
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    is_manager = serializers.BooleanField(default=False)

    class Meta:
        model = Employee
        fields = (
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
           
            "is_manager",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        name_pattern = re.compile(r"^[A-Za-z]+$")

        first_name = attrs.get("first_name")
        if first_name is None or not first_name.strip():
            raise serializers.ValidationError(
                {"first_name": "First name cannot be empty or only spaces."}
            )
        if first_name and not name_pattern.match(first_name):
            raise serializers.ValidationError(
                {"first_name": "First name must contain only alphabetic characters."}
            )

        last_name = attrs.get("last_name")
        if last_name is None or not last_name.strip():
            raise serializers.ValidationError(
                {"last_name": "First name cannot be empty or only spaces."}
            )
        if last_name and not name_pattern.match(last_name):
            raise serializers.ValidationError(
                {"last_name": "Last name must contain only alphabetic characters."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = Employee.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)