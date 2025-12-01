import tempfile
import subprocess
import os
from django.conf import settings
from faster_whisper import WhisperModel

MODEL_DIR = os.path.join(settings.BASE_DIR, "models","whisper-large-v3-ct2")

if os.path.exists(MODEL_DIR) and os.listdir(MODEL_DIR):
    whisper_model = WhisperModel(
        MODEL_DIR,
        device="cpu",
        compute_type="int8",
        local_files_only=True
    )
else:
    os.makedirs(os.path.dirname(MODEL_DIR), exist_ok=True)
    whisper_model = WhisperModel(
        "large-v3",
        device="cpu",
        compute_type="int8",
        download_root=os.path.join(settings.BASE_DIR, "models")
    )


def format_timestamp(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def segments_to_srt(segments):
    srt_content = ""
    for i, segment in enumerate(segments, start=1):
        srt_content += f"{i}\n{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n{segment.text.strip()}\n\n"
    return srt_content
def transcribe_audio_from_bytes(file_bytes, filename):
    temp_path = os.path.join(settings.MEDIA_ROOT, "temp", filename)
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    segments_gen, info = whisper_model.transcribe(
        temp_path,
        language="fa",
        task="transcribe",
        vad_filter=True,
        vad_parameters={
            "threshold": 0.7,
            "min_speech_duration_ms": 250,
            "min_silence_duration_ms": 1000,
        },
        beam_size=10,
        temperature=0.0,
        no_speech_threshold=0.7,
        log_prob_threshold=-0.5,
        compression_ratio_threshold=2.0,
    )

    segments = list(segments_gen)

    srt_text = segments_to_srt(segments)
    txt_text = " ".join([seg.text.strip() for seg in segments])
    os.remove(temp_path)
    return srt_text, txt_text


def transcribe_video_from_bytes(file_bytes, filename):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_video:
        temp_video.write(file_bytes)
        temp_video_path = temp_video.name

    temp_audio_path = tempfile.mktemp(suffix=".wav")

    command = [
        "ffmpeg",
        "-i", temp_video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        temp_audio_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        os.remove(temp_video_path)
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise RuntimeError(f"خطا : {e}")

    with open(temp_audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    srt_text, txt_text = transcribe_audio_from_bytes(audio_bytes, os.path.basename(temp_audio_path))

    os.remove(temp_video_path)
    os.remove(temp_audio_path)

    return srt_text, txt_text