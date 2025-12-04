from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import File
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.conf import settings
import magic
from .tasks import process_file_task
from django.http import FileResponse
import os
@login_required
def upload_file(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'هیچ فایلی آپلود نشده')
            return redirect('upload_file')

        uploaded_file = request.FILES['file']

        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(uploaded_file.read(1024))
        uploaded_file.seek(0)

        if not (mime_type.startswith("video/") or mime_type.startswith("audio/")):
            messages.error(request, 'فقط فایل‌های صوتی یا ویدیویی مجاز هستند')
            return redirect('upload_file')

        want_srt = request.POST.get("is_subtitle") == "on"
        want_txt = request.POST.get("is_text") == "on"

        if not (want_srt or want_txt):
            messages.error(request, "حداقل یکی از گزینه‌ها (متن یا زیرنویس) باید انتخاب شود.")
            return redirect('upload_file')

        file_data = uploaded_file.read()

        new_file = File.objects.create(
            user=request.user,
            filename=uploaded_file.name,
            data=file_data,
            is_text=want_txt,
            is_subtitle=want_srt,
            status='pending'
        )

        task = process_file_task.delay(new_file.id)
        new_file.task_id = task.id
        new_file.save(update_fields=['task_id'])

        return redirect('file_list')

    return render(request, 'upload.html')
@login_required
def file_list(request):
    files = File.objects.filter(user=request.user).order_by('-created_at')

    status_map = {
        'pending': 'در حال انتظار',
        'processing': 'در حال انجام',
        'done': 'انجام شد',
        'failed': 'ناموفق',
    }

    for f in files:
        f.display_status = status_map.get(f.status, 'نامشخص')


        size_bytes = len(f.data) if f.data else 0
        f.size_kb = round(size_bytes / 1024, 1)

    return render(request, 'file_list.html', {'files': files})

@login_required
def file_detail(request, pk):
    f = get_object_or_404(File, pk=pk, user=request.user)

    size_bytes = len(f.data) if f.data else 0
    size_kb = round(size_bytes / 1024, 1)

    srt_content = None
    if f.is_subtitle:
        base_name = os.path.splitext(f.filename)[0]
        srt_path = os.path.join(settings.MEDIA_ROOT, "results", f"{base_name}.srt")

        if os.path.exists(srt_path):
            with open(srt_path, "r", encoding="utf-8", errors="ignore") as file:
                srt_content = file.read()

    context = {
        "file": f,
        "size_kb": size_kb,
        "srt_content": srt_content,
        "txt_content": f.transcribed_text if f.is_text else None,
    }
    return render(request, "file_detail.html", context)



@login_required
def file_detail(request, pk):
    f = get_object_or_404(File, pk=pk, user=request.user)

    size_bytes = len(f.data) if f.data else 0
    size_kb = round(size_bytes / 1024, 1)

    return render(request, 'file_detail.html', {
        "file": f,
        "size_kb": size_kb,
        "txt_content": f.transcribed_text,
        "srt_content": f.srt_content,
    })


@login_required
def download_result(request, pk, file_type):
    file_obj = get_object_or_404(File, pk=pk, user=request.user)

    if file_obj.status != 'done':
        messages.error(request, "فایل هنوز آماده نیست!")
        return redirect('file_list')

    base_name = os.path.splitext(file_obj.filename)[0]
    user_dir = os.path.join(settings.MEDIA_ROOT, "results", str(request.user.id))

    if file_type == "srt" and file_obj.is_subtitle:
        path = os.path.join(user_dir, f"{base_name}.srt")
        if os.path.exists(path):
            return FileResponse(open(path, 'rb'), as_attachment=True, filename=f"{base_name}.srt")

    if file_type == "txt" and file_obj.is_text:
        path = os.path.join(user_dir, f"{base_name}.txt")
        if os.path.exists(path):
            return FileResponse(open(path, 'rb'), as_attachment=True, filename=f"{base_name}.txt")

    if file_type == "zip" and file_obj.is_text and file_obj.is_subtitle:
        path = os.path.join(user_dir, f"{base_name}.zip")
        if os.path.exists(path):
            return FileResponse(open(path, 'rb'), as_attachment=True, filename=f"{base_name}.zip")

    messages.error(request, "فایل یافت نشد.")
    return redirect('file_list')
def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('file_list')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})