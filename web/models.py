from django.db import models
from django.contrib.auth.models import User

class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال انجام'),
        ('done', 'انجام شد'),
        ('failed', 'ناموفق'),
    ]

    filename = models.CharField(max_length=255)
    data = models.BinaryField()
    transcribed_text = models.TextField(blank=True, null=True)
    srt_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_text = models.BooleanField(default=False)
    is_subtitle = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.filename
