# -*- coding: utf-8 -*-
"""
Command Registry for the Math Course AI program.

A single place to define application commands so that many toolbars / menus can
reference the SAME command (one callback) instead of duplicating button logic.
This is the cleanup mechanism for "the same button repeated in three toolbars".

Design goals:
  * No hard Tkinter dependency at import time (ttk is imported lazily only when
    actually building buttons), so the registry is unit-testable head-less.
  * Idempotent registration: re-registering an id replaces the definition and
    reports it as a duplicate, which keeps a single source of truth per command.
"""


class Command:
    """One named application command."""

    def __init__(self, command_id, label, callback, *, group="general",
                 tooltip=None, shortcut=None, icon=None):
        self.id = command_id
        self.label = label
        self.callback = callback
        self.group = group
        self.tooltip = tooltip
        self.shortcut = shortcut
        self.icon = icon

    def invoke(self, *args, **kwargs):
        if callable(self.callback):
            return self.callback(*args, **kwargs)
        return None

    def to_dict(self):
        return {"id": self.id, "label": self.label, "group": self.group,
                "shortcut": self.shortcut, "tooltip": self.tooltip}

    def __repr__(self):
        return f"<Command {self.id!r} ({self.label!r})>"


class CommandRegistry:
    """Central registry mapping command ids -> Command objects."""

    def __init__(self):
        self._commands = {}
        self._duplicate_count = 0

    # -- registration --------------------------------------------------- #
    def register(self, command_id, label, callback, *, group="general",
                 tooltip=None, shortcut=None, icon=None, replace=True):
        """Register a command. Returns True if it was new, False if it replaced
        an existing id (a duplicate). With replace=False a duplicate is ignored
        and the original kept."""
        is_new = command_id not in self._commands
        if not is_new:
            self._duplicate_count += 1
            if not replace:
                return False
        self._commands[command_id] = Command(
            command_id, label, callback, group=group,
            tooltip=tooltip, shortcut=shortcut, icon=icon)
        return is_new

    def register_many(self, specs):
        """specs: iterable of (command_id, label, callback) or dicts."""
        for spec in specs:
            if isinstance(spec, dict):
                self.register(**spec)
            else:
                self.register(spec[0], spec[1], spec[2],
                              **(spec[3] if len(spec) > 3 else {}))

    # -- queries -------------------------------------------------------- #
    def has(self, command_id):
        return command_id in self._commands

    def get(self, command_id):
        return self._commands.get(command_id)

    def label(self, command_id, default=None):
        cmd = self._commands.get(command_id)
        return cmd.label if cmd else (default if default is not None else command_id)

    def list_commands(self, group=None):
        cmds = list(self._commands.values())
        if group is not None:
            cmds = [c for c in cmds if c.group == group]
        return cmds

    def ids(self):
        return list(self._commands.keys())

    @property
    def duplicate_count(self):
        return self._duplicate_count

    # -- invocation ----------------------------------------------------- #
    def invoke(self, command_id, *args, **kwargs):
        cmd = self._commands.get(command_id)
        if cmd is None:
            return None
        return cmd.invoke(*args, **kwargs)

    # -- Tkinter helpers (lazy import so the module stays head-less) ----- #
    def make_button(self, parent, command_id, **kw):
        """Build a ttk.Button that invokes the given command. Unknown ids get a
        disabled placeholder button instead of crashing."""
        from tkinter import ttk
        cmd = self._commands.get(command_id)
        if cmd is None:
            btn = ttk.Button(parent, text=command_id, state="disabled")
            return btn
        text = kw.pop("text", cmd.label)
        btn = ttk.Button(parent, text=text,
                         command=lambda cid=command_id: self.invoke(cid), **kw)
        return btn

    def build_toolbar(self, toolbar, command_ids, *, side="left", padx=2, pady=0):
        """Pack a row of buttons for the given command ids into `toolbar`.
        Returns the list of created buttons. A None entry inserts a small gap."""
        buttons = []
        for cid in command_ids:
            if cid is None:
                continue
            btn = self.make_button(toolbar, cid)
            btn.pack(side=side, padx=padx, pady=pady)
            buttons.append(btn)
        return buttons


# Language & Science Dictionary command ids (registered against the app).
LANGUAGE_DICTIONARY_COMMANDS = [
    "command.open_language_dictionary",
    "command.translate_sentence",
    "command.translate_image",
    "command.add_term_to_dictionary",
    "command.open_history",
    "command.open_favorites",
    "command.refresh_language_models",
    "command.test_translation_model",
    "command.test_vision_model",
]


def register_language_commands(registry, app):
    """Bind the Language Dictionary commands to a host app. Each command opens
    the relevant Dictionary sub-tab; safe if the app lacks a method."""
    def sub(index):
        return lambda: getattr(app, "open_dictionary_subtab", lambda *_: None)(index)

    specs = [
        ("command.open_language_dictionary", "Language Dictionary", sub(0), {"group": "language"}),
        ("command.translate_sentence", "Sentence Translation", sub(1), {"group": "language"}),
        ("command.translate_image", "Image Translation", sub(2), {"group": "language"}),
        ("command.add_term_to_dictionary", "Add Term", sub(3), {"group": "language"}),
        ("command.open_history", "History", sub(4), {"group": "language"}),
        ("command.open_favorites", "Favorites", sub(6), {"group": "language"}),
        ("command.refresh_language_models", "Refresh Models", sub(7), {"group": "language"}),
        ("command.test_translation_model", "Test Translation", sub(7), {"group": "language"}),
        ("command.test_vision_model", "Test Vision", sub(7), {"group": "language"}),
    ]
    for cid, label, cb, kw in specs:
        registry.register(cid, label, cb, **kw)
    return registry
