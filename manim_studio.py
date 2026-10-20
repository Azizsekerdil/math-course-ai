# -*- coding: utf-8 -*-
"""Editable Manim scenes and an in-app MP4 preview for Math Course AI.

The main application uses Tkinter, so this module deliberately does not import
Qt or start another GUI event loop.  Rendering happens in a standard-library
thread and communicates with Tk through a queue; Tk widgets are only ever
updated from the main thread.

Manim scripts are Python programs.  The studio therefore makes the execution
boundary visible and requires a per-session acknowledgement before it launches
one.  It is for code the person operating the app has chosen to run, not for
automatically running code written by an AI model.
"""

from __future__ import annotations

import ast
import importlib.util
import keyword
import os
from pathlib import Path
from queue import Empty, Full, Queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone

import tkinter as tk
from tkinter import messagebox, ttk

from app_paths import exports_dir
from mca_common import RoundedButton, THEME


DEFAULT_SCENE_NAME = "SoruCozumu"
MANIM_PYTHON_ENV = "MATH_COURSE_AI_MANIM_PYTHON"
DEFAULT_SCENE_CODE = '''from manim import *


class SoruCozumu(Scene):
    def construct(self):
        title = Text("Manim Studio'ya Hoş Geldiniz", font_size=42)
        equation = Text("x^2 - 5x + 6 = 0", font_size=48)
        roots = Text("x = 2 veya x = 3", font_size=42)

        self.play(Write(title))
        self.wait(0.5)
        self.play(title.animate.to_edge(UP), Write(equation))
        self.wait(0.5)
        self.play(Transform(equation, roots))
        self.wait(1)
'''


# The order is part of the UI contract: medium quality is the default.
QUALITY_PRESETS = {
    "low": {"flag": "-ql", "folder": "480p15", "tr": "Hızlı (480p15)",
            "en": "Fast (480p15)"},
    "medium": {"flag": "-qm", "folder": "720p30", "tr": "Standart (720p30)",
               "en": "Standard (720p30)"},
    "high": {"flag": "-qh", "folder": "1080p60", "tr": "Yüksek (1080p60)",
             "en": "High (1080p60)"},
}
QUALITY_KEYS = tuple(QUALITY_PRESETS)
# Keep a long render's UI memory use bounded even if a scene prints in a loop.
MAX_LOG_CHARS = 160_000
MAX_LOG_EVENT_CHARS = 4_000
MAX_EVENTS_PER_TICK = 60


TEXT = {
    "tr": {
        "title": "🎬 Manim Animasyon Stüdyosu",
        "code": "Manim Python Kodu",
        "scene": "Sahne sınıfı:",
        "detect": "Algıla",
        "quality": "Render kalitesi:",
        "render": "▶ Oluştur ve Oynat",
        "cancel": "■ İptal",
        "output_folder": "📁 Çıktı klasörü",
        "logs": "Canlı derleme günlüğü",
        "preview": "Animasyon önizleme",
        "play": "▶ Oynat",
        "pause": "⏸ Duraklat",
        "stop": "■ Durdur",
        "mute": "🔇 Sessiz",
        "unmute": "🔊 Sesi aç",
        "open_video": "↗ Dışarıda aç",
        "volume": "Ses:",
        "run_confirm": "Bu kodu kendi bilgisayarımda çalıştırmanın riskini anlıyorum.",
        "run_warning": "Yalnızca güvendiğiniz Manim kodunu çalıştırın; kod, mevcut kullanıcı izinleriyle Python olarak çalışır.",
        "ready": "Manim kodunuzu düzenleyin, kaliteyi seçin ve render'ı başlatın.",
        "rendering": "Manim render işlemi arka planda çalışıyor…",
        "cancel_requested": "İptal isteği gönderildi; Manim işlemi sonlandırılıyor…",
        "render_complete": "Render başarıyla tamamlandı. Video oynatılıyor.",
        "render_complete_no_player": "Render tamamlandı. Uygulama içi oynatma için VLC kurulumu gerekli.",
        "cancelled": "Render iptal edildi.",
        "empty_code": "Lütfen render edilecek Manim kodunu girin.",
        "confirm_needed": "Kod çalıştırmadan önce güvenlik onay kutusunu işaretleyin.",
        "invalid_scene": "Sahne sınıfı geçerli bir Python sınıf adı olmalıdır.",
        "manim_missing": "Manim bu Python ortamında kurulu değil. Kurulum: pip install manim",
        "manim_python_missing": "Paketlenmiş uygulama için Manim yorumlayıcısı bulunamadı. MATH_COURSE_AI_MANIM_PYTHON değişkenini Manim kurulu python.exe yoluna ayarlayın.",
        "player_missing": "Uygulama içi MP4 oynatma için python-vlc ve VLC Media Player (libVLC) gerekir.",
        "player_playback_failed": "Video oynatma başlatılamadı. Videoyu dışarıda açabilirsiniz.",
        "player_help": "Önizleme için: pip install python-vlc  — ayrıca VLC Media Player'ı kurun.",
        "no_video": "Henüz render edilmiş video yok.",
        "found_scene": "Algılanan sahne: {name}",
        "scene_default": "Sahne bulunamadı; varsayılan kullanılacak: {name}",
        "command": "Komut:",
        "starting": "Geçici render alanı hazırlanıyor…",
        "video_not_found": "Manim başarılı döndü fakat bir MP4 çıktısı bulunamadı.",
        "render_failed": "Manim {code} çıkış koduyla sonlandı. Ayrıntılar günlükte.",
        "system_error": "Sistem hatası: {error}",
        "time": "{current} / {total}",
    },
    "en": {
        "title": "🎬 Manim Animation Studio",
        "code": "Manim Python Code",
        "scene": "Scene class:",
        "detect": "Detect",
        "quality": "Render quality:",
        "render": "▶ Render and Play",
        "cancel": "■ Cancel",
        "output_folder": "📁 Output folder",
        "logs": "Live render log",
        "preview": "Animation preview",
        "play": "▶ Play",
        "pause": "⏸ Pause",
        "stop": "■ Stop",
        "mute": "🔇 Mute",
        "unmute": "🔊 Unmute",
        "open_video": "↗ Open externally",
        "volume": "Volume:",
        "run_confirm": "I understand that this code will run on my computer.",
        "run_warning": "Only run Manim code you trust; it runs as Python with your current user permissions.",
        "ready": "Edit a Manim scene, select a quality, and start rendering.",
        "rendering": "Manim is rendering in the background…",
        "cancel_requested": "Cancellation requested; stopping the Manim process…",
        "render_complete": "Render completed. Playing the video.",
        "render_complete_no_player": "Render completed. Install VLC for in-app playback.",
        "cancelled": "Render cancelled.",
        "empty_code": "Enter Manim code to render first.",
        "confirm_needed": "Tick the safety acknowledgement before running code.",
        "invalid_scene": "The scene class must be a valid Python class name.",
        "manim_missing": "Manim is not installed in this Python environment. Install it with: pip install manim",
        "manim_python_missing": "No Manim interpreter was found for the packaged app. Set MATH_COURSE_AI_MANIM_PYTHON to the python.exe path where Manim is installed.",
        "player_missing": "In-app MP4 playback needs python-vlc and VLC Media Player (libVLC).",
        "player_playback_failed": "Video playback could not be started. You can open the video externally.",
        "player_help": "For preview: pip install python-vlc  — also install VLC Media Player.",
        "no_video": "No rendered video yet.",
        "found_scene": "Detected scene: {name}",
        "scene_default": "No scene found; using default: {name}",
        "command": "Command:",
        "starting": "Preparing an isolated render folder…",
        "video_not_found": "Manim completed but no MP4 output was found.",
        "render_failed": "Manim exited with code {code}. See the log for details.",
        "system_error": "System error: {error}",
        "time": "{current} / {total}",
    },
}


