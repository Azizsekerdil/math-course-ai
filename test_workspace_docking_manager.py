# -*- coding: utf-8 -*-
"""
Tests for the Workspace Docking Manager and Command Registry.

Head-less where possible; the dock/tab/float operations use a withdrawn Tk root.

Run with:
    python test_workspace_docking_manager.py
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PASSED = 0
FAILED = 0


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


def test_imports():
    print("\nIMPORTS")
    import workspace_docking_manager as wdm                      # item 1
    import command_registry as cr
    check(hasattr(wdm, "WorkspaceDockingManager"), "WorkspaceDockingManager import")
    check(hasattr(wdm, "DockablePanel"), "DockablePanel import")
    check(hasattr(wdm, "WorkspaceLayoutStore"), "WorkspaceLayoutStore import")
    check(hasattr(wdm, "WorkspaceManagerWindow"), "WorkspaceManagerWindow import")
    check(hasattr(cr, "CommandRegistry"), "CommandRegistry import")


def test_dockable_panel():
    print("\nDOCKABLE PANEL")
    from workspace_docking_manager import DockablePanel, HIDDEN
    p = DockablePanel("graph_panel", "Graph", lambda parent: None,
                      default_region="right")                    # item 2
    check(p.panel_id == "graph_panel", "panel_id set")
    check(p.title == "Graph", "title set")
    check(p.state == HIDDEN, "panel starts hidden")
    check(p.default_region == "right", "default_region set")
    d = p.to_dict()
    check(d["panel_id"] == "graph_panel" and "state" in d, "to_dict serializes")


def test_register():
    print("\nREGISTER PANEL")
    from workspace_docking_manager import WorkspaceDockingManager
    m = WorkspaceDockingManager()
    m.register_panel("a", "Alpha", lambda parent: None)          # item 3
    m.register_panel("b", "Beta", lambda parent: None)
    check(len(m.list_panels()) == 2, "two panels registered")
    check(m.get("a") is not None and m.get("missing") is None, "get by id")
    check("a" in m.panel_states(), "panel_states includes ids")


def test_command_registry_duplicate():
    print("\nCOMMAND REGISTRY")
    from command_registry import CommandRegistry
    reg = CommandRegistry()
    calls = []
    new1 = reg.register("cmd.solve", "Solve", lambda: calls.append("solve"))   # item 8
    new2 = reg.register("cmd.solve", "Solve Again", lambda: calls.append("again"))
    check(new1 is True, "first register returns True (new)")
    check(new2 is False, "duplicate register returns False")
    check(reg.duplicate_count == 1, "duplicate counted")
    check(len(reg.list_commands()) == 1, "only one command kept (dedup)")
    reg.invoke("cmd.solve")
    check(calls == ["again"], "latest callback wins after replace")
    check(reg.invoke("cmd.missing") is None, "invoking unknown command is safe")


def test_layout_store_missing_and_corrupt():
    print("\nLAYOUT STORE (missing / corrupted)")
    from workspace_docking_manager import WorkspaceLayoutStore
    tmp = Path(tempfile.gettempdir())
    missing = WorkspaceLayoutStore(tmp / "wdm_does_not_exist_123.json")
    check(missing.load() == {}, "missing layout file -> {} (no crash)")   # item 13
    corrupt = tmp / "wdm_corrupt.json"
    corrupt.write_text("{ this is not valid json :::", encoding="utf-8")
    store = WorkspaceLayoutStore(corrupt)
    check(store.load() == {}, "corrupted layout file -> {} (no crash)")   # item 14
    save_path = tmp / "wdm_roundtrip.json"
    s2 = WorkspaceLayoutStore(save_path)
    ok = s2.save({"panels": {"a": {"state": "tabbed"}}})                  # item 6
    check(ok and s2.exists(), "save layout writes file")
    loaded = s2.load()
    check(loaded.get("panels", {}).get("a", {}).get("state") == "tabbed", "load round-trips data")


def test_headless_docking():
    print("\nHEADLESS DOCKING (tabs / floating / hide / layout)")
    try:
        import tkinter as tk
        from tkinter import ttk
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] Tk unavailable: {exc}")
        return
    try:
        from workspace_docking_manager import (
            WorkspaceDockingManager, WorkspaceLayoutStore, TABBED, FLOATING, HIDDEN)
        notebook = ttk.Notebook(root)
        center = ttk.Frame(root)
        store = WorkspaceLayoutStore(Path(tempfile.gettempdir()) / "wdm_headless.json")
        m = WorkspaceDockingManager(app=root, notebook=notebook,
                                    regions={"center": center}, layout_store=store)
        m.register_panel("graph", "Graph", lambda parent: ttk.Label(parent, text="G"),
                         default_region="center")
        m.register_panel("step", "Step", lambda parent: ttk.Label(parent, text="S"),
                         default_region="center")

        # open as tab + duplicate prevention (item 4)
        m.open_as_tab("graph")
        m.open_as_tab("graph")
        root.update_idletasks()
        check(m.get("graph").state == TABBED, "graph is tabbed")
        check(len(notebook.tabs()) == 1, "open_as_tab twice -> ONE tab (dedup)")

        # floating + duplicate prevention (item 5)
        m.pop_out("step")
        win1 = m.get("step").floating_window
        m.pop_out("step")
        win2 = m.get("step").floating_window
        check(m.get("step").state == FLOATING, "step is floating")
        check(win1 is win2 and win1 is not None, "pop_out twice -> SAME window (dedup)")

        # hide + restore (item 7)
        m.hide("graph")
        check(m.get("graph").state == HIDDEN, "graph hidden")
        m.show("graph")
        check(m.get("graph").state != HIDDEN, "hidden panel restored via show()")

        # move_to API
        m.move_to("graph", "tab")
        check(m.get("graph").state == TABBED, "move_to tab works")
        m.move_to("graph", "floating")
        check(m.get("graph").state == FLOATING, "move_to floating works")
        m.move_to("graph", "center")
        check(m.get("graph").state == "docked", "move_to center docks")

        # layout save/load round-trip with real widgets (item 6)
        m.open_as_tab("graph")
        ok = m.save_layout()
        check(ok, "save_layout writes JSON")
        m.hide("graph")
        m.load_layout()
        check(m.get("graph").state == TABBED, "load_layout restores tabbed state")

        # presets
        check(m.apply_preset("compact") is True, "apply_preset returns True")
        check(m.apply_preset("does_not_exist") is False, "unknown preset returns False")

        # WorkspaceManagerWindow lists all panels (item 9)
        from workspace_docking_manager import WorkspaceManagerWindow
        wm = WorkspaceManagerWindow(m, app=root)
        root.update_idletasks()
        check(len(wm.tree.get_children()) == len(m.list_panels()),
              "manager window lists every panel")
        wm.destroy()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"headless docking raised: {exc}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def test_visual_math_integration():
    print("\nVISUAL MATH LAB INTEGRATION")
    import visual_math_lab as vml
    check(hasattr(vml, "SimulationStudioWindow"), "Simulation Studio still present")  # item 11
    check(hasattr(vml, "build_record_figure"), "build_record_figure still present")
    # the lab wires a command registry + docking manager
    check(hasattr(vml.VisualMathLab, "_open_workspace_manager"), "lab exposes workspace manager")
    import command_registry
    check(command_registry.CommandRegistry is not None, "command registry importable")


def test_ui_preferences():
    print("\nUI PREFERENCES (Wacom visibility persistence)")
    from ui_preferences import UIPreferences
    tmp = Path(tempfile.gettempdir())
    # default
    fresh = UIPreferences(tmp / "uiprefs_does_not_exist_999.json")
    check(fresh.get("wacom_visible") is True, "wacom visible default = True")       # item 1
    # toggle + persist
    p = tmp / "uiprefs_roundtrip.json"
    try:
        p.unlink()
    except Exception:
        pass
    store = UIPreferences(p)
    check(store.set("wacom_visible", False), "set wacom_visible False saves")        # item 2/3
    check(UIPreferences(p).get("wacom_visible") is False, "reload keeps wacom hidden")
    store.set("wacom_visible", True)
    check(UIPreferences(p).get("wacom_visible") is True, "toggle back to visible persists")
    # corrupted -> defaults, no crash
    bad = tmp / "uiprefs_corrupt.json"
    bad.write_text("}{ not json", encoding="utf-8")
    check(UIPreferences(bad).get("wacom_visible") is True, "corrupt prefs -> defaults (no crash)")  # item 4


def test_wacom_panel_registered():
    print("\nWACOM PANEL REGISTRATION")
    import tkinter as tk
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] Tk unavailable: {exc}")
        return
    try:
        import visual_math_lab as vml

        class _App:
            language = "en"
        lab = vml.VisualMathLab(root, _App())
        root.update_idletasks()
        mgr = lab._ensure_dock_manager()
        check(mgr is not None, "dock manager created")
        ids = [p.panel_id for p in mgr.list_panels()]
        check("wacom_board_panel" in ids, "workspace manager lists wacom_board_panel")  # item 6
        # show/hide a panel via manager must not crash even with no live host
        mgr.hide("wacom_board_panel")
        mgr.show("wacom_board_panel")
        check(True, "wacom panel show/hide via manager no crash")                       # item 4
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"wacom registration raised: {exc}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def main():
    print("=" * 64)
    print("Workspace Docking Manager — Test Suite")
    print("=" * 64)
    for fn in (test_imports, test_dockable_panel, test_register,
               test_command_registry_duplicate, test_layout_store_missing_and_corrupt,
               test_headless_docking, test_visual_math_integration,
               test_ui_preferences, test_wacom_panel_registered):
        try:
            fn()
        except Exception as exc:
            global FAILED
            FAILED += 1
            import traceback
            traceback.print_exc()
            print(f"   [ERROR] {fn.__name__}: {exc}")
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
