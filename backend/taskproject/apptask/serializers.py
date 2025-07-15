from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'username', 'name',
            'role', 'password', 'password_confirm', 'phone', 'dni'
        ]
    
    def validate_email(self, value):
        if not value.endswith('@uni.edu.ec'):
            raise serializers.ValidationError(
                "El email debe ser del dominio @uni.edu.ec"
            )
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Usar name como first_name si no se proporciona
        if not validated_data.get('first_name') and validated_data.get('name'):
            validated_data['first_name'] = validated_data['name']
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    if not user.is_active:
                        raise serializers.ValidationError('Cuenta desactivada')
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError('Credenciales incorrectas')
            except User.DoesNotExist:
                raise serializers.ValidationError('Usuario no encontrado')
        
        raise serializers.ValidationError('Email y contraseña requeridos')

class UserProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(read_only=True)
    is_institutional_email = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'username', 'name',
            'role', 'role_display', 'phone', 'dni', 'display_name',
            'is_institutional_email', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'email', 'date_joined']

class UserListSerializer(serializers.ModelSerializer):
    """Serializer para lista de usuarios (admin)"""
    role_display = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'display_name', 'username', 'name',
            'role', 'role_display', 'is_active', 'date_joined'
        ]