def quality_flag(quality_key: str) -> str:
    """Return Manim's CLI flag for one of the studio's quality options."""
    return QUALITY_PRESETS.get(quality_key, QUALITY_PRESETS["medium"])["flag"]


def is_manim_available() -> bool:
    """Check availability without importing Manim (which is expensive at startup).

    A frozen GUI cannot import an external Manim installation itself.  For that
    case this intentionally checks only whether an interpreter target exists;
    ``python -m manim`` runs in the background worker and streams an exact
    missing-package/setup error instead of blocking Tk for a probe timeout.
    """
    if getattr(sys, "frozen", False):
        return manim_python_command() is not None
    try:
        return importlib.util.find_spec("manim") is not None
    except (AttributeError, ImportError, ModuleNotFoundError, ValueError):
        return False


def manim_python_command() -> list[str] | None:
    """Return the interpreter that can run ``-m manim`` without using a shell.

    In source mode it is exactly this application's interpreter, preserving the
    expected virtual-environment behaviour.  A PyInstaller executable is *not*
    a Python interpreter, so a frozen build must use an explicitly configured
    interpreter or one found on ``PATH``.  The environment variable deliberately
    accepts one executable path, not a shell command, to keep argument handling
    injection-free.
    """
    if not getattr(sys, "frozen", False):
        return [sys.executable]
    configured = (os.getenv(MANIM_PYTHON_ENV) or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_file():
            return [str(path)]
        return None
    # A nearby base interpreter is useful for some one-folder launchers.  It
    # must differ from the frozen GUI binary or ``-m manim`` would relaunch the
    # app itself.
    base = str(getattr(sys, "_base_executable", "") or "")
    if base and Path(base).is_file() and os.path.normcase(base) != os.path.normcase(sys.executable):
        return [base]
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            return [found]
    return None


def detect_scene_name(code: str, default: str = DEFAULT_SCENE_NAME) -> str:
    """Find the first conventional Manim Scene subclass in pasted source.

    The result only selects a scene for Manim's CLI; it is not a security
    validator.  If a user is still editing syntactically invalid code, retain a
    predictable default and let Manim present the detailed parse error in its
    live log.
    """
    try:
        tree = ast.parse(code or "")
    except (SyntaxError, TypeError, ValueError):
        return default
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            name = ""
            if isinstance(base, ast.Name):
                name = base.id
            elif isinstance(base, ast.Attribute):
                name = base.attr
            if name in {
                "Scene", "ThreeDScene", "SpecialThreeDScene", "MovingCameraScene",
                "ZoomedScene", "VectorScene", "LinearTransformationScene",
                "InteractiveScene",
            }:
                return node.name
    return default


def resolve_scene_name(code: str, requested_name: str,
                       user_selected: bool = False) -> str:
    """Choose the scene to render without surprising an explicit selection.

    The template starts with ``SoruCozumu`` in the scene field.  When someone
    replaces the template with a pasted scene, that untouched default must not
    make the first Render click target a class that no longer exists.  A name
    entered deliberately in the field remains authoritative, which is useful
    for scripts containing several scene classes.
    """
    requested = (requested_name or "").strip()
    detected = detect_scene_name(code, "")
    if detected and not user_selected:
        return detected
    return requested or detected or DEFAULT_SCENE_NAME


def is_valid_scene_name(scene_name: str) -> bool:
    """Return whether a value can name a Python/Manim scene class."""
    return bool(scene_name and scene_name.isidentifier() and not keyword.iskeyword(scene_name))


def is_error_log_line(text: str) -> bool:
    """Recognise common renderer failure text for the red live-log tag."""
    value = (text or "").casefold()
    return any(marker in value for marker in (
        "traceback", "syntaxerror", "error", "exception", "fatal", "failed",
    ))


def build_manim_command(script_path: Path | str, media_dir: Path | str,
                        quality: str, scene_name: str) -> list[str]:
    """Build the argument-vector form of the render command (never a shell)."""
    if quality not in {preset["flag"] for preset in QUALITY_PRESETS.values()}:
        raise ValueError("Unsupported Manim quality flag: %r" % quality)
    launcher = manim_python_command()
    if launcher is None:
        raise RuntimeError(
            "No Python interpreter is available for Manim. In a packaged app, "
            "set %s to the full path of a Python interpreter with Manim installed."
            % MANIM_PYTHON_ENV)
    return launcher + [
        "-m", "manim", "-v", "WARNING", quality,
        "--media_dir", str(media_dir), str(script_path), scene_name,
    ]


def command_for_log(command: list[str]) -> str:
    """Render a readable command line without passing it through a shell."""
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    try:
        import shlex
        return shlex.join(command)
    except (AttributeError, ImportError):
        return " ".join(repr(part) if " " in part else part for part in command)


def find_rendered_video(media_dir: Path | str, scene_name: str = "") -> Path | None:
    """Return the newest MP4 from this render only, preferring the named scene."""
    root = Path(media_dir)
    if not root.is_dir():
        return None
    try:
        candidates = [path for path in root.rglob("*.mp4") if path.is_file()]
    except OSError:
        return None
    if scene_name:
        named = [path for path in candidates if path.stem == scene_name]
        if named:
            candidates = named
    if not candidates:
        return None
    try:
        return max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.stat().st_size))
    except OSError:
        return None


