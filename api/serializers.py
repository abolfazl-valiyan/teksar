from rest_framework import serializers
from web.models import *
class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    is_text = serializers.BooleanField(default=True)
    is_subtitle = serializers.BooleanField(default=False)


class FileSubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['filename', 'status']
class FileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'