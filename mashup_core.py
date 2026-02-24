from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from moviepy.audio.AudioClip import AudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import os


class MashupError(Exception):
    """Raised when mashup generation fails."""


def _write_audio_compat(clip: AudioClip, output_path: Path) -> None:
    try:
        clip.write_audiofile(
            str(output_path),
            codec="mp3",
            verbose=False,
            logger=None,
        )
    except TypeError:
        # moviepy v2 dropped/changed some kwargs.
        clip.write_audiofile(str(output_path), codec="mp3")


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "output"


def validate_positive_int(value: str, minimum: int, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise MashupError(f"{name} must be an integer.") from exc
    if parsed <= minimum:
        raise MashupError(f"{name} must be greater than {minimum}.")
    return parsed


def _download_videos(singer_name: str, count: int, videos_dir: Path) -> list[Path]:
    search_count = max(count * 4, count + 10)
    query = f"ytsearch{search_count}:{singer_name} official video"
    output_template = str(videos_dir / "%(title).80s-%(id)s.%(ext)s")

    base_opts = {
        # Prefer a single progressive stream to avoid ffmpeg merge during download.
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "ignoreerrors": True,
        "restrictfilenames": True,
        "retries": 5,
        "sleep_interval_requests": 1,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    cookie_attempts: list[tuple[str, ...] | None] = [
        None,
        ("chrome",),
        ("edge",),
        ("firefox",),
    ]
    cookie_file = os.getenv("YTDLP_COOKIE_FILE", "").strip()
    downloaded: list[Path] = []

    for cookies_from_browser in cookie_attempts:
        ydl_opts = dict(base_opts)
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file
        if cookies_from_browser is not None:
            ydl_opts["cookiesfrombrowser"] = cookies_from_browser

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                entries = info.get("entries") or []

                downloaded = []
                for entry in entries:
                    if not entry:
                        continue
                    file_path = Path(ydl.prepare_filename(entry))
                    if not file_path.exists():
                        guessed = list(videos_dir.glob(f"*{entry.get('id', '')}*"))
                        if guessed:
                            file_path = guessed[0]
                    if file_path.exists():
                        downloaded.append(file_path)
        except DownloadError:
            continue

        if len(downloaded) >= count:
            break

    if len(downloaded) < count:
        raise MashupError(
            f"Could only download {len(downloaded)} videos for '{singer_name}'. "
            "Open YouTube in your browser first (logged in), or set YTDLP_COOKIE_FILE, then retry."
        )
    return downloaded[:count]


def _trim_audio(video_paths: Iterable[Path], seconds: int, audios_dir: Path) -> list[Path]:
    trimmed_files: list[Path] = []
    for idx, video_path in enumerate(video_paths, start=1):
        output_audio = audios_dir / f"track_{idx:02d}.mp3"
        with VideoFileClip(str(video_path)) as video_clip:
            if video_clip.audio is None:
                continue

            max_duration = float(video_clip.audio.duration or 0)
            end_time = min(float(seconds), max_duration)
            if end_time <= 0:
                continue

            # moviepy v1 uses subclip, moviepy v2 uses subclipped.
            if hasattr(video_clip.audio, "subclip"):
                trimmed_audio: AudioClip = video_clip.audio.subclip(0, end_time)
            else:
                trimmed_audio = video_clip.audio.subclipped(0, end_time)
            _write_audio_compat(trimmed_audio, output_audio)
            trimmed_audio.close()
            trimmed_files.append(output_audio)

    if not trimmed_files:
        raise MashupError("No audio could be extracted from downloaded videos.")
    return trimmed_files


def _merge_audio(audio_paths: Iterable[Path], output_file: Path) -> Path:
    clips: list[AudioFileClip] = []
    try:
        clips = [AudioFileClip(str(path)) for path in audio_paths]
        if not clips:
            raise MashupError("No audio clips available to merge.")
        merged = concatenate_audioclips(clips)
        _write_audio_compat(merged, output_file)
        merged.close()
    finally:
        for clip in clips:
            clip.close()
    return output_file


def create_mashup(
    singer_name: str,
    number_of_videos: int,
    audio_duration_sec: int,
    output_filename: str,
    base_work_dir: Path | None = None,
) -> Path:
    singer_name = singer_name.strip()
    if not singer_name:
        raise MashupError("Singer name cannot be empty.")

    if number_of_videos <= 10:
        raise MashupError("Number of videos must be greater than 10.")
    if audio_duration_sec <= 20:
        raise MashupError("Audio duration must be greater than 20 seconds.")
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin is None:
        try:
            import imageio_ffmpeg

            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_bin)
        except Exception as exc:
            raise MashupError(
                "ffmpeg is not installed or not in PATH. Install ffmpeg and retry."
            ) from exc

    target_output = Path(output_filename).expanduser().resolve()
    target_output.parent.mkdir(parents=True, exist_ok=True)

    temp_root: Path | None = None
    work_dir = base_work_dir
    if work_dir is None:
        temp_root = Path(tempfile.mkdtemp(prefix="mashup_"))
        work_dir = temp_root
    work_dir.mkdir(parents=True, exist_ok=True)

    videos_dir = work_dir / "videos"
    audios_dir = work_dir / "audios"
    videos_dir.mkdir(parents=True, exist_ok=True)
    audios_dir.mkdir(parents=True, exist_ok=True)

    try:
        if ffmpeg_bin:
            os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_bin)
        videos = _download_videos(singer_name, number_of_videos, videos_dir)
        clipped_audios = _trim_audio(videos, audio_duration_sec, audios_dir)
        merged_path = work_dir / f"{sanitize_filename(target_output.stem)}.mp3"
        _merge_audio(clipped_audios, merged_path)
        shutil.copy2(merged_path, target_output)
        return target_output
    except MashupError:
        raise
    except Exception as exc:  # pragma: no cover
        raise MashupError(f"Unexpected error while creating mashup: {exc}") from exc
    finally:
        if temp_root and temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
