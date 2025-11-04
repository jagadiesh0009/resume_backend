from .models import *
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
User = get_user_model()
class FruitSerializer(serializers.ModelSerializer):
    class Meta:
        model=Fruit
        fields='__all__'
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields='__all__'
    def create(self, validated_data):
        # User creation logic
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user
    
    

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    new_password=serializers.CharField()  

# serializers.py
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not check_password(value, user.password):
            raise serializers.ValidationError("Incorrect old password")
        return value

    def validate_new_password(self, value):
        validate_password(value)  # Django's strong password checks
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['username','dateofbirth','email','phn','first_name','last_name','photo']
        read_only_fields = ['username']

