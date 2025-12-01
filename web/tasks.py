import os
from .models import File
from celery import shared_task
from .transcribe import transcribe_video_from_bytes, transcribe_audio_from_bytes
import zipfile
from django.conf import settings

@shared_task(bind=True)
def process_file_task(self, file_id):
    file_obj = File.objects.get(id=file_id)
    file_obj.status = 'processing'
    file_obj.save(update_fields=['status'])

    try:
        if file_obj.filename.lower().split('.')[-1] in {'mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'}:
            srt_text, txt_text = transcribe_audio_from_bytes(file_obj.data, file_obj.filename)
        else:
            srt_text, txt_text = transcribe_video_from_bytes(file_obj.data, file_obj.filename)

        base_name = os.path.splitext(file_obj.filename)[0]
        results_dir = os.path.join(settings.MEDIA_ROOT, "results", str(file_obj.user.id))
        os.makedirs(results_dir, exist_ok=True)

        if file_obj.is_text:
            txt_path = os.path.join(results_dir, f"{base_name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt_text)

        if file_obj.is_subtitle:
            srt_path = os.path.join(results_dir, f"{base_name}.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_text)

        if file_obj.is_text and file_obj.is_subtitle:
            zip_path = os.path.join(results_dir, f"{base_name}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(txt_path, f"{base_name}.txt")
                zf.write(srt_path, f"{base_name}.srt")

        file_obj.transcribed_text = txt_text if file_obj.is_text else None
        file_obj.srt_content = srt_text if file_obj.is_subtitle else None
        file_obj.status = 'done'
        file_obj.save()

    except Exception as e:
        file_obj.status = 'failed'
        file_obj.error_message = str(e)
        file_obj.save()
        raise
