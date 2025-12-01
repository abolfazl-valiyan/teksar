from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import magic
from web.views import transcribe_audio_from_bytes, transcribe_video_from_bytes
from .serializers import *

ALLOWED_AUDIO = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/x-m4a']
ALLOWED_VIDEO = ['video/mp4', 'video/quicktime', 'video/x-matroska']

@api_view(['POST'])
def upload_file_api(request):
    if 'file' not in request.FILES:
        return Response({"error": "هیچ فایلی ارسال نشده است."}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    want_txt = request.data.get('is_text', 'true').lower() == 'true'
    want_srt = request.data.get('is_subtitle', 'false').lower() == 'true'

    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(uploaded_file.read(1024))
    uploaded_file.seek(0)

    if mime_type in ALLOWED_AUDIO:
        file_type = 'audio'
    elif mime_type in ALLOWED_VIDEO:
        file_type = 'video'
    else:
        return Response({
            "error": "فقط فایل‌های صوتی یا ویدیویی مجاز هستند."
        }, status=status.HTTP_400_BAD_REQUEST)

    file_data = uploaded_file.read()

    new_file = File.objects.create(
        filename=uploaded_file.name,
        data=file_data,
        is_text=want_txt,
        is_subtitle=want_srt,
        status='processing'
    )

    try:
        if file_type == 'audio':
            srt_text, txt_text = transcribe_audio_from_bytes(file_data, uploaded_file.name)
        else:
            srt_text, txt_text = transcribe_video_from_bytes(file_data, uploaded_file.name)
    except Exception as e:
        new_file.status = 'failed'
        new_file.save()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    new_file.transcribed_text = txt_text if want_txt else None
    new_file.status = 'done'
    new_file.save()

    return Response({
        "filename": new_file.filename,
        "srt_content": srt_text if want_srt else None,
        "txt_content": txt_text if want_txt else None,
        "status": new_file.status
    })

@api_view(['GET'])
def subtitle_list_api(request):
    files = File.objects.filter(is_subtitle=True).order_by('-id')
    serializer = FileSubtitleSerializer(files, many=True)
    return Response(serializer.data)
@api_view(['GET', 'DELETE'])
def subtitle_detail_api(request, pk):
    try:
        file = File.objects.get(pk=pk, is_subtitle=True)
    except File.DoesNotExist:
        return Response({"error": "فایل مورد نظر پیدا نشد."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = FileDetailSerializer(file)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        file.delete()
        return Response({"message": "فایل با موفقیت حذف شد."}, status=status.HTTP_204_NO_CONTENT)