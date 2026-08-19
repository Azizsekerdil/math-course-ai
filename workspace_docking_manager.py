# -*- coding: utf-8 -*-
"""
Workspace Docking Manager for the Math Course AI program.

A Blender / Visual-Studio-style panel system: panels are registered once with a
factory, then can be docked into named regions, opened as notebook tabs, popped
out into floating Toplevel windows, hidden, moved, and persisted to JSON.

Because Tkinter cannot truly re-parent an existing widget, panels are moved by
DESTROYING the current view and REBUILDING it via its factory in the new
container. Factories therefore must build a fresh view bound to the app's data
model (the data is the source of truth, the view is disposable).

Pure logic (registry, state, layout store, presets, dedup) works head-less;
only the actual dock/tab/float operations need a live Tk root.
"""

import json
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - tkinter always present on the targets
    tk = None
    ttk = None

from app_paths import settings_dir as _settings_dir

SETTINGS_DIR = _settings_dir()
LAYOUT_PATH = SETTINGS_DIR / "workspace_layout.json"

# Panel states
DOCKED = "docked"
FLOATING = "floating"
TABBED = "tabbed"
HIDDEN = "hidden"

REGIONS = ("left", "right", "top", "bottom", "center")


# ---------------------------------------------------------------------------
# DockablePanel
# ---------------------------------------------------------------------------
class DockablePanel:
    """Metadata + lifecycle for a single dockable panel."""

    def __init__(self, panel_id, title, factory, *, default_region="center",
                 supports_popout=True, supports_tab=True, supports_close=True,
                 supports_move=True):
        self.panel_id = panel_id
        self.title = title
        self.factory = factory                # callable(parent) -> tk widget
        self.default_region = default_region
        self.supports_popout = supports_popout
        self.supports_tab = supports_tab
        self.supports_close = supports_close
        self.supports_move = supports_move
        # live state
        self.state = HIDDEN
        self.region = default_region
        self.widget = None
        self.container = None
        self.floating_window = None

    @property
    def visible(self):
        return self.state != HIDDEN

    def to_dict(self):
        d = {"panel_id": self.panel_id, "state": self.state, "region": self.region}
        win = self.floating_window
        if self.state == FLOATING and win is not None:
            try:
                if win.winfo_exists():
                    d["geometry"] = win.winfo_geometry()
            except Exception:
                pass
        return d

    def __repr__(self):
        return f"<DockablePanel {self.panel_id!r} state={self.state} region={self.region}>"


# ---------------------------------------------------------------------------
# WorkspaceLayoutStore
# ---------------------------------------------------------------------------
class WorkspaceLayoutStore:
    """Reads/writes the workspace layout JSON. Never raises on missing or
    corrupted files (returns {} instead)."""

    def __init__(self, path=None):
        self.path = Path(path) if path else LAYOUT_PATH

    def exists(self):
        try:
            return self.path.exists()
        except Exception:
            return False

    def save(self, data):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def load(self):
        try:
            if not self.path.exists():
                return {}
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except Exception:
            # Missing / corrupted / unreadable -> empty, no crash.
            return {}


# ---------------------------------------------------------------------------
# Layout presets (GÖREV 10)
# ---------------------------------------------------------------------------
LAYOUT_PRESETS = {
    "default_study": {
        "label": "Default Study Layout",
        "panels": {
            "resources_panel": DOCKED, "pdf_reader_panel": "center",
            "visual_math_lab_panel": "center", "graph_panel": "right",
            "step_solution_panel": "bottom", "real_life_panel": "bottom",
        },
    },
    "visual_math_focus": {
        "label": "Visual Math Focus Layout",
        "panels": {
            "visual_math_lab_panel": "center", "graph_panel": "center",
            "step_solution_panel": "bottom", "resources_panel": HIDDEN,
        },
    },
    "simulation_studio": {
        "label": "Simulation Studio Layout",
        "panels": {
            "simulation_studio_panel": FLOATING, "graph_panel": "right",
            "course_simulation_panel": "center", "resources_panel": HIDDEN,
        },
    },
    "wacom_teaching": {
        "label": "Tablet Çizim Ders Düzeni",
        "panels": {
            "pdf_reader_panel": "left", "wacom_board_panel": "right",
            "ai_tutor_panel": "bottom", "graph_panel": HIDDEN,
        },
    },
    "presentation": {
        "label": "Presentation Layout",
        "panels": {
            "graph_panel": "center", "step_solution_panel": HIDDEN,
            "resources_panel": HIDDEN, "real_life_panel": HIDDEN,
        },
    },
    "compact": {
        "label": "Compact Mode",
        "panels": {"graph_panel": "center", "step_solution_panel": "bottom"},
    },
}


