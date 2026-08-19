# -*- coding: utf-8 -*-
"""Math Course AI — NVIDIA NIM (build.nvidia.com) cloud provider — OPTIONAL.

The program's default AI provider is the LOCAL model (LM Studio): free, and it
keeps the user's data on their own machine. This module is the *optional*
second provider, and it is the ONLY path by which anything leaves.

Contracts:
• EXPLICIT CONSENT PER SESSION. Every outbound call goes through
  ``cloud_consent.require()``. Without a consent recorded in the current
  session no request is built and no byte leaves the machine — see
  ``cloud_consent.py``. Having an API key on the machine is NOT consent.
• ``sohbet()``/``sohbet_akisli()`` DO NOT RAISE for transport problems; they
  return {"ok","metin","usage","model","hata","sure"} so the caller can fall
  back to the local model. Missing consent is the one hard refusal.
• THE KEY IS NEVER WRITTEN TO DISK IN PLAINTEXT: NVIDIA_API_KEY environment
  variable first, then this program's own Windows Credential Manager entry
  (``MathCourseAI/NVIDIA``). No other application's credential store is read.
• On the free trial endpoints NVIDIA logs requests and answers (API Trial
  ToS); the UI says so — do not send personal or sensitive data.

Models are taken from the build.nvidia.com catalogue (all three free
endpoints; the timings below were the queue measurement on 2026-08-14 and
will vary):
  z-ai/glm-5.2                              — fast + accurate (4 s), code/agentic
  nvidia/llama-3.3-nemotron-super-49b-v1.5  — maths + tool calling (42 s)
  openai/gpt-oss-120b                       — MoE reasoning/maths (68 s,
                                              varies with the queue)
"""

import json
import os
import time

import cloud_consent

__all__ = ["NVIDIA_URL", "MODELLER", "VARSAYILAN_MODEL", "anahtar_oku",
           "CONSENT_REQUIRED",
           "anahtar_kaydet", "anahtar_var_mi", "anahtar_maskeli",
           "sohbet", "sohbet_akisli", "durum"]

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
_ANAHTAR_HEDEF = "MathCourseAI/NVIDIA"

MODELLER = ["z-ai/glm-5.2",
            "nvidia/llama-3.3-nemotron-super-49b-v1.5",
            "openai/gpt-oss-120b"]
VARSAYILAN_MODEL = MODELLER[0]

#: This provider always requires per-session consent (cloud_consent.py).
CONSENT_REQUIRED = True


# ══════════════════════════════════════════════════════════════════════════
# ANAHTAR DEPOSU — Windows Credential Manager (ctypes, ek bağımlılık yok)
# ══════════════════════════════════════════════════════════════════════════

def _cred_oku(hedef):
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                        ("LastWritten", wintypes.FILETIME),
                        ("CredentialBlobSize", wintypes.DWORD),
                        ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
                        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
                        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
                        ("UserName", wintypes.LPWSTR)]

        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        advapi.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                     ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
        advapi.CredReadW.restype = wintypes.BOOL
        p = ctypes.POINTER(CREDENTIAL)()
        if not advapi.CredReadW(hedef, 1, 0, ctypes.byref(p)):
            return None
        try:
            blob = ctypes.string_at(p.contents.CredentialBlob,
                                    p.contents.CredentialBlobSize)
            return blob.decode("utf-16-le", errors="ignore") or None
        finally:
            advapi.CredFree(p)
    except Exception:
        return None


def _cred_yaz(deger, hedef):
    if os.name != "nt" or not deger:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                        ("LastWritten", wintypes.FILETIME),
                        ("CredentialBlobSize", wintypes.DWORD),
                        ("CredentialBlob", ctypes.c_char_p),
                        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
                        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
                        ("UserName", wintypes.LPWSTR)]

        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        advapi.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
        advapi.CredWriteW.restype = wintypes.BOOL
        blob = deger.encode("utf-16-le")
        c = CREDENTIAL(Flags=0, Type=1, TargetName=hedef, Comment=None,
                       LastWritten=wintypes.FILETIME(),
                       CredentialBlobSize=len(blob), CredentialBlob=blob,
                       Persist=2, AttributeCount=0, Attributes=None,
                       TargetAlias=None, UserName="mathcourseai")
        return bool(advapi.CredWriteW(ctypes.byref(c), 0))
    except Exception:
        return False


