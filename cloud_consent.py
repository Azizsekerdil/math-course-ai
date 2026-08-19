# -*- coding: utf-8 -*-
"""Math Course AI — per-session consent gate for the optional cloud provider.

Math Course AI runs its AI features against a LOCAL model by default. A cloud
provider (NVIDIA NIM) is also supported, but it is **never** selected
automatically and **never** contacted implicitly:

  * the default provider is always the local one, whether or not an API key
    happens to exist on the machine;
  * routing anything to the cloud requires an explicit choice **in the current
    session**, recorded here;
  * consent is process-scoped only. It is not written to disk, not remembered
    across restarts, and cannot be pre-set by an environment variable.

Every outbound cloud call in this program goes through `require()`.

Why a separate module: this is the one place a reviewer has to read to know
whether the program can talk to the network, and it must be testable without a
GUI.
"""

from __future__ import annotations

import threading

__all__ = ["CloudConsentRequired", "grant_for_session", "revoke", "is_granted",
           "require", "state", "DISCLOSURE_TR", "DISCLOSURE_EN", "reset_for_tests"]

_lock = threading.Lock()
_granted = False
_granted_provider = None

DISCLOSURE_TR = (
    "Bu seçim, yazdıklarını BİLGİSAYARINDAN ÇIKARIR.\n\n"
    "• İstek metnin ve sohbetin son 12 turu NVIDIA'nın sunucularına gönderilir "
    "(https://integrate.api.nvidia.com).\n"
    "• Ücretsiz deneme uçlarında istek ve yanıtlar NVIDIA tarafından loglanır "
    "(API Trial ToS). Saklama süresi, veri konumu ve eğitim dışı bırakma "
    "seçeneği NVIDIA'nın koşullarına tabidir; bu program bunları garanti edemez.\n"
    "• Öğrenci adı, not defteri, sınav geçmişi ve tutanak GÖNDERİLMEZ — yalnızca "
    "o pencerede senin yazdıkların gider. Kişisel veya hassas bilgi yazma.\n"
    "• Bu izin YALNIZCA bu oturum içindir. Program kapanınca sıfırlanır.\n\n"
    "Yerel model (LM Studio) ile devam edersen hiçbir veri bilgisayarından çıkmaz."
)

DISCLOSURE_EN = (
    "This choice SENDS WHAT YOU TYPE OFF YOUR COMPUTER.\n\n"
    "• Your prompt and the last 12 turns of the conversation are sent to "
    "NVIDIA's servers (https://integrate.api.nvidia.com).\n"
    "• On the free trial endpoints NVIDIA logs requests and answers (API Trial "
    "ToS). Retention period, data location and any training opt-out are "
    "governed by NVIDIA's terms; this program cannot guarantee them.\n"
    "• Student names, notebooks, exam history and the work record are NOT sent "
    "— only what you type in that window. Do not type personal or sensitive data.\n"
    "• This permission lasts for THIS SESSION ONLY and resets when the program "
    "closes.\n\n"
    "If you stay on the local model (LM Studio) nothing leaves your computer."
)


class CloudConsentRequired(RuntimeError):
    """Raised when a cloud call is attempted without session consent."""

    def __init__(self, provider="cloud"):
        super().__init__(
            f"{provider}: bu oturumda bulut kullanımına izin verilmedi — "
            f"istek gönderilmedi. / no cloud consent in this session — "
            f"no request was sent.")
        self.provider = provider


def grant_for_session(provider="NVIDIA NIM"):
    """Record that the user explicitly chose the cloud in THIS session."""
    global _granted, _granted_provider
    with _lock:
        _granted = True
        _granted_provider = provider
    return True


def revoke():
    """Drop consent (used when the user switches back to the local model)."""
    global _granted, _granted_provider
    with _lock:
        _granted = False
        _granted_provider = None
    return True


def is_granted(provider=None):
    with _lock:
        if not _granted:
            return False
        return True if provider is None else (provider == _granted_provider)


def require(provider="cloud"):
    """Gate every outbound cloud call. Raises CloudConsentRequired if not granted."""
    if not is_granted():
        raise CloudConsentRequired(provider)
    return True


def state():
    with _lock:
        return {"granted": _granted, "provider": _granted_provider,
                "scope": "process-session-only", "persisted": False}


def reset_for_tests():
    """Test helper — identical to revoke(), named so intent is obvious."""
    return revoke()