# ---------------------------------------------------------------------------
# WorkspaceDockingManager
# ---------------------------------------------------------------------------
class WorkspaceDockingManager:
    """Registers panels and moves them between docked regions, notebook tabs
    and floating windows, with duplicate prevention and JSON persistence."""

    def __init__(self, *, app=None, notebook=None, regions=None,
                 layout_store=None, commands=None):
        self.app = app                       # toplevel parent for floating windows
        self.notebook = notebook             # ttk.Notebook used for tabs
        self.regions = dict(regions or {})   # region name -> container frame
        self.store = layout_store or WorkspaceLayoutStore()
        self.commands = commands             # optional CommandRegistry
        self.panels = {}                     # panel_id -> DockablePanel
        self._tab_frames = {}                # panel_id -> tab frame

    # -- registration --------------------------------------------------- #
    def register(self, panel):
        self.panels[panel.panel_id] = panel
        return panel

    def register_panel(self, panel_id, title, factory, **kw):
        return self.register(DockablePanel(panel_id, title, factory, **kw))

    def get(self, panel_id):
        return self.panels.get(panel_id)

    def list_panels(self):
        return list(self.panels.values())

    def panel_states(self):
        return {pid: p.state for pid, p in self.panels.items()}

    def set_region(self, region, container):
        self.regions[region] = container

    def set_notebook(self, notebook):
        self.notebook = notebook

    # -- internal widget helpers --------------------------------------- #
    def _build_widget(self, panel, parent):
        try:
            panel.widget = panel.factory(parent)
            panel.container = parent
        except Exception:
            panel.widget = None
        return panel.widget

    def _destroy_widget(self, panel):
        if panel.widget is not None:
            try:
                panel.widget.destroy()
            except Exception:
                pass
        panel.widget = None

    def _teardown(self, panel):
        """Remove a panel's current view (tab/float/dock) without changing
        its logical target state."""
        if panel.state == TABBED:
            frame = self._tab_frames.pop(panel.panel_id, None)
            self._destroy_widget(panel)
            if frame is not None and self.notebook is not None:
                try:
                    self.notebook.forget(frame)
                except Exception:
                    pass
                try:
                    frame.destroy()
                except Exception:
                    pass
        elif panel.state == FLOATING:
            self._destroy_widget(panel)
            if panel.floating_window is not None:
                try:
                    panel.floating_window.destroy()
                except Exception:
                    pass
            panel.floating_window = None
        elif panel.state == DOCKED:
            self._destroy_widget(panel)
        panel.container = None

    # -- operations ----------------------------------------------------- #
    def show(self, panel_id):
        panel = self.get(panel_id)
        if panel is None:
            return None
        if panel.state == HIDDEN:
            return self.dock_back(panel_id)
        return panel

    def hide(self, panel_id):
        panel = self.get(panel_id)
        if panel is None:
            return None
        self._teardown(panel)
        panel.state = HIDDEN
        return panel

    def open_as_tab(self, panel_id):
        panel = self.get(panel_id)
        if panel is None or self.notebook is None or not panel.supports_tab:
            return None
        # Duplicate prevention: if already a tab, just focus it.
        if panel.state == TABBED and panel.panel_id in self._tab_frames:
            try:
                self.notebook.select(self._tab_frames[panel.panel_id])
            except Exception:
                pass
            return panel
        self._teardown(panel)
        frame = ttk.Frame(self.notebook)
        try:
            self.notebook.add(frame, text=panel.title)
        except Exception:
            return None
        self._build_widget(panel, frame)
        if panel.widget is not None:
            try:
                panel.widget.pack(fill="both", expand=True)
            except Exception:
                pass
        self._tab_frames[panel.panel_id] = frame
        panel.state = TABBED
        panel.region = "tab"
        try:
            self.notebook.select(frame)
        except Exception:
            pass
        return panel

    def pop_out(self, panel_id):
        panel = self.get(panel_id)
        if panel is None or not panel.supports_popout or tk is None:
            return None
        # Duplicate prevention: if already floating, focus the existing window.
        if panel.state == FLOATING and panel.floating_window is not None:
            try:
                if panel.floating_window.winfo_exists():
                    panel.floating_window.deiconify()
                    panel.floating_window.lift()
                    panel.floating_window.focus_force()
                    return panel
            except Exception:
                pass
        self._teardown(panel)
        top = tk.Toplevel(self.app)
        top.title(panel.title)
        try:
            top.minsize(360, 280)
            top.resizable(True, True)
        except Exception:
            pass
        top.protocol("WM_DELETE_WINDOW", lambda pid=panel_id: self.dock_back(pid))
        bar = ttk.Frame(top)
        bar.pack(fill="x")
        ttk.Label(bar, text=panel.title).pack(side="left", padx=6, pady=3)
        ttk.Button(bar, text="Dock Back",
                   command=lambda pid=panel_id: self.dock_back(pid)).pack(side="right", padx=4, pady=2)
        body = ttk.Frame(top)
        body.pack(fill="both", expand=True)
        self._build_widget(panel, body)
        if panel.widget is not None:
            try:
                panel.widget.pack(fill="both", expand=True)
            except Exception:
                pass
        panel.state = FLOATING
        panel.region = "floating"
        panel.floating_window = top
        return panel

    def dock_back(self, panel_id, region=None):
        panel = self.get(panel_id)
        if panel is None:
            return None
        self._teardown(panel)
        region = region or panel.default_region
        container = self.regions.get(region) or self.regions.get("center")
        if container is None:
            panel.state = HIDDEN
            return panel
        self._build_widget(panel, container)
        if panel.widget is not None:
            try:
                panel.widget.pack(fill="both", expand=True)
            except Exception:
                pass
        panel.state = DOCKED
        panel.region = region
        return panel

    def move_to(self, panel_id, target):
        """Move a panel to: left/right/top/bottom/center (dock), tab, floating,
        or hidden. The user-facing 'Move' menu calls this."""
        target = (target or "").lower()
        if target in ("tab", "new_tab", "newtab"):
            return self.open_as_tab(panel_id)
        if target in ("floating", "float", "window", "popout", "pop_out"):
            return self.pop_out(panel_id)
        if target in ("hidden", "hide"):
            return self.hide(panel_id)
        return self.dock_back(panel_id, target if target in REGIONS else None)

    # -- layout persistence -------------------------------------------- #
    def capture_layout(self, extra=None):
        data = {"panels": {pid: p.to_dict() for pid, p in self.panels.items()}}
        if self.app is not None:
            try:
                data["window_geometry"] = self.app.winfo_geometry()
            except Exception:
                pass
        if extra:
            data.update(extra)
        return data

    def apply_layout(self, data):
        if not isinstance(data, dict):
            return
        for pid, pdata in (data.get("panels") or {}).items():
            panel = self.get(pid)
            if panel is None:
                continue
            st = pdata.get("state", HIDDEN)
            region = pdata.get("region")
            if st == TABBED:
                self.open_as_tab(pid)
            elif st == FLOATING:
                self.pop_out(pid)
                geo = pdata.get("geometry")
                if geo and panel.floating_window is not None:
                    try:
                        panel.floating_window.geometry(geo)
                    except Exception:
                        pass
            elif st == DOCKED:
                self.dock_back(pid, region)
            else:
                self.hide(pid)

    def save_layout(self, extra=None):
        return self.store.save(self.capture_layout(extra))

    def load_layout(self):
        data = self.store.load()
        if data:
            self.apply_layout(data)
        return data

    def reset_layout(self):
        for panel in self.panels.values():
            if panel.default_region == HIDDEN:
                self.hide(panel.panel_id)
            else:
                self.dock_back(panel.panel_id, panel.default_region)

    def apply_preset(self, preset_name):
        preset = LAYOUT_PRESETS.get(preset_name)
        if not preset:
            return False
        for pid, target in preset.get("panels", {}).items():
            if self.get(pid) is None:
                continue
            self.move_to(pid, target)
        # Any panel not named in the preset is hidden for a clean workspace.
        named = set(preset.get("panels", {}).keys())
        for pid, panel in self.panels.items():
            if pid not in named and panel.state != HIDDEN:
                self.hide(pid)
        return True


