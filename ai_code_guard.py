# -*- coding: utf-8 -*-
"""Math Course AI — static policy guard for AI-generated Python.

WHAT THIS IS
------------
The AI Terminal can ask a model to write a small Python program. Running a
program a language model wrote is dangerous, so this module implements the
layers that sit *around* the human approval dialog:

  1. an explicit ALLOWED-OPERATION POLICY (allowlist of modules, builtins and
     AST node types — everything not listed is refused);
  2. a STATIC CHECKER (`analyze`) that walks the AST before the code is ever
     shown as runnable and reports, per line, what the code would do;
  3. an ISOLATED WORKSPACE (`make_run_workspace`) — a fresh, empty, per-run
     directory, so one run can never see or clobber another run's files;
  4. OS-LEVEL RESOURCE CONTAINMENT on Windows (`_job_object`) — a Job Object
     that caps memory (1 GiB) and the number of processes (2, enough for the
     Windows venv launcher and its interpreter, not enough for a fork bomb)
     and kills the whole tree when the job handle closes.

WHAT THIS IS **NOT**
--------------------
This is **not** a security sandbox and it is not marketed as one.

  * A Windows Job Object caps *resources*. It does **not** stop the child
    process from reading, writing or deleting any file the signed-in user can
    reach, and it does **not** stop network access.
  * A static AST checker can be defeated. Any allowlisted callable that
    reaches dynamic dispatch, and any bug in this module, is a bypass.
  * There is no seccomp/AppContainer/container boundary here.

Because a genuine OS sandbox could not be completed for this release, the
execution feature is **DISABLED BY DEFAULT** in the public build. See
`execution_enabled()`. Enabling it is an informed, explicit choice by the
person running the program, documented in `docs/known-limitations.md`.

The module is deliberately import-light (stdlib only) and every decision
function is pure, so the whole policy is unit-testable without a GUI, a
subprocess or a network.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

__all__ = [
    "POLICY_VERSION", "ALLOWED_MODULES", "ALLOWED_BUILTINS", "BLOCKED_BUILTINS",
    "CAPABILITY_LABELS", "Violation", "AnalysisResult", "analyze",
    "execution_enabled", "ENABLE_ENV_VAR", "make_run_workspace",
    "cleanup_old_workspaces", "run_guarded", "policy_summary",
]

POLICY_VERSION = "1.0"

# ══════════════════════════════════════════════════════════════════════════
# 1. THE ALLOWED-OPERATION POLICY
#    Everything below is an ALLOWLIST. A name that is not listed is refused;
#    the policy never tries to enumerate "dangerous" things.
# ══════════════════════════════════════════════════════════════════════════

#: Top-level modules the generated program may import. Chosen to cover exactly
#: what the terminal advertises: symbolic maths, numerics, plotting, and the
#: pure-computation corners of the standard library.
ALLOWED_MODULES = frozenset({
    # maths / science
    "sympy", "numpy", "math", "cmath", "statistics", "fractions", "decimal",
    "random", "matplotlib", "mpl_toolkits",
    # pure data handling
    "itertools", "functools", "operator", "collections", "heapq", "bisect",
    "string", "textwrap", "re", "json", "csv", "datetime", "time", "copy",
    "enum", "dataclasses", "typing", "abc", "numbers", "pprint", "unicodedata",
    "difflib", "array", "types", "warnings", "contextlib",
})

#: Builtins the generated program may call. `print` is how it returns results.
ALLOWED_BUILTINS = frozenset({
    "abs", "all", "any", "ascii", "bin", "bool", "bytes", "callable", "chr",
    "complex", "dict", "divmod", "enumerate", "filter", "float", "format",
    "frozenset", "hash", "hex", "int", "isinstance", "issubclass", "iter",
    "len", "list", "map", "max", "min", "next", "object", "oct", "ord", "pow",
    "print", "range", "repr", "reversed", "round", "set", "slice", "sorted",
    "str", "sum", "tuple", "zip",
    # exception names the program may legitimately raise/catch
    "ArithmeticError", "AssertionError", "AttributeError", "Exception",
    "IndexError", "KeyError", "NotImplementedError", "OverflowError",
    "RuntimeError", "StopIteration", "TypeError", "ValueError",
    "ZeroDivisionError", "True", "False", "None",
})

#: Builtins that are always refused, with the capability each one grants.
#: (Kept explicit so the approval dialog can name the reason to the human.)
BLOCKED_BUILTINS = {
    "eval": "dynamic-code", "exec": "dynamic-code", "compile": "dynamic-code",
    "__import__": "dynamic-code", "globals": "introspection",
    "locals": "introspection", "vars": "introspection", "dir": "introspection",
    "getattr": "introspection", "setattr": "introspection",
    "delattr": "introspection", "hasattr": "introspection",
    "open": "filesystem", "input": "interactive", "breakpoint": "debugger",
    "memoryview": "memory", "id": "introspection", "super": "introspection",
    "help": "interactive", "exit": "process", "quit": "process",
}

#: Modules that are refused *by name* purely so the message can be specific.
#: (They would be refused anyway for not being in ALLOWED_MODULES.)
_NAMED_MODULE_CAPABILITY = {
    "os": "filesystem", "os.path": "filesystem", "io": "filesystem",
    "pathlib": "filesystem", "shutil": "filesystem", "glob": "filesystem",
    "tempfile": "filesystem", "fileinput": "filesystem", "zipfile": "filesystem",
    "tarfile": "filesystem", "sqlite3": "filesystem", "shelve": "filesystem",
    "socket": "network", "ssl": "network", "urllib": "network",
    "http": "network", "requests": "network", "ftplib": "network",
    "smtplib": "network", "telnetlib": "network", "asyncio": "network",
    "xmlrpc": "network", "webbrowser": "network",
    "subprocess": "process", "multiprocessing": "process", "signal": "process",
    "threading": "process", "sys": "process", "ctypes": "native-code",
    "cffi": "native-code", "mmap": "native-code", "winreg": "system-settings",
    "msvcrt": "system-settings", "platform": "system-info",
    "getpass": "credentials", "keyring": "credentials", "secrets": "credentials",
    "pickle": "deserialization", "marshal": "deserialization",
    "shelve.open": "deserialization", "importlib": "dynamic-code",
    "runpy": "dynamic-code", "code": "dynamic-code", "codeop": "dynamic-code",
    "pty": "process", "pdb": "debugger", "tkinter": "gui", "atexit": "process",
}

CAPABILITY_LABELS = {
    "filesystem": ("dosya sistemi (okuma/yazma/silme)", "the file system (read/write/delete)"),
    "network": ("ağ erişimi", "network access"),
    "process": ("başka program çalıştırma / süreç denetimi", "running other programs / process control"),
    "native-code": ("doğrudan makine kodu çağrısı", "direct native-code calls"),
    "system-settings": ("sistem ve kayıt defteri ayarları", "system and registry settings"),
    "credentials": ("kimlik bilgisi deposu", "the credential store"),
    "deserialization": ("güvensiz veri çözme", "unsafe deserialization"),
    "dynamic-code": ("çalışma anında kod üretme", "generating code at run time"),
    "introspection": ("yorumlayıcı iç yapısına erişim", "interpreter internals"),
    "interactive": ("etkileşimli girdi", "interactive input"),
    "debugger": ("hata ayıklayıcı", "the debugger"),
    "memory": ("ham bellek", "raw memory"),
    "gui": ("pencere yönetimi", "window management"),
    "system-info": ("makine kimlik bilgisi", "machine identity information"),
    "unknown-name": ("tanımlanamayan isim", "an unrecognised name"),
    "unsupported-syntax": ("politikada bulunmayan sözdizimi", "syntax the policy does not cover"),
    "dunder": ("özel (dunder) öznitelik", "a private (dunder) attribute"),
}

#: AST node types the policy understands. Anything else is refused rather than
#: silently permitted — the checker fails closed.
_ALLOWED_NODES = (
    ast.Module, ast.Expression, ast.Interactive,
    ast.Expr, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr,
    ast.If, ast.For, ast.While, ast.Break, ast.Continue, ast.Pass,
    ast.FunctionDef, ast.Return, ast.Lambda, ast.arguments, ast.arg,
    ast.ClassDef, ast.Try, ast.ExceptHandler, ast.Raise, ast.Assert,
    ast.With, ast.withitem, ast.Import, ast.ImportFrom, ast.alias,
    ast.Global, ast.Nonlocal, ast.Delete,
    ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare, ast.Call, ast.IfExp,
    ast.Attribute, ast.Subscript, ast.Starred, ast.Name, ast.Constant,
    ast.List, ast.Tuple, ast.Dict, ast.Set, ast.Slice,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.JoinedStr, ast.FormattedValue,
    ast.keyword, ast.Load, ast.Store, ast.Del,
    ast.And, ast.Or, ast.Not, ast.Invert, ast.UAdd, ast.USub,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor, ast.MatMult,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
)

#: Async and dynamic-import syntax is refused outright: the terminal advertises
#: "a single self-contained script", none of this is needed for that, and each
#: one widens the checker's blind spot.
_REFUSED_NODES = {
    ast.AsyncFunctionDef: "process", ast.AsyncFor: "process",
    ast.AsyncWith: "process", ast.Await: "process", ast.Yield: "unsupported-syntax",
    ast.YieldFrom: "unsupported-syntax",
}

#: Attribute names that reach interpreter internals from *any* object.
_DUNDER_RE = re.compile(r"^__.*__$")
_ALLOWED_DUNDER = frozenset({"__init__", "__repr__", "__str__", "__eq__",
                             "__lt__", "__le__", "__gt__", "__ge__", "__hash__",
                             "__len__", "__iter__", "__next__", "__call__",
                             "__enter__", "__exit__", "__doc__", "__name__"})


class Violation:
    """One refusal, with everything the approval dialog needs to explain it."""

    __slots__ = ("line", "col", "capability", "symbol", "message")

    def __init__(self, line, col, capability, symbol, message):
        self.line = int(line or 0)
        self.col = int(col or 0)
        self.capability = capability
        self.symbol = symbol
        self.message = message

    def as_dict(self):
        return {"line": self.line, "col": self.col, "capability": self.capability,
                "symbol": self.symbol, "message": self.message}

    def __repr__(self):                                    # pragma: no cover
        return f"<Violation line={self.line} {self.capability}:{self.symbol}>"

    def __eq__(self, other):
        return isinstance(other, Violation) and self.as_dict() == other.as_dict()


class AnalysisResult:
    """Verdict of the static checker."""

    __slots__ = ("ok", "violations", "imports", "capabilities", "syntax_error",
                 "policy_version")

    def __init__(self, ok, violations, imports, capabilities, syntax_error=None):
        self.ok = bool(ok)
        self.violations = list(violations)
        self.imports = sorted(imports)
        self.capabilities = sorted(capabilities)
        self.syntax_error = syntax_error
        self.policy_version = POLICY_VERSION

    def as_dict(self):
        return {"ok": self.ok, "policy_version": self.policy_version,
                "violations": [v.as_dict() for v in self.violations],
                "imports": self.imports, "capabilities": self.capabilities,
                "syntax_error": self.syntax_error}

    def summary(self, lang="tr"):
        """One human sentence, for the approval dialog."""
        if self.syntax_error:
            return ("Kod ayrıştırılamadı (sözdizimi hatası): " + self.syntax_error
                    if lang == "tr" else
                    "The code could not be parsed (syntax error): " + self.syntax_error)
        if self.ok:
            mods = ", ".join(self.imports) or ("yok" if lang == "tr" else "none")
            return (f"Statik denetim GEÇTİ · politika v{POLICY_VERSION} · "
                    f"içe aktarılan modüller: {mods}" if lang == "tr" else
                    f"Static check PASSED · policy v{POLICY_VERSION} · "
                    f"imported modules: {mods}")
        caps = ", ".join(CAPABILITY_LABELS.get(c, (c, c))[0 if lang == "tr" else 1]
                         for c in self.capabilities)
        n = len(self.violations)
        return (f"Statik denetim REDDETTİ — {n} ihlal. Bu kod şunlara dokunuyor: {caps}."
                if lang == "tr" else
                f"Static check REFUSED — {n} violation(s). This code touches: {caps}.")


# ══════════════════════════════════════════════════════════════════════════
# 2. THE STATIC CHECKER
# ══════════════════════════════════════════════════════════════════════════

def _root_module(dotted):
    return (dotted or "").split(".", 1)[0]


def analyze(code, allowed_modules=None):
    """Walk `code` and decide whether the policy permits running it.

    Pure: no import of the analysed code, no filesystem, no network.
    Fails CLOSED — an unparseable file or an AST node the policy does not
    model is a refusal, never a pass.
    """
    allowed = frozenset(allowed_modules) if allowed_modules is not None else ALLOWED_MODULES
    violations, imports, capabilities = [], set(), set()

    if not isinstance(code, str) or not code.strip():
        return AnalysisResult(False, [Violation(0, 0, "unsupported-syntax", "",
                                                "Boş kod / empty code")], (), {"unsupported-syntax"})
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return AnalysisResult(False, [Violation(getattr(e, "lineno", 0) or 0,
                                                getattr(e, "offset", 0) or 0,
                                                "unsupported-syntax", "",
                                                str(e.msg))],
                              (), {"unsupported-syntax"}, syntax_error=str(e.msg))

    def add(node, capability, symbol, message):
        capabilities.add(capability)
        violations.append(Violation(getattr(node, "lineno", 0),
                                    getattr(node, "col_offset", 0),
                                    capability, symbol, message))

    # names bound by the program itself (defs, args, assignments, imports…)
    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.add(node.id)
        elif isinstance(node, ast.alias):
            bound.add((node.asname or node.name).split(".", 1)[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.Global):
            bound.update(node.names)
        elif isinstance(node, ast.Nonlocal):
            bound.update(node.names)

    for node in ast.walk(tree):
        for bad_type, cap in _REFUSED_NODES.items():
            if isinstance(node, bad_type):
                add(node, cap, type(node).__name__,
                    f"{type(node).__name__} politikada yok / not permitted by policy")
                break
        else:
            if not isinstance(node, _ALLOWED_NODES):
                add(node, "unsupported-syntax", type(node).__name__,
                    f"{type(node).__name__} politikada modellenmemiş / not modelled by policy")

        # ---- imports -------------------------------------------------------
        if isinstance(node, ast.Import):
            for a in node.names:
                root = _root_module(a.name)
                imports.add(root)
                if root not in allowed:
                    cap = _NAMED_MODULE_CAPABILITY.get(a.name) or \
                          _NAMED_MODULE_CAPABILITY.get(root) or "unknown-name"
                    add(node, cap, a.name, f"import {a.name} — izin listesinde yok / not on the allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.level:                      # relative import: no package here
                add(node, "filesystem", "." * node.level,
                    "göreli içe aktarma / relative import is not permitted")
                continue
            root = _root_module(node.module or "")
            imports.add(root)
            if root not in allowed:
                cap = _NAMED_MODULE_CAPABILITY.get(node.module or "") or \
                      _NAMED_MODULE_CAPABILITY.get(root) or "unknown-name"
                add(node, cap, node.module or "?",
                    f"from {node.module} import … — izin listesinde yok / not on the allowlist")

        # ---- builtin usage -------------------------------------------------
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in BLOCKED_BUILTINS:
                add(node, BLOCKED_BUILTINS[node.id], node.id,
                    f"{node.id}() politikaca yasak / refused by policy")
            elif node.id not in ALLOWED_BUILTINS and node.id not in bound:
                add(node, "unknown-name", node.id,
                    f"'{node.id}' ne tanımlı ne de izinli / neither defined nor allowlisted")

        # ---- attribute access ----------------------------------------------
        elif isinstance(node, ast.Attribute):
            if _DUNDER_RE.match(node.attr) and node.attr not in _ALLOWED_DUNDER:
                add(node, "dunder", node.attr,
                    f".{node.attr} — yorumlayıcı içine erişim / reaches interpreter internals")

        # ---- f-string / str formatting cannot execute; nothing to do here --

    return AnalysisResult(not violations, violations, imports, capabilities)


def policy_summary(lang="tr"):
    """Human-readable statement of what the policy permits — for the UI/docs."""
    mods = ", ".join(sorted(ALLOWED_MODULES))
    if lang == "tr":
        return (f"İzinli modüller (v{POLICY_VERSION}): {mods}.\n"
                "Dosya sistemi, ağ, alt süreç, ctypes, kayıt defteri, pickle ve "
                "çalışma anında kod üretimi REDDEDİLİR. Statik denetim bir "
                "güvenlik sınırı DEĞİLDİR; insan onayının yerine geçmez.")
    return (f"Allowed modules (v{POLICY_VERSION}): {mods}.\n"
            "File system, network, subprocesses, ctypes, registry, pickle and "
            "run-time code generation are REFUSED. The static check is NOT a "
            "security boundary and does not replace human approval.")


# ══════════════════════════════════════════════════════════════════════════
# 3. DEFAULT-OFF SWITCH
# ══════════════════════════════════════════════════════════════════════════

ENABLE_ENV_VAR = "MATH_COURSE_AI_ENABLE_CODE_EXECUTION"
_TRUE = {"1", "true", "yes", "on", "evet", "acik", "açık"}


def execution_enabled(env=None):
    """True only when the operator has explicitly opted in.

    Default in the public build is **False**: no OS sandbox could be completed
    for this release, so running model-written code stays off until a human
    turns it on knowingly. See docs/known-limitations.md.
    """
    src = os.environ if env is None else env
    return str(src.get(ENABLE_ENV_VAR, "")).strip().lower() in _TRUE


# ══════════════════════════════════════════════════════════════════════════
# 4. ISOLATED WORKSPACE
# ══════════════════════════════════════════════════════════════════════════

_WS_PREFIX = "run_"


def make_run_workspace(root):
    """Create a FRESH, EMPTY directory for exactly one run.

    Each approved run gets its own directory, so a run can neither read nor
    overwrite the files of a previous one. Returns the created Path.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    ws = Path(tempfile.mkdtemp(prefix=f"{_WS_PREFIX}{stamp}-", dir=str(root)))
    return ws


