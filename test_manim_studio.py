# -*- coding: utf-8 -*-
"""Headless checks for the optional Manim Animation Studio.

No real Manim/VLC installation is required: this suite exercises the command,
scene discovery, isolated output lookup, and worker-to-queue boundary with a
small ``Popen`` fake.  Run with ``python test_manim_studio.py``.
"""

import io
import os
import sys
import tempfile
import threading
from pathlib import Path
from queue import Queue
from types import SimpleNamespace

import tkinter as tk

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
_TMP = Path(tempfile.mkdtemp(prefix="mcai-manim-test-"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", str(_TMP / "exports"))
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", str(_TMP / "settings"))

import manim_studio as manim_studio_module  # noqa: E402

from manim_studio import (  # noqa: E402
    DEFAULT_SCENE_CODE,
    DEFAULT_SCENE_NAME,
    EmbeddedVlcPlayer,
    MANIM_PYTHON_ENV,
    MAX_LOG_CHARS,
    ManimRenderWorker,
    ManimStudio,
    QUALITY_PRESETS,
    build_manim_command,
    command_for_log,
    detect_scene_name,
    find_rendered_video,
    is_manim_available,
    is_error_log_line,
    is_valid_scene_name,
    manim_python_command,
    quality_flag,
    resolve_scene_name,
)


PASSED = 0
FAILED = 0


def check(condition, label):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


class FakeProcess:
    def __init__(self, lines=(), return_code=0):
        self.stdout = io.StringIO("".join(lines))
        self.return_code = return_code
        self.terminated = False

    def poll(self):
        return self.return_code

    def wait(self):
        return self.return_code

    def terminate(self):
        self.terminated = True
        self.return_code = -15


class SuccessfulPopen:
    def __init__(self):
        self.command = None
        self.kwargs = None

    def __call__(self, command, **kwargs):
        self.command = list(command)
        self.kwargs = kwargs
        media_dir = Path(command[command.index("--media_dir") + 1])
        scene = command[-1]
        video = media_dir / "videos" / "temp_scene" / "480p15" / (scene + ".mp4")
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"not a real movie, only worker-path coverage")
        return FakeProcess(["Manim Community v0.x\n", "Writing movie file\n"], 0)


class FailedPopen:
    def __call__(self, _command, **_kwargs):
        return FakeProcess(["SyntaxError: invalid syntax\n"], 2)


class CancelDuringLaunchProcess:
    """A child created only after its factory has been deliberately paused."""

    def __init__(self):
        self.stdout = io.StringIO("")
        self.return_code = None
        self.terminated = False

    def poll(self):
        return self.return_code

    def wait(self):
        return self.return_code if self.return_code is not None else 0

    def terminate(self):
        self.terminated = True
        self.return_code = -15


class GatePopen:
    """Hold Popen's return so cancellation lands in the launch race window."""

    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()
        self.process = CancelDuringLaunchProcess()

    def __call__(self, _command, **_kwargs):
        self.entered.set()
        self.release.wait(2)
        return self.process


class SpamPopen(SuccessfulPopen):
    def __call__(self, command, **kwargs):
        self.command = list(command)
        self.kwargs = kwargs
        media_dir = Path(command[command.index("--media_dir") + 1])
        scene = command[-1]
        video = media_dir / "videos" / "temp_scene" / "480p15" / (scene + ".mp4")
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"small test movie")
        return FakeProcess(["very noisy line\n"] * 100, 0)


class CancellingNoisyPopen:
    """Cancel during launch, then expose a long buffered stdout stream."""

    def __init__(self):
        self.worker = None
        self.process = FakeProcess(["buffered output\n"] * 50, 0)

    def __call__(self, _command, **_kwargs):
        self.worker.cancel()
        return self.process


def drain(events):
    out = []
    while not events.empty():
        out.append(events.get_nowait())
    return out