def anahtar_oku():
    """API anahtarı → str veya None.

    Okuma sırası: NVIDIA_API_KEY ortam değişkeni → bu programın KENDİ
    Credential Manager kaydı (MathCourseAI/NVIDIA). Başka bir uygulamanın
    kimlik deposu OKUNMAZ: kullanıcı anahtarı bu programa açıkça vermelidir.
    """
    ortam = (os.getenv("NVIDIA_API_KEY") or "").strip()
    if ortam:
        return ortam
    return _cred_oku(_ANAHTAR_HEDEF)


def anahtar_kaydet(anahtar):
    """Anahtarı Credential Manager'a yazar → (ok, mesaj)."""
    anahtar = (anahtar or "").strip()
    if not anahtar:
        return False, "Anahtar boş."
    if not anahtar.startswith("nvapi-"):
        return False, "NVIDIA anahtarları 'nvapi-' ile başlar; değer yanlış görünüyor."
    if _cred_yaz(anahtar, _ANAHTAR_HEDEF):
        return True, "Anahtar Windows Credential Manager'a kaydedildi (düz metin dosya yok)."
    return False, ("Credential Manager'a yazılamadı. Alternatif: komut satırında "
                   "setx NVIDIA_API_KEY <anahtar>")


def anahtar_var_mi():
    return bool(anahtar_oku())


def anahtar_maskeli():
    """Anahtarın gösterilebilir hâli.

    Arayüze YALNIZCA sağlayıcı adı, durum ve SON 4 karakter çıkar. Önek ya da
    uzunluk gibi ek parçalar gösterilmez: bunlar bir anahtarı daraltmaya
    yarayabilir ve ekran görüntüsü/sunum yoluyla dışarı sızabilir.
    """
    a = anahtar_oku()
    if not a:
        return "YAPILANDIRILMADI / NOT_CONFIGURED"
    return "NVIDIA NIM · HAZIR · " + ("•" * 4) + a[-4:]


# ══════════════════════════════════════════════════════════════════════════
# SOHBET — OpenAI uyumlu
# ══════════════════════════════════════════════════════════════════════════

def _payload_hazirla(payload, model, stream):
    p = dict(payload or {})
    p["model"] = model or p.get("model") or VARSAYILAN_MODEL
    if p["model"] not in MODELLER:
        p["model"] = VARSAYILAN_MODEL
    p["stream"] = bool(stream)
    # NIM ucretsiz uclari max_tokens ister; dusuk tavan uzun cozumleri keser.
    try:
        if int(p.get("max_tokens") or 0) < 2048:
            p["max_tokens"] = 2048
    except Exception:
        p["max_tokens"] = 2048
    return p


def _hata_metni(e):
    ad = type(e).__name__
    m = str(e)
    if "401" in m or "Unauthorized" in m:
        return "Anahtar reddedildi (401) — build.nvidia.com'dan yeni anahtar gerekebilir."
    if "429" in m:
        return "Hız sınırı (429) — ücretsiz uçta kuyruk dolu, biraz bekleyip yeniden dene."
    if "Timeout" in ad or "timed out" in m:
        return "Zaman aşımı — model kuyruğu yoğun olabilir (gpt-oss kuyruğu dalgalıdır)."
    if "Connection" in ad:
        return "Bağlantıya izin verilmedi ya da ağ yok."
    return "%s: %s" % (ad, m)


def sohbet(payload, model=None, timeout=300, anahtar=None):
    """Tek parça sohbet — sohbet_akisli'nin stream=False hâli."""
    return sohbet_akisli(payload, model=model, timeout=timeout,
                         anahtar=anahtar, parca_cb=None, iptal_mi=None,
                         stream=False)


