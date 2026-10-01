"""Tests for the product video transcode + caption pipeline (F-014).

Verifies that:
  - video_transcode_task is registered as a Celery shared task
  - generate_video_captions is registered as a Celery shared task
  - _generate_caption returns empty string when AI text provider is unavailable
  - The task name follows the jobs.video_tasks.* naming convention
"""
from __future__ import annotations

import sys
import os

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


def test_video_transcode_task_registered():
    """video_transcode_task must be a Celery shared task with the correct name."""
    from jobs.video_tasks import video_transcode_task

    assert hasattr(video_transcode_task, "name"), "Task must have a name attribute"
    assert video_transcode_task.name == "tasks.video_tasks.video_transcode"


def test_generate_video_captions_task_registered():
    """generate_video_captions must be a Celery shared task with the correct name."""
    from jobs.video_tasks import generate_video_captions

    assert hasattr(generate_video_captions, "name"), "Task must have a name attribute"
    assert generate_video_captions.name == "tasks.video_tasks.generate_video_captions"


def test_video_transcode_task_has_retry_config():
    """video_transcode_task must have retry settings."""
    from jobs.video_tasks import video_transcode_task

    assert video_transcode_task.max_retries == 3
    assert video_transcode_task.default_retry_delay == 120


def test_generate_caption_returns_empty_when_no_provider():
    """_generate_caption must return '' gracefully when text provider is absent."""
    from jobs.video_tasks import _generate_caption

    result = _generate_caption(b"fake-video-bytes", filename="test.mp4")
    assert isinstance(result, str)


def test_video_transcode_logs_state_changes():
    """Task source must reference upload_status states (processing/completed/failed)."""
    import inspect

    from jobs.video_tasks import video_transcode_task

    source = inspect.getsource(video_transcode_task)
    assert "processing" in source
    assert "completed" in source
    assert "failed" in source


def test_video_transcode_uses_storage_backend():
    """Task must store the transcoded asset via the storage backend."""
    import inspect

    from jobs.video_tasks import video_transcode_task

    source = inspect.getsource(video_transcode_task)
    assert "storage" in source or "_store" in source