def test_scene_detection_and_quality():
    print("\n== Scene discovery and quality mapping ==")
    check(detect_scene_name(DEFAULT_SCENE_CODE) == DEFAULT_SCENE_NAME,
          "default template exposes SoruCozumu")
    check(detect_scene_name("from manim import Scene\nclass Orbit(ThreeDScene):\n    pass\n") == "Orbit",
          "3D Scene subclass is detected")
    check(detect_scene_name("class Broken(Scene):\n") == DEFAULT_SCENE_NAME,
          "syntax still editing falls back safely")
    pasted_scene = "from manim import Scene\nclass PastedExample(Scene):\n    pass\n"
    check(resolve_scene_name(pasted_scene, DEFAULT_SCENE_NAME) == "PastedExample",
          "an untouched template scene name follows pasted Manim code")
    check(resolve_scene_name(pasted_scene, "ChosenScene", user_selected=True) == "ChosenScene",
          "an explicitly entered scene name is preserved for multi-scene scripts")
    check(is_valid_scene_name("SoruCozumu") and not is_valid_scene_name("class"),
          "scene names reject Python keywords as well as invalid identifiers")
    check(is_error_log_line("SyntaxError: invalid syntax") and
          not is_error_log_line("Writing movie file"),
          "live-log error detection reserves red text for renderer failures")
    check([quality_flag(key) for key in ("low", "medium", "high")] == ["-ql", "-qm", "-qh"],
          "low/medium/high map to Manim quality flags")
    check(QUALITY_PRESETS["medium"]["folder"] == "720p30",
          "medium preset carries expected Manim folder")
    check(isinstance(is_manim_available(), bool),
          "Manim availability probe is safe when dependency is absent")


def test_command_and_output_lookup():
    print("\n== Shell-free command and isolated output lookup ==")
    command = build_manim_command("script with spaces.py", "media out", "-qm", "DemoScene")
    check(command[:6] == [sys.executable, "-m", "manim", "-v", "WARNING", "-qm"],
          "command preserves requested python -m manim -v WARNING quality sequence")
    check(command[6:9] == ["--media_dir", "media out", "script with spaces.py"] and command[-1] == "DemoScene",
          "media directory, script and scene remain separate process arguments")
    check("script with spaces.py" in command_for_log(command),
          "command can be rendered for the live log")

    old_env = os.environ.get(MANIM_PYTHON_ENV)
    had_frozen = hasattr(sys, "frozen")
    old_frozen = getattr(sys, "frozen", None)
    try:
        sys.frozen = True
        os.environ[MANIM_PYTHON_ENV] = sys.executable
        check(manim_python_command() == [sys.executable],
              "packaged app uses the explicitly configured external Manim interpreter")
    finally:
        if old_env is None:
            os.environ.pop(MANIM_PYTHON_ENV, None)
        else:
            os.environ[MANIM_PYTHON_ENV] = old_env
        if had_frozen:
            sys.frozen = old_frozen
        else:
            delattr(sys, "frozen")

    try:
        build_manim_command("a.py", "media", "-qunsafe", "Scene")
    except ValueError:
        invalid_quality_rejected = True
    else:
        invalid_quality_rejected = False
    check(invalid_quality_rejected, "unknown quality flag is refused before subprocess launch")

    media = _TMP / "lookup_media"
    named = media / "videos" / "temp_scene" / "720p30" / "Wanted.mp4"
    other = media / "videos" / "temp_scene" / "720p30" / "Other.mp4"
    named.parent.mkdir(parents=True, exist_ok=True)
    named.write_bytes(b"wanted")
    other.write_bytes(b"other")
    os.utime(named, (1, 1))
    os.utime(other, None)
    check(find_rendered_video(media, "Wanted") == named,
          "named scene is preferred over a newer unrelated MP4")
    check(find_rendered_video(media / "missing", "Wanted") is None,
          "missing media directory reports no video instead of crashing")


