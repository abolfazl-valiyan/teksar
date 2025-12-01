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
from celery.result import AsyncResult
from .transcribe import transcribe_audio_from_bytes,transcribe_video_from_bytes
# @login_required
# def upload_file(request):
#     if request.method == 'POST':
#         if 'file' not in request.FILES:
#             messages.error(request, 'هیچ فایلی آپلود نشده')
#             return redirect('upload_file')
#
#         uploaded_file = request.FILES['file']
#
#         mime = magic.Magic(mime=True)
#         mime_type = mime.from_buffer(uploaded_file.read(1024))
#         uploaded_file.seek(0)
#
#         if mime_type.startswith("video/"):
#             file_type = "video"
#         elif mime_type.startswith("audio/"):
#             file_type = "audio"
#         else:
#             messages.error(request, 'فقط فایل‌های صوتی یا ویدیویی مجاز هستند')
#             return redirect('upload_file')
#
#         want_srt = request.POST.get("is_subtitle") == "on"
#         want_txt = request.POST.get("is_text") == "on"
#
#         if not (want_srt or want_txt):
#             messages.error(request, "حداقل یکی از گزینه‌ها باید انتخاب شود.")
#             return redirect('upload_file')
#
#         file_data = uploaded_file.read()
#
#         new_file = File.objects.create(
#             user=request.user,
#             filename=uploaded_file.name,
#             data=file_data,
#             is_text=want_txt,
#             is_subtitle=want_srt,
#             status='pending'
#         )
#
#         if file_type == 'audio':
#             srt_text, txt_text = transcribe_audio_from_bytes(file_data, uploaded_file.name)
#         else:
#             try:
#                 srt_text, txt_text = transcribe_video_from_bytes(file_data, uploaded_file.name)
#             except RuntimeError as e:
#                 new_file.status = 'failed'
#                 new_file.error_message = str(e)
#                 new_file.save()
#                 messages.error(request, str(e))
#                 return redirect('upload_file')
#
#         # new_file.transcribed_text = txt_text if want_txt else None
#         # new_file.status = 'done'
#         # new_file.save()
#         task = process_file_task.delay(new_file.id)
#         new_file.task_id = task.id
#         new_file.save(update_fields=['task_id'])
#
#         base_name = os.path.splitext(uploaded_file.name)[0]
#
#         if want_srt and want_txt:
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
#                 with zipfile.ZipFile(temp_zip, 'w') as zipf:
#                     zipf.writestr(f"{base_name}.srt", srt_text)
#                     zipf.writestr(f"{base_name}.txt", txt_text)
#                 temp_zip_path = temp_zip.name
#
#             with open(temp_zip_path, "rb") as f:
#                 response = HttpResponse(f.read(), content_type="application/zip")
#                 response['Content-Disposition'] = f'attachment; filename="{base_name}.zip"'
#             os.remove(temp_zip_path)
#             return response
#
#         elif want_srt:
#             results_dir = os.path.join(settings.MEDIA_ROOT, "results")
#             os.makedirs(results_dir, exist_ok=True)
#             srt_path = os.path.join(results_dir, f"{base_name}.srt")
#             with open(srt_path, "w", encoding="utf-8") as srt_file:
#                 srt_file.write(srt_text)
#             response = HttpResponse(srt_text, content_type="application/x-subrip")
#             response['Content-Disposition'] = f'attachment; filename="{base_name}.srt"'
#             return response
#
#         else:
#             response = HttpResponse(txt_text, content_type="text/plain; charset=utf-8")
#             response['Content-Disposition'] = f'attachment; filename="{base_name}.txt"'
#             return response
#
#     return render(request, 'upload.html')
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
# @login_required
# def file_list(request):
#     files = File.objects.filter(user=request.user).order_by('-created_at')
#
#     for f in files:
#         display = 'در حال انجام'
#         if f.status == 'done':
#             display = 'اوکی'
#         elif f.status == 'failed':
#             display = 'ناموفق'
#
#         if f.task_id:
#             try:
#                 state = AsyncResult(f.task_id).state
#                 if state in ('PENDING', 'RECEIVED', 'STARTED', 'RETRY'):
#                     display = 'در حال انجام'
#                     if f.status != 'processing':
#                         f.status = 'processing'
#                         f.save(update_fields=['status'])
#                 elif state == 'SUCCESS':
#                     display = 'اوکی'
#                     if f.status != 'done':
#                         f.status = 'done'
#                         f.save(update_fields=['status'])
#                 elif state in ('FAILURE', 'REVOKED'):
#                     display = 'ناموفق'
#                     if f.status != 'failed':
#                         f.status = 'failed'
#                         f.save(update_fields=['status'])
#             except Exception:
#                 pass
#
#         f.display_status = display
#
#     return render(request, 'file_list.html', {'files': files})
@login_required
def file_list(request):
    files = File.objects.filter(user=request.user).order_by('-created_at')

    status_map = {
        'pending': 'در حال انتظار',
        'processing': 'در حال انجام',
        'done': 'اوکی',
        'failed': 'ناموفق',
    }

    for f in files:
        f.display_status = status_map.get(f.status, 'نامشخص')

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