def cleanup_old_workspaces(root, keep=20):
    """Keep only the newest `keep` run workspaces; delete the rest."""
    root = Path(root)
    if not root.is_dir():
        return 0
    dirs = sorted((p for p in root.iterdir()
                   if p.is_dir() and p.name.startswith(_WS_PREFIX)),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for p in dirs[max(0, int(keep)):]:
        try:
            shutil.rmtree(p, ignore_errors=True)
            removed += 1
        except Exception:
            pass
    return removed


# ══════════════════════════════════════════════════════════════════════════
# 5. RESOURCE CONTAINMENT (Windows Job Object) — caps resources, NOT rights
# ══════════════════════════════════════════════════════════════════════════

_JOB_MEMORY_BYTES = 1024 * 1024 * 1024          # 1 GiB
#: Why 2 and not 1: on Windows a virtual environment's python.exe is a
#: launcher that spawns the real interpreter as a child. A limit of 1 makes
#: that spawn fail before a single statement runs. Two still stops a fork
#: bomb; one only stopped legitimate runs.
_JOB_MAX_PROCESSES = 2


def _job_object(memory_bytes=_JOB_MEMORY_BYTES, max_processes=_JOB_MAX_PROCESSES):
    """Create a Windows Job Object that caps memory/processes and kills the
    tree when closed. Returns (handle, assign_fn, close_fn) or None.

    HONEST SCOPE: this is resource containment. It does NOT restrict which
    files or hosts the child may reach.
    """
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                        ("WriteOperationCount", ctypes.c_ulonglong),
                        ("OtherOperationCount", ctypes.c_ulonglong),
                        ("ReadTransferCount", ctypes.c_ulonglong),
                        ("WriteTransferCount", ctypes.c_ulonglong),
                        ("OtherTransferCount", ctypes.c_ulonglong)]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                        ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                        ("IoInfo", IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
        JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
        JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
        JobObjectExtendedLimitInformation = 9

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        h = k32.CreateJobObjectW(None, None)
        if not h:
            return None

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_JOB_MEMORY |
            JOB_OBJECT_LIMIT_ACTIVE_PROCESS | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
        info.BasicLimitInformation.ActiveProcessLimit = int(max_processes)
        info.ProcessMemoryLimit = int(memory_bytes)
        info.JobMemoryLimit = int(memory_bytes)
        if not k32.SetInformationJobObject(h, JobObjectExtendedLimitInformation,
                                           ctypes.byref(info), ctypes.sizeof(info)):
            k32.CloseHandle(h)
            return None

        PROCESS_SET_QUOTA, PROCESS_TERMINATE = 0x0100, 0x0001

        def assign(pid):
            ph = k32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, int(pid))
            if not ph:
                return False
            try:
                return bool(k32.AssignProcessToJobObject(h, ph))
            finally:
                k32.CloseHandle(ph)

        def close():
            try:
                k32.CloseHandle(h)
            except Exception:
                pass

        return h, assign, close
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════
# 6. THE GUARDED RUNNER
# ══════════════════════════════════════════════════════════════════════════