def test_worker_events():
    print("\n== Non-blocking worker event contract ==")
    events = Queue()
    fake = SuccessfulPopen()
    worker = ManimRenderWorker(
        "from manim import *\nclass DemoScene(Scene):\n    pass\n",
        "-ql", "DemoScene", events, output_root=_TMP / "worker_success", popen_factory=fake,
    )
    worker.run()  # Deliberately direct: event handling is independent from Tk/thread scheduling.
    received = drain(events)
    finished = [event for event in received if event[0] == "finished"]
    check(bool(finished) and Path(finished[0][1]).is_file(),
          "successful worker emits an existing MP4 path")
    check(any(event[0] == "started" for event in received) and
          any(event[0] == "log" and "Writing movie" in event[2] for event in received),
          "worker emits start and streaming log events")
    check(fake.command is not None and fake.command[5] == "-ql" and
          fake.kwargs.get("shell") is None and worker.script_path.read_text(encoding="utf-8").startswith("from manim"),
          "worker writes source and launches an argument-vector command without shell=True")

    events = Queue()
    failed = ManimRenderWorker("bad", "-qm", "SoruCozumu", events,
                               output_root=_TMP / "worker_failed", popen_factory=FailedPopen())
    failed.run()
    received = drain(events)
    check(any(event[0] == "error" and "code 2" in event[1] for event in received),
          "failed render reports an actionable final error after its log")

    events = Queue()
    cancelled = ManimRenderWorker("pass", "-qm", "SoruCozumu", events,
                                  output_root=_TMP / "worker_cancelled", popen_factory=FailedPopen())
    cancelled.cancel()
    cancelled.run()
    received = drain(events)
    check(any(event[0] == "cancelled" for event in received),
          "pre-start cancellation never launches a renderer")

    events = Queue()
    gated = GatePopen()
    race = ManimRenderWorker("pass", "-qm", "SoruCozumu", events,
                             output_root=_TMP / "worker_launch_race", popen_factory=gated)
    race.start()
    launch_started = gated.entered.wait(1)
    race.cancel()
    gated.release.set()
    race.join(2)
    received = drain(events)
    check(launch_started and not race.is_alive() and gated.process.terminated and
          any(event[0] == "cancelled" for event in received),
          "cancellation during Popen creation terminates the just-created child")

    events = Queue(maxsize=2)
    spam = ManimRenderWorker("pass", "-ql", "SoruCozumu", events,
                             output_root=_TMP / "worker_spam", popen_factory=SpamPopen())
    spam.run()
    received = drain(events)
    check(len(received) <= 2 and any(event[0] == "finished" for event in received),
          "bounded event queue drops excess logs but preserves final completion")

    events = Queue()
    terminal = ManimRenderWorker("pass", "-qm", "SoruCozumu", events,
                                 output_root=_TMP / "worker_terminal")
    terminal.cancel()
    terminal._emit_terminal("finished", "would-have-finished.mp4")
    received = drain(events)
    check(any(event[0] == "cancelled" for event in received) and
          not any(event[0] == "finished" for event in received),
          "an accepted cancel wins over a late terminal completion")

    events = Queue()
    noisy_popen = CancellingNoisyPopen()
    one_shot = ManimRenderWorker("pass", "-qm", "SoruCozumu", events,
                                 output_root=_TMP / "worker_one_shot_cancel",
                                 popen_factory=noisy_popen)
    noisy_popen.worker = one_shot
    termination_calls = []
    termination_done = threading.Event()

    def record_termination(process=None, _process_group_id=None):
        termination_calls.append(process)
        if process is not None:
            process.terminate()
        termination_done.set()

    one_shot._terminate_process = record_termination
    one_shot.run()
    termination_done.wait(1)
    received = drain(events)
    check(len(termination_calls) == 1 and
          any(event[0] == "cancelled" for event in received),
          "cancelling a buffered log stream sends one non-blocking teardown request")

    posix_worker = ManimRenderWorker("pass", "-qm", "SoruCozumu", Queue())
    orphaned_parent = FakeProcess()
    orphaned_parent.pid = 731
    killed_groups = []
    original_os_name = manim_studio_module.os.name
    had_killpg = hasattr(manim_studio_module.os, "killpg")
    original_killpg = getattr(manim_studio_module.os, "killpg", None)
    try:
        manim_studio_module.os.name = "posix"
        manim_studio_module.os.killpg = lambda group_id, sig: killed_groups.append((group_id, sig))
        posix_worker._terminate_process(orphaned_parent, 2468)
    finally:
        manim_studio_module.os.name = original_os_name
        if had_killpg:
            manim_studio_module.os.killpg = original_killpg
        else:
            delattr(manim_studio_module.os, "killpg")
    check(killed_groups and killed_groups[0][0] == 2468,
          "POSIX cancellation uses the saved process group after a parent exits")

    windows_worker = ManimRenderWorker("pass", "-qm", "SoruCozumu", Queue())
    windows_process = FakeProcess()
    windows_process.pid = 9123
    taskkill_calls = []
    original_os_name = manim_studio_module.os.name
    original_run = manim_studio_module.subprocess.run
    try:
        manim_studio_module.os.name = "nt"

        def fake_taskkill(command, **kwargs):
            taskkill_calls.append((command, kwargs))
            return SimpleNamespace(returncode=0)

        manim_studio_module.subprocess.run = fake_taskkill
        windows_worker._terminate_process(windows_process)
    finally:
        manim_studio_module.os.name = original_os_name
        manim_studio_module.subprocess.run = original_run
    check(taskkill_calls and taskkill_calls[0][0][:3] == ["taskkill", "/PID", "9123"] and
          taskkill_calls[0][1].get("timeout") == 5,
          "Windows cancellation requests a bounded process-tree teardown")


