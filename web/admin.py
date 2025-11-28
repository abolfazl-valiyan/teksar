from django.contrib import admin
from .models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("filename", "user", "status", "created_at", "is_text", "is_subtitle")
    list_filter = ("status", "is_text", "is_subtitle", "created_at")
    search_fields = ("filename", "user__username")
    readonly_fields = ("created_at",)