def studio_output_root() -> Path:
    """Return a durable, user-visible output root with a safe temp fallback."""
    try:
        root = exports_dir() / "animations" / "manim_studio"
        root.mkdir(parents=True, exist_ok=True)
        return root
    except OSError:
        root = Path(tempfile.gettempdir()) / "MathCourseAI" / "manim_studio"
        root.mkdir(parents=True, exist_ok=True)
        return root


def _format_time(milliseconds: int | float) -> str:
    total_seconds = max(0, int(float(milliseconds) / 1000))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


class ManimRenderWorker(threading.Thread):
    """Run a Manim CLI render without ever touching Tk from this thread.

    Events are tuples put in ``events``:
    ``("log", stream, text)``, ``("finished", video_path)``,
    ``("error", message)``, or ``("cancelled", message)``.
    """

    def __init__(self, code: str, quality: str, scene_name: str,
                 events: Queue, output_root: Path | str | None = None,
                 popen_factory=None):
        super().__init__(name="ManimRenderWorker", daemon=True)
        self.code = code
        self.quality = quality
        self.scene_name = scene_name
        self.events = events
        self.output_root = Path(output_root) if output_root is not None else studio_output_root()
        self._popen_factory = popen_factory or subprocess.Popen
        self._cancel_requested = threading.Event()
        self._process_lock = threading.Lock()
        self._terminal_lock = threading.Lock()
        self._termination_lock = threading.Lock()
        self._terminal_emitted = False
        self._termination_sent = False
        self._process = None
        self._process_group_id: int | None = None
        self._dropped_log_events = 0
        self.run_dir: Path | None = None
        self.media_dir: Path | None = None
        self.script_path: Path | None = None

    def _emit(self, *event) -> None:
        # A renderer can produce enormous logs (or a pasted script can print in
        # a loop).  Dropping excess *log* lines preserves a responsive Tk event
        # loop; lifecycle events evict an old queued item rather than vanishing.
        try:
            self.events.put_nowait(event)
            return
        except Full:
            if event and event[0] == "log":
                self._dropped_log_events += 1
                return
        try:
            self.events.get_nowait()
        except Empty:
            pass
        try:
            self.events.put_nowait(event)
        except Full:
            # A simultaneous GUI drain can close this tiny race.  There is no
            # safe reason to block a process-output reader here.
            if event and event[0] == "log":
                self._dropped_log_events += 1

    def cancel(self) -> bool:
        """Request cancellation unless a terminal result already won the race."""
        with self._terminal_lock:
            if self._terminal_emitted:
                return False
            self._cancel_requested.set()
        # ``taskkill /T`` can briefly block on Windows.  Cancellation originates
        # from Tk's main thread, so dispatch the actual process-tree teardown
        # and keep the interface responsive.
        self._request_termination()
        return True

    def _emit_terminal(self, kind: str, payload: str) -> bool:
        """Emit exactly one terminal event with an atomic cancel/completion choice.

        A renderer can exit just as the learner clicks Cancel.  The first side
        that takes this lock wins: a queued completion is never later relabelled
        as cancelled, while a cancellation already accepted here cannot be
        overwritten by a late success/error event.
        """
        with self._terminal_lock:
            if self._terminal_emitted:
                return False
            event = (("cancelled", "Render cancelled.")
                     if self._cancel_requested.is_set() else (kind, payload))
            self._terminal_emitted = True
        self._emit(*event)
        return event[0] == kind

    def _request_termination(self) -> None:
        """Schedule exactly one non-blocking teardown for a published child."""
        with self._process_lock:
            process = self._process
            process_group_id = self._process_group_id
        if process is None:
            # ``run`` checks again immediately after it publishes a process,
            # covering cancellation while Popen is still being constructed.
            return
        with self._termination_lock:
            if self._termination_sent:
                return
            self._termination_sent = True
        threading.Thread(
            target=self._terminate_process,
            args=(process, process_group_id),
            name="ManimProcessTermination",
            # This is intentionally non-daemon.  It never blocks Tk itself,
            # but Python waits for its bounded taskkill/terminate request on
            # app shutdown instead of allowing a Manim child to outlive the
            # closing desktop application.
            daemon=False,
        ).start()

    def _terminate_process(self, process=None, process_group_id=None) -> None:
        if process is None:
            with self._process_lock:
                process = self._process
                process_group_id = self._process_group_id
        if process is None:
            return
        try:
            pid = getattr(process, "pid", None)
            if os.name == "nt" and pid:
                # Manim may leave ffmpeg as a child holding stdout open.  Ask
                # Windows to stop the current tree.  ``taskkill`` is
                # best-effort if the Python parent changes state mid-request.
                result = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, check=False,
                    timeout=5,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                # ``taskkill`` can fail because the process has just changed
                # state or a system policy rejected tree traversal.  Do not
                # leave the direct Python renderer running in that case.
                if result.returncode != 0:
                    process.terminate()
            elif os.name != "nt" and (process_group_id or pid):
                # ``start_new_session`` makes the original child PID the
                # process-group ID.  Store it at launch rather than asking
                # ``getpgid(parent_pid)`` later: the parent may already be
                # gone while ffmpeg still belongs to its process group.
                os.killpg(process_group_id or pid, signal.SIGTERM)
            elif process.poll() is None:
                process.terminate()
        except (AttributeError, OSError, subprocess.SubprocessError, ProcessLookupError):
            try:
                process.terminate()
            except (AttributeError, OSError, subprocess.SubprocessError):
                pass
            pass

    def _make_run_dir(self) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        root = self.output_root
        root.mkdir(parents=True, exist_ok=True)
        # The microsecond timestamp prevents two quick clicks from sharing a
        # script or output tree; the counter is a harmless fallback for clocks
        # with lower precision.
        candidate = root / ("render_" + stamp)
        counter = 1
        while candidate.exists():
            candidate = root / ("render_%s_%d" % (stamp, counter))
            counter += 1
        candidate.mkdir(parents=True, exist_ok=False)
        return candidate

    def run(self) -> None:
        process = None
        try:
            if self._cancel_requested.is_set():
                self._emit_terminal("cancelled", "Render cancelled before it started.")
                return
            self.run_dir = self._make_run_dir()
            self.media_dir = self.run_dir / "media"
            self.script_path = self.run_dir / "temp_scene.py"
            self.script_path.write_text(self.code, encoding="utf-8")
            command = build_manim_command(self.script_path, self.media_dir,
                                          self.quality, self.scene_name)
            self._emit("started", str(self.run_dir), command_for_log(command))
            if self._cancel_requested.is_set():
                self._emit_terminal("cancelled", "Render cancelled before it started.")
                return
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            if os.name == "nt":
                creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            process = self._popen_factory(
                command,
                cwd=str(self.run_dir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
                start_new_session=(os.name != "nt"),
            )
            with self._process_lock:
                self._process = process
                self._process_group_id = (getattr(process, "pid", None)
                                          if os.name != "nt" else None)
                cancelled_during_launch = self._cancel_requested.is_set()
            # ``cancel()`` can land while ``Popen`` is creating the child.  It
            # sees no process in that narrow window, so re-check immediately
            # after publishing the child before a blocking stdout.readline().
            if cancelled_during_launch:
                self._request_termination()

            stream = getattr(process, "stdout", None)
            if stream is not None:
                for line in iter(stream.readline, ""):
                    if self._cancel_requested.is_set():
                        # Do not drain a large buffered stream after cancel or
                        # invoke taskkill once per line.  The one-shot teardown
                        # above closes the child and lets ``wait`` finish.
                        self._request_termination()
                        break
                    if line:
                        self._emit("log", "output", line.rstrip("\r\n"))
            if self._cancel_requested.is_set():
                self._request_termination()

            return_code = process.wait()
            if self._cancel_requested.is_set():
                self._emit_terminal("cancelled", "Render cancelled.")
            elif return_code != 0:
                if self._dropped_log_events:
                    self._emit("log", "system", "… %d log lines were skipped to keep the UI responsive."
                               % self._dropped_log_events)
                self._emit_terminal("error", "Manim exited with code %s. See the log for details." % return_code)
            else:
                video_path = find_rendered_video(self.media_dir, self.scene_name)
                if self._dropped_log_events:
                    self._emit("log", "system", "… %d log lines were skipped to keep the UI responsive."
                               % self._dropped_log_events)
                if video_path is None:
                    self._emit_terminal("error", "Manim completed but no MP4 output was found.")
                else:
                    self._emit_terminal("finished", str(video_path))
        except Exception as exc:
            self._emit_terminal("error", "System error: %s" % exc)
        finally:
            try:
                if process is not None and getattr(process, "stdout", None) is not None:
                    process.stdout.close()
            except (AttributeError, OSError):
                pass
            with self._process_lock:
                self._process = None
                self._process_group_id = None


class EmbeddedVlcPlayer:
    """A tiny Tk host around optional python-vlc/libVLC playback.

    ``python-vlc`` is imported only when an MP4 is ready, so simply opening the
    studio remains quick and works in the base (no optional dependencies) app.
    """

    def __init__(self, host: tk.Misc):
        self.host = host
        self._vlc = None
        self._instance = None
        self._player = None
        self._media = None
        self.error = ""

    @property
    def available(self) -> bool:
        return self._player is not None

    def _ensure(self) -> bool:
        if self._player is not None:
            return True
        try:
            import vlc  # Optional: it dynamically loads the installed libVLC runtime.
            self._vlc = vlc
            self._instance = vlc.Instance("--no-video-title-show", "--quiet")
            self._player = self._instance.media_player_new()
            self._attach_host()
            self.error = ""
            return True
        except Exception as exc:
            self.error = str(exc) or exc.__class__.__name__
            self.release()
            return False

    def _attach_host(self) -> None:
        if self._player is None:
            return
        self.host.update_idletasks()
        window_id = self.host.winfo_id()
        if sys.platform.startswith("win"):
            self._player.set_hwnd(window_id)
        elif sys.platform == "darwin":
            self._player.set_nsobject(window_id)
        else:
            self._player.set_xwindow(window_id)

    def load(self, path: Path | str) -> bool:
        if not self._ensure():
            return False
        try:
            self._attach_host()
            path_str = str(Path(path).resolve())
            self._media = self._instance.media_new_path(path_str)
            self._player.set_media(self._media)
            self.error = ""
            return True
        except Exception as exc:
            self.error = str(exc) or exc.__class__.__name__
            return False

    def play(self) -> bool:
        try:
            if self._player is None:
                return False
            self._attach_host()
            result = self._player.play()
            if result not in (None, 0):
                self.error = "libVLC could not start playback (code %s)." % result
                return False
            self.error = ""
            return True
        except Exception as exc:
            self.error = str(exc) or exc.__class__.__name__
            return False

    def pause(self, paused: bool) -> None:
        if self._player is None:
            return
        try:
            self._player.set_pause(1 if paused else 0)
        except Exception:
            pass

    def stop(self) -> None:
        if self._player is None:
            return
        try:
            self._player.stop()
        except Exception:
            pass

    def is_playing(self) -> bool:
        try:
            return bool(self._player is not None and self._player.is_playing())
        except Exception:
            return False

    def duration_ms(self) -> int:
        try:
            return max(0, int(self._player.get_length())) if self._player is not None else 0
        except Exception:
            return 0

    def position_ms(self) -> int:
        try:
            return max(0, int(self._player.get_time())) if self._player is not None else 0
        except Exception:
            return 0

    def seek(self, milliseconds: int | float) -> None:
        if self._player is None:
            return
        try:
            self._player.set_time(max(0, int(float(milliseconds))))
        except Exception:
            pass

    def set_volume(self, volume: int | float) -> None:
        if self._player is None:
            return
        try:
            self._player.audio_set_volume(max(0, min(100, int(float(volume)))))
        except Exception:
            pass

    def set_mute(self, muted: bool) -> None:
        if self._player is None:
            return
        try:
            self._player.audio_set_mute(bool(muted))
        except Exception:
            pass

    def release(self) -> None:
        for item in (self._player, self._media, self._instance):
            try:
                if item is not None:
                    item.release()
            except Exception:
                pass
        self._player = None
        self._media = None
        self._instance = None
        self._vlc = None


class ManimStudio(ttk.Frame):
    """The lazily-created workspace panel used by ``MathCourseApp``."""

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        # The worker may produce much faster than the GUI can paint.  A bounded
        # queue plus bounded draining prevents log spam from freezing the tab.
        self.events: Queue = Queue(maxsize=1200)
        self.worker: ManimRenderWorker | None = None
        self.render_root = studio_output_root()
        self.last_video_path: Path | None = None
        self._destroyed = False
        self._event_after_id = None
        self._playback_after_id = None
        self._updating_timeline = False
        self._timeline_dragging = False
        self._muted = False
        self._scene_name_is_manual = False
        self._setting_scene_name = False
        self._render_error_in_log = False
        self._build_ui()
        self.refresh_ui()
        self._schedule_event_poll()
        self._schedule_playback_poll()
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _lang(self) -> str:
        return "en" if getattr(self.app, "language", "tr") == "en" else "tr"

    def _t(self, key: str, **values) -> str:
        return TEXT[self._lang()][key].format(**values)

    def _build_ui(self) -> None:
        self.header_label = ttk.Label(self, style="Header.TLabel")
        self.header_label.pack(fill="x", padx=12, pady=(10, 3))

        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.left_panel = ttk.Frame(paned, style="Panel.TFrame")
        self.right_panel = ttk.Frame(paned, style="Panel.TFrame")
        paned.add(self.left_panel, weight=1)
        paned.add(self.right_panel, weight=1)

        self.code_label = ttk.Label(self.left_panel, style="Muted.TLabel")
        self.code_label.pack(anchor="w", padx=8, pady=(8, 2))
        editor_shell = tk.Frame(self.left_panel, bg=THEME["border"])
        editor_shell.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.code_editor = tk.Text(
            editor_shell, wrap="none", undo=True, height=22,
            bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"],
            selectbackground=THEME["accent_soft"], selectforeground=THEME["text"],
            relief="flat", borderwidth=0, font=("Consolas", 10),
        )
        code_y = ttk.Scrollbar(editor_shell, orient="vertical", command=self.code_editor.yview)
        code_x = ttk.Scrollbar(editor_shell, orient="horizontal", command=self.code_editor.xview)
        self.code_editor.configure(yscrollcommand=code_y.set, xscrollcommand=code_x.set)
        code_y.pack(side="right", fill="y")
        code_x.pack(side="bottom", fill="x")
        self.code_editor.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self.code_editor.insert("1.0", DEFAULT_SCENE_CODE)

        scene_row = ttk.Frame(self.left_panel, style="Panel.TFrame")
        scene_row.pack(fill="x", padx=8, pady=(0, 4))
        self.scene_label = ttk.Label(scene_row, style="Muted.TLabel")
        self.scene_label.pack(side="left")
        self.scene_name_var = tk.StringVar(value=DEFAULT_SCENE_NAME)
        self.scene_entry = ttk.Entry(scene_row, textvariable=self.scene_name_var, width=24)
        self.scene_entry.pack(side="left", fill="x", expand=True, padx=(6, 4))
        self.scene_entry.bind("<KeyRelease>", self._mark_scene_name_manual, add="+")
        self.scene_entry.bind("<<Paste>>", self._mark_scene_name_manual, add="+")
        self.detect_button = RoundedButton(scene_row, command=self.detect_scene,
                                           parent_bg=THEME["panel"], radius=10, padx=10, pady=5)
        self.detect_button.pack(side="left")

        quality_row = ttk.Frame(self.left_panel, style="Panel.TFrame")
        quality_row.pack(fill="x", padx=8, pady=4)
        self.quality_label = ttk.Label(quality_row, style="Muted.TLabel")
        self.quality_label.pack(side="left")
        self.quality_combo = ttk.Combobox(
            quality_row, state="readonly", width=24,
            values=[QUALITY_PRESETS[key][self._lang()] for key in QUALITY_KEYS],
        )
        self.quality_combo.pack(side="left", padx=(6, 0))
        self.quality_combo.current(QUALITY_KEYS.index("medium"))

        self.confirm_var = tk.BooleanVar(value=False)
        self.confirm_check = tk.Checkbutton(
            self.left_panel, variable=self.confirm_var, anchor="w", justify="left",
            wraplength=560, bg=THEME["panel"], fg=THEME["text"],
            activebackground=THEME["panel"], activeforeground=THEME["text"],
            selectcolor=THEME["surface"], font=("Segoe UI", 9, "bold"),
        )
        self.confirm_check.pack(fill="x", padx=8, pady=(8, 1))
        self.warning_label = tk.Label(
            self.left_panel, justify="left", anchor="w", wraplength=590,
            bg=THEME["panel"], fg=THEME["danger"], font=("Segoe UI", 8),
        )
        self.warning_label.pack(fill="x", padx=12, pady=(0, 7))

        render_row = ttk.Frame(self.left_panel, style="Panel.TFrame")
        render_row.pack(fill="x", padx=8, pady=(0, 8))
        self.render_button = RoundedButton(
            render_row, command=self.start_render, parent_bg=THEME["panel"],
            bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B", radius=11,
            padx=14, pady=7,
        )
        self.render_button.pack(side="left", padx=(0, 4))
        self.cancel_button = RoundedButton(render_row, command=self.cancel_render,
                                           parent_bg=THEME["panel"], radius=11, padx=12, pady=7)
        self.cancel_button.pack(side="left", padx=4)
        self.cancel_button.config(state="disabled")
        self.output_button = RoundedButton(render_row, command=self.open_output_folder,
                                           parent_bg=THEME["panel"], radius=11, padx=12, pady=7)
        self.output_button.pack(side="right")

        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.left_panel, textvariable=self.status_var, justify="left", anchor="w",
            wraplength=600, bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 9),
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 4))

        self.logs_label = ttk.Label(self.left_panel, style="Muted.TLabel")
        self.logs_label.pack(anchor="w", padx=8, pady=(4, 2))
        log_shell = tk.Frame(self.left_panel, bg=THEME["border"])
        log_shell.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_box = tk.Text(
            log_shell, wrap="word", height=10, state="normal",
            bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"],
            relief="flat", borderwidth=0, font=("Consolas", 9),
        )
        log_y = ttk.Scrollbar(log_shell, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_y.set)
        log_y.pack(side="right", fill="y")
        self.log_box.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self.log_box.tag_configure("error", foreground=THEME["danger"])
        self.log_box.tag_configure("success", foreground=THEME["green"])
        self.log_box.tag_configure("command", foreground=THEME["accent"])

        self.preview_label = ttk.Label(self.right_panel, style="Header.TLabel")
        self.preview_label.pack(anchor="w", padx=8, pady=(8, 4))
        video_shell = tk.Frame(self.right_panel, bg=THEME["border"])
        video_shell.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.video_host = tk.Frame(video_shell, bg="#000000", height=360)
        self.video_host.pack(fill="both", expand=True, padx=1, pady=1)
        self.video_host.pack_propagate(False)
        self.video_message = tk.Label(
            self.video_host, bg="#000000", fg="#E6E6E6", justify="center",
            wraplength=500, font=("Segoe UI", 10),
        )
        self.video_message.place(relx=0.5, rely=0.5, anchor="center")
        self.player = EmbeddedVlcPlayer(self.video_host)

        controls = ttk.Frame(self.right_panel, style="Panel.TFrame")
        controls.pack(fill="x", padx=8, pady=(0, 4))
        self.play_button = RoundedButton(controls, command=self.toggle_play,
                                         parent_bg=THEME["panel"], radius=10, padx=11, pady=6)
        self.play_button.pack(side="left", padx=(0, 3))
        self.stop_button = RoundedButton(controls, command=self.stop_playback,
                                         parent_bg=THEME["panel"], radius=10, padx=11, pady=6)
        self.stop_button.pack(side="left", padx=3)
        self.mute_button = RoundedButton(controls, command=self.toggle_mute,
                                         parent_bg=THEME["panel"], radius=10, padx=11, pady=6)
        self.mute_button.pack(side="left", padx=3)
        self.open_video_button = RoundedButton(controls, command=self.open_video_externally,
                                               parent_bg=THEME["panel"], radius=10, padx=11, pady=6)
        self.open_video_button.pack(side="right")
        self.open_video_button.config(state="disabled")

        timeline_row = ttk.Frame(self.right_panel, style="Panel.TFrame")
        timeline_row.pack(fill="x", padx=8, pady=3)
        self.timeline = tk.Scale(
            timeline_row, from_=0, to=1000, orient="horizontal", showvalue=False,
            bg=THEME["panel"], fg=THEME["text"], activebackground=THEME["accent"],
            highlightthickness=0, troughcolor=THEME["line"], sliderrelief="flat",
            command=self._on_timeline_change,
        )
        self.timeline.pack(side="left", fill="x", expand=True)
        self.timeline.bind("<ButtonPress-1>", self._timeline_press)
        self.timeline.bind("<ButtonRelease-1>", self._timeline_release)
        self.time_var = tk.StringVar(value="0:00 / 0:00")
        tk.Label(timeline_row, textvariable=self.time_var, bg=THEME["panel"],
                 fg=THEME["muted"], font=("Segoe UI", 8)).pack(side="right", padx=(6, 0))

        volume_row = ttk.Frame(self.right_panel, style="Panel.TFrame")
        volume_row.pack(fill="x", padx=8, pady=(2, 8))
        self.volume_label = ttk.Label(volume_row, style="Muted.TLabel")
        self.volume_label.pack(side="left")
        self.volume_scale = tk.Scale(
            volume_row, from_=0, to=100, orient="horizontal", showvalue=False,
            length=180, bg=THEME["panel"], fg=THEME["text"],
            activebackground=THEME["accent"], highlightthickness=0,
            troughcolor=THEME["line"], sliderrelief="flat", command=self.set_volume,
        )
        self.volume_scale.set(80)
        self.volume_scale.pack(side="left", padx=(5, 0))
        self.player_help_label = tk.Label(
            self.right_panel, justify="left", anchor="w", wraplength=600,
            bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8),
        )
        self.player_help_label.pack(fill="x", padx=10, pady=(0, 8))

    def refresh_ui(self) -> None:
        """Refresh labels when the host application switches language."""
        quality_index = self.quality_combo.current()
        if quality_index < 0:
            quality_index = QUALITY_KEYS.index("medium")
        self.header_label.config(text=self._t("title"))
        self.code_label.config(text=self._t("code"))
        self.scene_label.config(text=self._t("scene"))
        self.detect_button.config(text=self._t("detect"))
        self.quality_label.config(text=self._t("quality"))
        self.quality_combo.configure(values=[QUALITY_PRESETS[key][self._lang()] for key in QUALITY_KEYS])
        self.quality_combo.current(min(quality_index, len(QUALITY_KEYS) - 1))
        self.confirm_check.config(text=self._t("run_confirm"))
        self.warning_label.config(text=self._t("run_warning"))
        self.render_button.config(text=self._t("render"))
        self.cancel_button.config(text=self._t("cancel"))
        self.output_button.config(text=self._t("output_folder"))
        self.logs_label.config(text=self._t("logs"))
        self.preview_label.config(text=self._t("preview"))
        self.stop_button.config(text=self._t("stop"))
        self.mute_button.config(text=self._t("unmute") if self._muted else self._t("mute"))
        self.open_video_button.config(text=self._t("open_video"))
        self.volume_label.config(text=self._t("volume"))
        self.player_help_label.config(text=self._t("player_help"))
        self.play_button.config(text=self._t("pause") if self.player.is_playing() else self._t("play"))
        if not self.status_var.get():
            self._set_status(self._t("ready"))
        if self.last_video_path is None:
            self._show_video_message(self._t("no_video"))

    def _selected_quality(self) -> str:
        index = self.quality_combo.current()
        if index < 0 or index >= len(QUALITY_KEYS):
            return "medium"
        return QUALITY_KEYS[index]

    def detect_scene(self) -> None:
        name = detect_scene_name(self.code_editor.get("1.0", "end"), DEFAULT_SCENE_NAME)
        self._set_scene_name(name, user_selected=False)
        if name == DEFAULT_SCENE_NAME:
            self._set_status(self._t("scene_default", name=name))
        else:
            self._set_status(self._t("found_scene", name=name))

    def _mark_scene_name_manual(self, _event=None) -> None:
        if not self._setting_scene_name:
            self._scene_name_is_manual = True

    def _set_scene_name(self, name: str, user_selected: bool = False) -> None:
        self._setting_scene_name = True
        try:
            self.scene_name_var.set(name)
        finally:
            self._setting_scene_name = False
        self._scene_name_is_manual = user_selected

    def _set_status(self, text: str, level: str = "normal") -> None:
        """Set status text and make actionable renderer failures unmistakable."""
        self.status_var.set(text)
        colors = {
            "error": THEME["danger"],
            "success": THEME["green"],
            "warning": THEME["accent"],
        }
        try:
            self.status_label.config(fg=colors.get(level, THEME["muted"]))
        except tk.TclError:
            pass

    def _append_log(self, text: str, tag: str | None = None) -> None:
        if not text:
            return
        try:
            # A hostile/buggy child can emit one enormous line.  Keeping that
            # line intact makes Tk's word-wrapping work disproportionately
            # expensive, so retain a clear prefix and an explicit truncation.
            if len(text) > MAX_LOG_EVENT_CHARS:
                text = text[:MAX_LOG_EVENT_CHARS] + "\n… [one oversized log entry was truncated]"
            suffix = "" if text.endswith("\n") else "\n"
            if tag:
                self.log_box.insert("end", text + suffix, tag)
            else:
                self.log_box.insert("end", text + suffix)
            size = int(self.log_box.count("1.0", "end-1c", "chars")[0])
            if size > MAX_LOG_CHARS:
                self.log_box.delete("1.0", "1.0 + %dc" % (size - MAX_LOG_CHARS))
            self.log_box.see("end")
        except tk.TclError:
            pass

    def _reset_log(self) -> None:
        self._render_error_in_log = False
        try:
            self.log_box.delete("1.0", "end")
        except tk.TclError:
            pass

    def _show_video_message(self, text: str) -> None:
        try:
            self.video_message.config(text=text)
            self.video_message.place(relx=0.5, rely=0.5, anchor="center")
        except tk.TclError:
            pass

    def _hide_video_message(self) -> None:
        try:
            self.video_message.place_forget()
        except tk.TclError:
            pass

    def start_render(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return
        code = self.code_editor.get("1.0", "end").strip()
        if not code:
            messagebox.showwarning(self._t("title"), self._t("empty_code"), parent=self.winfo_toplevel())
            return
        if not self.confirm_var.get():
            messagebox.showwarning(self._t("title"), self._t("confirm_needed"), parent=self.winfo_toplevel())
            return
        if not is_manim_available():
            message = self._t("manim_python_missing") if getattr(sys, "frozen", False) else self._t("manim_missing")
            self._append_log(message, "error")
            self._set_status(message, "error")
            return
        scene_name = resolve_scene_name(
            code, self.scene_name_var.get(), self._scene_name_is_manual,
        )
        if scene_name != self.scene_name_var.get().strip():
            self._set_scene_name(scene_name, user_selected=False)
        if not is_valid_scene_name(scene_name):
            messagebox.showwarning(self._t("title"), self._t("invalid_scene"), parent=self.winfo_toplevel())
            return

        self._reset_log()
        self._append_log(self._t("starting"), "command")
        self._set_status(self._t("rendering"))
        self.render_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.stop_playback()
        self.worker = ManimRenderWorker(
            code=code,
            quality=quality_flag(self._selected_quality()),
            scene_name=scene_name,
            events=self.events,
            output_root=self.render_root,
        )
        self.worker.start()

    def cancel_render(self) -> None:
        if self.worker is None or not self.worker.is_alive():
            return
        if self.worker.cancel():
            self.cancel_button.config(state="disabled")
            self._set_status(self._t("cancel_requested"), "warning")

    def _schedule_event_poll(self, delay=70) -> None:
        if self._destroyed:
            return
        try:
            self._event_after_id = self.after(delay, self._poll_events)
        except tk.TclError:
            self._destroyed = True

    def _poll_events(self) -> None:
        if self._destroyed:
            return
        try:
            processed = 0
            while processed < MAX_EVENTS_PER_TICK:
                event = self.events.get_nowait()
                processed += 1
                kind = event[0]
                if kind == "started":
                    _kind, run_dir, command = event
                    self._append_log(run_dir, "command")
                    self._append_log(self._t("command") + " " + command, "command")
                elif kind == "log":
                    _kind, _stream, text = event
                    is_error = is_error_log_line(text)
                    self._render_error_in_log = self._render_error_in_log or is_error
                    self._append_log(text, "error" if self._render_error_in_log else None)
                    if not text.strip() and not is_error:
                        self._render_error_in_log = False
                elif kind == "finished":
                    self._on_render_success(Path(event[1]))
                elif kind == "error":
                    self._on_render_error(event[1])
                elif kind == "cancelled":
                    self._on_render_cancelled(event[1])
        except Empty:
            pass
        finally:
            self._schedule_event_poll(10 if not self.events.empty() else 70)

    def _finish_render_controls(self) -> None:
        self.render_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.worker = None

    def _on_render_success(self, video_path: Path) -> None:
        self._finish_render_controls()
        self.last_video_path = video_path
        self.open_video_button.config(state="normal")
        self._append_log("✓ " + self._t("render_complete"), "success")
        if self.player.load(video_path):
            self.player.set_volume(self.volume_scale.get())
            self.player.set_mute(self._muted)
            if self.player.play():
                self._hide_video_message()
                self._set_status(self._t("render_complete"), "success")
            else:
                detail = self.player.error or self._t("player_playback_failed")
                self._show_video_message(self._t("player_playback_failed"))
                self._append_log(self._t("player_playback_failed") + "\n" + detail, "error")
                self._set_status(self._t("player_playback_failed"), "error")
        else:
            detail = self.player.error or self._t("player_missing")
            self._show_video_message(self._t("player_missing"))
            self._append_log(self._t("player_missing") + "\n" + detail, "error")
            self._set_status(self._t("render_complete_no_player"), "warning")

    def _on_render_error(self, message: str) -> None:
        self._finish_render_controls()
        self._append_log("✗ " + message, "error")
        self._set_status(message, "error")

    def _on_render_cancelled(self, message: str) -> None:
        self._finish_render_controls()
        self._append_log("■ " + message, "error")
        self._set_status(self._t("cancelled"), "warning")

    def _schedule_playback_poll(self) -> None:
        if self._destroyed:
            return
        try:
            self._playback_after_id = self.after(250, self._poll_playback)
        except tk.TclError:
            self._destroyed = True

    def _poll_playback(self) -> None:
        if self._destroyed:
            return
        try:
            duration = self.player.duration_ms()
            position = self.player.position_ms()
            if duration > 0:
                if not self._timeline_dragging:
                    self._updating_timeline = True
                    self.timeline.configure(to=duration)
                    self.timeline.set(min(position, duration))
                    self._updating_timeline = False
                self.time_var.set(self._t("time", current=_format_time(position),
                                          total=_format_time(duration)))
            self.play_button.config(text=self._t("pause") if self.player.is_playing() else self._t("play"))
        finally:
            self._schedule_playback_poll()

    def toggle_play(self) -> None:
        if self.last_video_path is None:
            self._show_video_message(self._t("no_video"))
            return
        if not self.player.available:
            if not self.player.load(self.last_video_path):
                self._show_video_message(self._t("player_missing"))
                self._append_log(self._t("player_missing") + "\n" + self.player.error, "error")
                return
        if self.player.is_playing():
            self.player.pause(True)
        else:
            self._hide_video_message()
            if not self.player.play():
                detail = self.player.error or self._t("player_playback_failed")
                self._show_video_message(self._t("player_playback_failed"))
                self._append_log(self._t("player_playback_failed") + "\n" + detail, "error")
                self._set_status(self._t("player_playback_failed"), "error")

    def stop_playback(self) -> None:
        self.player.stop()
        try:
            self._updating_timeline = True
            self.timeline.set(0)
            self._updating_timeline = False
            self.time_var.set(self._t("time", current="0:00", total="0:00"))
        except tk.TclError:
            pass

    def _timeline_press(self, _event=None) -> None:
        self._timeline_dragging = True

    def _timeline_release(self, _event=None) -> None:
        self._timeline_dragging = False
        self.player.seek(self.timeline.get())

    def _on_timeline_change(self, _value=None) -> None:
        # Seeking on release avoids making a heavy MP4 decoder chase every
        # pixel of a drag, while programmatic updates never seek at all.
        if self._updating_timeline:
            return

    def set_volume(self, value=None) -> None:
        self.player.set_volume(self.volume_scale.get() if value is None else value)

    def toggle_mute(self) -> None:
        self._muted = not self._muted
        self.player.set_mute(self._muted)
        self.mute_button.config(text=self._t("unmute") if self._muted else self._t("mute"))

    def open_output_folder(self) -> None:
        self.render_root.mkdir(parents=True, exist_ok=True)
        self._open_path(self.render_root)

    def open_video_externally(self) -> None:
        if self.last_video_path is None or not self.last_video_path.exists():
            self._set_status(self._t("no_video"))
            return
        self._open_path(self.last_video_path)

    @staticmethod
    def _open_path(path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except (OSError, subprocess.SubprocessError):
            pass

    def _on_destroy(self, event) -> None:
        if event.widget is not self or self._destroyed:
            return
        self._destroyed = True
        if self.worker is not None:
            self.worker.cancel()
        self.player.release()
        for after_id in (self._event_after_id, self._playback_after_id):
            try:
                if after_id is not None:
                    self.after_cancel(after_id)
            except tk.TclError:
                pass