def sohbet_akisli(payload, model=None, timeout=300, anahtar=None,
                  parca_cb=None, iptal_mi=None, stream=True):
    """Akışlı sohbet: her içerik parçası için parca_cb(str) çağrılır.

    iptal_mi: her parçada yoklanır; True dönerse istek kapatılır ve o ana
    kadarki metin ok=True, hata="iptal" ile döner (yarım yanıt atılmaz).
    """
    t0 = time.time()
    sonuc = {"ok": False, "metin": "", "usage": {}, "model": model or VARSAYILAN_MODEL,
             "hata": None, "sure": 0.0}
    # ---- GATE 1: explicit per-session consent. Nothing is built, nothing is
    # sent, and no key is even read until the user has chosen the cloud in
    # THIS session. A key sitting on the machine is not consent.
    if not cloud_consent.is_granted():
        sonuc["hata"] = ("Bu oturumda bulut kullanımına izin verilmedi — istek "
                         "GÖNDERİLMEDİ. Sağlayıcı listesinden NVIDIA NIM'i seçip "
                         "onay penceresini kabul et. / No cloud consent in this "
                         "session — nothing was sent.")
        sonuc["sure"] = round(time.time() - t0, 2)
        return sonuc
    a = (anahtar or "").strip() or anahtar_oku()
    if not a:
        sonuc["hata"] = ("NVIDIA API anahtarı tanımlı değil — AI Terminali'ndeki 🔑 "
                         "düğmesiyle kaydet ya da setx NVIDIA_API_KEY kullan.")
        return sonuc
    try:
        import requests
        p = _payload_hazirla(payload, model, stream)
        sonuc["model"] = p["model"]
        headers = {"Authorization": "Bearer %s" % a,
                   "Accept": "text/event-stream" if stream else "application/json"}
        r = requests.post(NVIDIA_URL, json=p, headers=headers,
                          timeout=(10, timeout), stream=stream)
        # SSE yaniti charset bildirmez; requests ISO-8859-1 varsayar ve Turkce
        # bozulur (canli olculdu). Uc UTF-8 konusur.
        if not r.encoding or "8859" in str(r.encoding):
            r.encoding = "utf-8"
        if r.status_code != 200:
            govde = (r.text or "")[:300]
            sonuc["hata"] = _hata_metni(Exception("HTTP %d: %s" % (r.status_code, govde)))
            return sonuc
        if not stream:
            veri = r.json()
            sonuc["metin"] = (((veri.get("choices") or [{}])[0].get("message") or {})
                              .get("content") or "")
            sonuc["usage"] = veri.get("usage") or {}
            sonuc["ok"] = bool(sonuc["metin"])
            if not sonuc["ok"]:
                sonuc["hata"] = "Yanıt boş döndü."
            return sonuc
        parcalar = []
        for satir in r.iter_lines(decode_unicode=True):
            if iptal_mi and iptal_mi():
                sonuc["hata"] = "iptal"
                break
            if not satir or not satir.startswith("data:"):
                continue
            veri = satir[5:].strip()
            if veri == "[DONE]":
                break
            try:
                obj = json.loads(veri)
            except Exception:
                continue
            if obj.get("usage"):
                sonuc["usage"] = obj["usage"]
            secenekler = obj.get("choices") or []
            if not secenekler:
                continue
            delta = secenekler[0].get("delta") or {}
            parca = delta.get("content")
            if parca:
                parcalar.append(parca)
                if parca_cb:
                    try:
                        parca_cb(parca)
                    except Exception:
                        pass
        try:
            r.close()
        except Exception:
            pass
        sonuc["metin"] = "".join(parcalar)
        sonuc["ok"] = bool(sonuc["metin"])
        if not sonuc["ok"] and not sonuc["hata"]:
            sonuc["hata"] = "Yanıt boş döndü."
        return sonuc
    except Exception as e:
        sonuc["hata"] = _hata_metni(e)
        return sonuc
    finally:
        sonuc["sure"] = round(time.time() - t0, 2)


def durum():
    """Tanılama özeti — anahtarın tamamını içermez."""
    kaynak = "ortam değişkeni" if os.getenv("NVIDIA_API_KEY") else (
        "Credential Manager (MathCourseAI)" if _cred_oku(_ANAHTAR_HEDEF) else "yok")
    return {"anahtar": anahtar_var_mi(), "anahtar_maskeli": anahtar_maskeli(),
            "anahtar_kaynagi": kaynak, "url": NVIDIA_URL, "modeller": list(MODELLER),
            "durum": "YAPILANDIRILMADI" if not anahtar_var_mi() else "HAZIR",
            "oturum_izni": cloud_consent.is_granted()}
