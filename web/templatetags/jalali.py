from django import template
from django.utils import timezone
from datetime import timedelta
from jalali_date import datetime2jalali

register = template.Library()

@register.filter
def jalali(dt):
    if not dt:
        return ""

    now = timezone.now()

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_default_timezone())

    diff = now - dt

    if diff < timedelta(minutes=1):
        return "چند لحظه پیش"

    if diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes} دقیقه پیش"

    if diff < timedelta(hours=24):
        hours = diff.seconds // 3600
        return f"{hours} ساعت پیش"

    if diff < timedelta(days=2):
        return "دیروز"

    if diff < timedelta(days=7):
        days = diff.days
        return f"{days} روز پیش"

    return datetime2jalali(dt).strftime("%Y/%m/%d")