#: Environment variables never inherited by the child (keys, tokens, paths of
#: the parent's own data). The child gets a minimal, scrubbed environment.
_ENV_DENY_SUBSTRINGS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL",
                        "AUTH", "SESSION", "COOKIE", "NVIDIA", "OPENAI", "ANTHROPIC",
                        "AWS_", "AZURE", "GITHUB", "GH_", "HF_", "APPDATA")
_ENV_KEEP = ("SystemRoot", "windir", "SystemDrive", "COMSPEC", "NUMBER_OF_PROCESSORS",
             "PROCESSOR_ARCHITECTURE", "PATH", "TEMP", "TMP", "LOCALAPPDATA_UNUSED")


def build_child_env(base_env=None, workspace=None):
    """Minimal, scrubbed environment for the child process (pure, testable)."""
    src = os.environ if base_env is None else base_env
    out = {}
    for k in _ENV_KEEP:
        if k in src:
            out[k] = src[k]
    for k, v in list(out.items()):
        up = k.upper()
        if any(s in up for s in _ENV_DENY_SUBSTRINGS) and k.upper() != "PATH":
            out.pop(k, None)
    if workspace:
        out["TEMP"] = out["TMP"] = str(workspace)
    out["PYTHONDONTWRITEBYTECODE"] = "1"
    out["PYTHONUTF8"] = "1"
    out["PYTHONNOUSERSITE"] = "1"
    out["MPLCONFIGDIR"] = str(workspace) if workspace else out.get("TEMP", "")
    # Never let the child inherit the parent's opt-in: it must not re-enter.
    out.pop(ENABLE_ENV_VAR, None)
    return out