# ---------------------------------------------------------------------------
# WorkspaceManagerWindow
# ---------------------------------------------------------------------------
class WorkspaceManagerWindow(tk.Toplevel if tk is not None else object):
    """Lists every registered panel with its state/region and offers Show /
    Hide / Open as Tab / Pop Out / Dock / Reset plus layout save/load/presets."""

    def __init__(self, manager, app=None, theme_bg="#0f1b28"):
        super().__init__(app)
        self.manager = manager
        self.bg = theme_bg
        self.title("Workspace Manager / Çalışma Alanı Yöneticisi")
        try:
            self.configure(bg=self.bg)
        except Exception:
            pass
        self.geometry("760x520")
        self.minsize(620, 420)
        self.resizable(True, True)
        self._build()
        self.refresh()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(top, text="Workspace", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Save Layout", command=self._save).pack(side="right", padx=2)
        ttk.Button(top, text="Load Layout", command=self._load).pack(side="right", padx=2)
        ttk.Button(top, text="Reset Layout", command=self._reset).pack(side="right", padx=2)
        ttk.Button(top, text="Restore Default", command=lambda: self._preset("default_study")).pack(side="right", padx=2)

        split = ttk.PanedWindow(self, orient="horizontal")
        split.pack(fill="both", expand=True, padx=8, pady=4)

        # --- left: panel list + actions + presets ---
        left = ttk.Frame(split)
        split.add(left, weight=2)
        cols = ("panel", "state", "region", "visible")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=10, selectmode="browse")
        for c, txt, w in (("panel", "Panel", 170), ("state", "State", 80),
                          ("region", "Region", 80), ("visible", "Visible", 60)):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor="w" if c == "panel" else "center")
        self.tree.pack(fill="both", expand=True, pady=(0, 4))
        actions = ttk.Frame(left)
        actions.pack(fill="x")
        for text, fn in (("Show", self._show), ("Hide", self._hide),
                         ("Open as Tab", lambda: self._move("tab")),
                         ("Pop Out", lambda: self._move("floating")),
                         ("Dock", lambda: self._move("center")),
                         ("Reset", self._reset_one)):
            ttk.Button(actions, text=text, command=fn).pack(side="left", padx=1)
        presets = ttk.Frame(left)
        presets.pack(fill="x", pady=(4, 0))
        ttk.Label(presets, text="Presets:").pack(side="left", padx=(0, 4))
        for name, preset in LAYOUT_PRESETS.items():
            ttk.Button(presets, text=preset["label"].replace(" Layout", "").replace(" Mode", ""),
                       command=lambda n=name: self._preset(n)).pack(side="left", padx=1)

        # --- right: live docking area (notebook for tabs + a center dock) ---
        right = ttk.PanedWindow(split, orient="vertical")
        split.add(right, weight=4)
        self._dock_notebook = ttk.Notebook(right)
        right.add(self._dock_notebook, weight=2)
        self._dock_center = ttk.Frame(right)
        right.add(self._dock_center, weight=3)
        # Wire the manager to dock/tab INTO this window unless it already has
        # its own host (e.g. in head-less tests).
        if self.manager.notebook is None:
            self.manager.set_notebook(self._dock_notebook)
        if "center" not in self.manager.regions:
            for r in ("center", "left", "right", "top", "bottom"):
                self.manager.set_region(r, self._dock_center)

    # -- helpers -- #
    def _selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def refresh(self):
        try:
            self.tree.delete(*self.tree.get_children())
        except Exception:
            return
        for panel in self.manager.list_panels():
            self.tree.insert("", "end", iid=panel.panel_id,
                             values=(panel.title, panel.state, panel.region,
                                     "yes" if panel.visible else "no"))

    def _show(self):
        pid = self._selected()
        if pid:
            self.manager.show(pid)
            self.refresh()

    def _hide(self):
        pid = self._selected()
        if pid:
            self.manager.hide(pid)
            self.refresh()

    def _move(self, target):
        pid = self._selected()
        if pid:
            self.manager.move_to(pid, target)
            self.refresh()

    def _reset_one(self):
        pid = self._selected()
        if pid:
            panel = self.manager.get(pid)
            self.manager.move_to(pid, panel.default_region)
            self.refresh()

    def _reset(self):
        self.manager.reset_layout()
        self.refresh()

    def _save(self):
        self.manager.save_layout()

    def _load(self):
        self.manager.load_layout()
        self.refresh()

    def _preset(self, name):
        self.manager.apply_preset(name)
        self.refresh()