def test_player_failure_signal():
    print("\n== Optional player failure handling ==")

    class FailedPlayer:
        def play(self):
            return -1

    player = EmbeddedVlcPlayer(SimpleNamespace())
    player._player = FailedPlayer()
    player._attach_host = lambda: None
    check(not player.play() and "could not start playback" in player.error,
          "libVLC playback failure is exposed instead of reported as success")
    player.release()


def test_widget_construction():
    print("\n== Tk widget construction without optional dependencies ==")
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError as exc:
        print(f"   [SKIP] Tk display unavailable: {exc}")
        return
    try:
        studio = ManimStudio(root, SimpleNamespace(language="en"))
        studio.pack(fill="both", expand=True)
        root.update_idletasks()
        check(studio.scene_name_var.get() == DEFAULT_SCENE_NAME and
              studio._selected_quality() == "medium",
              "widget starts with the requested scene and 720p30 default")
        check("Manim Animation Studio" in studio.header_label.cget("text") and
              studio.render_button.cget("state") == "normal",
              "lazy studio panel builds without Manim or VLC installed")
        studio._on_render_error("synthetic renderer failure")
        check(studio.status_label.cget("fg") == manim_studio_module.THEME["danger"],
              "renderer failures are red in the visible status panel")
        original_log_limit = manim_studio_module.MAX_LOG_CHARS
        try:
            manim_studio_module.MAX_LOG_CHARS = 128
            for _ in range(4):
                studio._append_log("short log entry " * 4)
            log_size = int(studio.log_box.count("1.0", "end-1c", "chars")[0])
        finally:
            manim_studio_module.MAX_LOG_CHARS = original_log_limit
        check(log_size <= 128,
              "live log keeps a bounded amount of text during noisy renders")
    finally:
        try:
            studio.destroy()
            root.update_idletasks()
        except (UnboundLocalError, tk.TclError):
            pass
        root.destroy()


def main():
    test_scene_detection_and_quality()
    test_command_and_output_lookup()
    test_worker_events()
    test_player_failure_signal()
    test_widget_construction()
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())