class GuardedRunResult:
    __slots__ = ("status", "stdout", "stderr", "returncode", "workspace",
                 "analysis", "seconds")

    def __init__(self, status, stdout="", stderr="", returncode=None,
                 workspace=None, analysis=None, seconds=0.0):
        self.status = status          # ok | refused_disabled | refused_policy | timeout | error
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.workspace = workspace
        self.analysis = analysis
        self.seconds = seconds

    @property
    def ran(self):
        return self.status in ("ok", "timeout")


def run_guarded(code, workspace_root, timeout=180, env=None,
                allow_when_disabled=False, python_exe=None):
    """Run model-written `code` only if every gate passes.

    Gate order (each one can refuse on its own):
      1. feature switch — off by default in the public build
      2. static policy check
      3. fresh isolated workspace
      4. scrubbed environment + `python -I -B`
      5. Windows Job Object resource caps
      6. hard timeout

    The human approval dialog is a SEPARATE, earlier gate owned by the caller;
    this function never asks and never assumes it happened.
    """
    t0 = time.time()
    if not (execution_enabled(env) or allow_when_disabled):
        return GuardedRunResult("refused_disabled", analysis=None,
                                seconds=time.time() - t0)

    result = analyze(code)
    if not result.ok:
        return GuardedRunResult("refused_policy", analysis=result,
                                seconds=time.time() - t0)

    ws = make_run_workspace(workspace_root)
    child_env = build_child_env(env, ws)
    exe = python_exe or sys.executable
    job = _job_object()
    try:
        proc = subprocess.Popen([exe, "-I", "-B", "-c", code],
                                cwd=str(ws), env=child_env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace")
        if job:
            try:
                job[1](proc.pid)
            except Exception:
                pass
        try:
            out, err = proc.communicate(timeout=timeout)
            status = "ok"
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
            status = "timeout"
        return GuardedRunResult(status, out or "", err or "", proc.returncode,
                                ws, result, time.time() - t0)
    except Exception as e:
        return GuardedRunResult("error", "", str(e), None, ws, result,
                                time.time() - t0)
    finally:
        if job:
            job[2]()
