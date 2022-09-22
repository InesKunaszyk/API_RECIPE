"""
Serializers for the user API View
"""

from django.contrib.auth import get_user_model, authenticate

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields =['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, "min_length": 10}}

    def create(self, validated_data):
        """Create and return a user with encrytped password"""
        return get_user_model().objects.create_user(**validated_data)
