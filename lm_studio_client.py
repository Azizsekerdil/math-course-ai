# -*- coding: utf-8 -*-
"""Math Course AI — LM Studio istemcisi.

Ana dosyadan (Math_Course_AI.pyw) V48'de mekanik olarak cikarildi.
Yerel LM Studio sunucusuyla tum konusma bu siniftan gecer: model listesi
(60 sn onbellek), profil eslestirme (math/science/vision/...), tamamlama
istekleri ve token kullanim logu.
"""

import re
import json
import time
import base64
import mimetypes
import threading
import urllib.request
import urllib.error
from pathlib import Path

from mca_common import (
    DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_MATH_MODEL, DEFAULT_SCIENCE_MODEL,
    DEFAULT_PHYSICS_MODEL, DEFAULT_CHEMISTRY_MODEL, DEFAULT_DNA_MODEL,
    DEFAULT_CODE_MODEL, DEFAULT_VISION_MODEL, TOKEN_LOG_PATH, estimate_tokens,
    now_iso, safe_output_tokens, guard_url,
)

class LMStudioClient:
    """LM Studio local API client with task-specific model profiles."""

    PROFILE_DEFAULTS = {
        "math": DEFAULT_MATH_MODEL,
        "science": DEFAULT_SCIENCE_MODEL,
        "physics": DEFAULT_PHYSICS_MODEL,
        "chemistry": DEFAULT_CHEMISTRY_MODEL,
        "dna": DEFAULT_DNA_MODEL,
        "code": DEFAULT_CODE_MODEL,
        "vision": DEFAULT_VISION_MODEL,
    }

    PROFILE_KEYWORDS = {
        "math": ["qwen2.5-math", "qwen25-math", "mathstral", "qwen-math", "math"],
        "science": ["qwen3-vl", "qwen3", "mistral-small-3.2", "mistral-small", "qwen2.5-7b", "qwen2.5"],
        "physics": ["qwen3-vl", "qwen3", "mistral-small-3.2", "mistral-small", "qwen2.5"],
        "chemistry": ["mistral-small-3.2", "mistral-small", "qwen3-vl", "qwen3", "qwen2.5"],
        "dna": ["biomistral", "bio-mistral", "bio", "mistral-small-3.2", "qwen3", "qwen2.5"],
        "code": ["deepseek-coder", "coder", "qwen2.5-coder", "qwen-coder"],
        "vision": ["qwen3-vl", "qwen2.5-vl", "qwen25-vl", "qwen2-vl", "internvl", "minicpm-v", "pixtral", "llava", "gemma-3", "moondream", "vision", "vl"],
    }

    def __init__(self, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL, vision_model=DEFAULT_VISION_MODEL, config=None):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.vision_model = (vision_model or DEFAULT_VISION_MODEL).strip()
        self.config = config or {}
        self.model_profiles = self.build_profiles(self.config, self.model, self.vision_model)
        self.lock = threading.Lock()

    def build_profiles(self, config, model, vision_model):
        profiles = dict(self.PROFILE_DEFAULTS)
        profiles["math"] = config.get("math_model") or config.get("model") or model or DEFAULT_MATH_MODEL
        profiles["science"] = config.get("science_model") or DEFAULT_SCIENCE_MODEL
        profiles["physics"] = config.get("physics_model") or profiles["science"]
        profiles["chemistry"] = config.get("chemistry_model") or DEFAULT_CHEMISTRY_MODEL
        profiles["dna"] = config.get("dna_model") or DEFAULT_DNA_MODEL
        profiles["code"] = config.get("code_model") or DEFAULT_CODE_MODEL
        profiles["vision"] = config.get("vision_model") or vision_model or DEFAULT_VISION_MODEL
        return {k: (v or "").strip() for k, v in profiles.items()}

    @staticmethod
    def norm(s):
        return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

    @classmethod
    def match_model(cls, models, preferred="", keywords=None):
        if not models:
            return preferred or ""
        preferred = (preferred or "").strip()
        if preferred and preferred.lower() != "auto":
            pnorm = cls.norm(preferred)
            for m in models:
                if pnorm and pnorm == cls.norm(m):
                    return m
            for m in models:
                if preferred.lower() in m.lower() or pnorm in cls.norm(m):
                    return m
        for kw in (keywords or []):
            knorm = cls.norm(kw)
            for m in models:
                if kw.lower() in m.lower() or knorm in cls.norm(m):
                    return m
        return models[0] if models else (preferred or "")

    @classmethod
    def suggest_profiles_from_models(cls, models, current=None):
        current = current or {}
        suggested = {}
        for profile in ["math", "science", "physics", "chemistry", "dna", "code", "vision"]:
            preferred = current.get(f"{profile}_model") or current.get("vision_model" if profile == "vision" else "model") or cls.PROFILE_DEFAULTS.get(profile, "")
            suggested[profile] = cls.match_model(models, preferred, cls.PROFILE_KEYWORDS.get(profile, []))
        return suggested

    def get_models(self, timeout=8, force=False):
        """Loaded model list, cached for 60 s.

        /v1/models used to be hit on EVERY completion (slow, and one hiccup
        broke the request). The cache keeps requests fast; on a transient
        failure the last known list is reused so a brief server restart no
        longer kills the AI boxes."""
        now = time.time()
        cache = getattr(self, "_models_cache", None)
        if not force and cache and now - cache[0] < 60:
            return cache[1]
        url = guard_url(self.base_url + "/v1/models")
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310 - guard_url() allows only http(s)
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            models = [m.get("id", "") for m in data.get("data", [])]
            self._models_cache = (now, models)
            return models
        except Exception:
            if cache and cache[1]:
                return cache[1]
            raise

    def choose_profile_model(self, profile="math"):
        profile = (profile or "math").lower()
        models = self.get_models()
        preferred = self.model_profiles.get(profile) or self.PROFILE_DEFAULTS.get(profile) or self.model
        chosen = self.match_model(models, preferred, self.PROFILE_KEYWORDS.get(profile, []))
        if profile == "math":
            self.model = chosen
            self.model_profiles["math"] = chosen
        elif profile == "vision":
            self.vision_model = chosen
            self.model_profiles["vision"] = chosen
        else:
            self.model_profiles[profile] = chosen
        return chosen

    def choose_model(self):
        return self.choose_profile_model("math")

    def choose_vision_model(self):
        models = self.get_models()
        if not models:
            return None
        preferred = (self.model_profiles.get("vision") or self.vision_model or "auto").strip()
        if preferred.lower() == "auto":
            preferred = ""
        chosen = self.match_model(models, preferred, self.PROFILE_KEYWORDS["vision"])
        if chosen:
            self.vision_model = chosen
            self.model_profiles["vision"] = chosen
            return chosen
        return None

    def profile_report(self):
        models = self.get_models()
        suggestions = self.suggest_profiles_from_models(models, self.config)
        lines = ["LM Studio reachable.", "", "Loaded models:"]
        lines += [f"- {m}" for m in models] if models else ["- No models returned"]
        lines += ["", "Recommended profile mapping:"]
        labels = [("math", "Math / Matematik"), ("science", "General Science / Genel Bilim"), ("physics", "Physics / Fizik"), ("chemistry", "Chemistry / Kimya"), ("dna", "DNA / Bio"), ("vision", "Vision / Görsel"), ("code", "Code / Kod")]
        for key, label in labels:
            lines.append(f"- {label}: {suggestions.get(key, '')}")
        return "\n".join(lines), suggestions

    def complete(self, system_prompt, user_prompt, max_tokens=None, timeout=120, profile="math"):
        with self.lock:
            try:
                model = self.choose_profile_model(profile)
            except Exception:
                # Soguk baslangicta (cache bos) sunucu kapaliysa get_models
                # istisna firlatir; yukari cikarsa run_ai worker'i olur ve
                # worker_busy takili kalirdi (AI dugmeleri yeniden baslatana
                # kadar kilitli). Yapilandirilmis profil adiyla devam edilir;
                # asagidaki istek dongusu hatayi zaten tuple olarak dondurur.
                model = self.model_profiles.get(profile) or self.model
            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
            if max_tokens is None:
                max_tokens = safe_output_tokens(prompt)
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": 0.15,
                "top_p": 0.85,
                "max_tokens": int(max_tokens),
                "stream": False,
                "stop": ["<|im_end|>", "<|endoftext|>", "<|im_start|>", "</s>"],
                "frequency_penalty": 0.15,
                "presence_penalty": 0.0,
            }
            req = urllib.request.Request(
                self.base_url + "/v1/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            start = time.time()
            last_exc = None
            for attempt in (1, 2):   # one automatic retry on transient failures
                try:
                    guard_url(req.full_url)
                    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - guard_url() allows only http(s)
                        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    text = data.get("choices", [{}])[0].get("text", "").strip()
                    usage = data.get("usage", {})
                    finish = data.get("choices", [{}])[0].get("finish_reason", "")
                    self.log_usage(model, usage, prompt, text, finish, time.time() - start, profile=profile)
                    if finish == "length":
                        text += "\n\n[Note: The model reached the safe token limit. Ask for 'continue' if you want more detail.]"
                    return text, usage, finish
                except urllib.error.HTTPError as exc:
                    last_exc = exc     # 4xx/5xx: retrying rarely helps — fail fast
                    break
                except Exception as exc:
                    last_exc = exc     # timeout / connection reset: retry once
                    if attempt == 1:
                        time.sleep(1.2)
            return (f"AI request failed: {last_exc}\n\n"
                    "LM Studio kapalı veya model yüklenmemiş olabilir. "
                    "Local Server'ın çalıştığını ve bir modelin yüklü olduğunu kontrol et "
                    "(API Test butonuyla bağlantıyı sınayabilirsin)."), {}, "error"

    def complete_with_image(self, system_prompt, user_prompt, image_path, max_tokens=None, timeout=150):
        """Send an image question to a vision-capable LM Studio model."""
        with self.lock:
            model = self.choose_vision_model()
            if not model:
                return (
                    "Image problem solving needs a vision-capable LM Studio model. "
                    "Load qwen3-vl-8b or qwen2.5-vl-7b-instruct in LM Studio, then set Vision Model ID to auto or the exact model name in Settings."
                ), {}, "no_vision_model"

            path = Path(image_path)
            mime = mimetypes.guess_type(str(path))[0] or "image/png"
            data64 = base64.b64encode(path.read_bytes()).decode("ascii")
            if max_tokens is None:
                max_tokens = safe_output_tokens(user_prompt, "answer")
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data64}"}},
                    ]},
                ],
                "temperature": 0.15,
                "top_p": 0.85,
                "max_tokens": int(max_tokens),
                "stream": False,
            }
            req = urllib.request.Request(
                self.base_url + "/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            start = time.time()
            try:
                guard_url(req.full_url)
                with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - guard_url() allows only http(s)
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                msg = data.get("choices", [{}])[0].get("message", {})
                text = msg.get("content", "").strip()
                usage = data.get("usage", {})
                finish = data.get("choices", [{}])[0].get("finish_reason", "")
                self.log_usage(model, usage, user_prompt + "\n[image attached]", text, finish, time.time() - start, profile="vision")
                return text, usage, finish
            except urllib.error.HTTPError as exc:
                details = ""
                try:
                    details = exc.read().decode("utf-8", errors="ignore")[:1200]
                except Exception:
                    pass
                return (
                    "Image request failed. This usually means the selected LM Studio model does not support images or the server rejected the image payload.\n\n"
                    "Fix: load qwen3-vl-8b or qwen2.5-vl-7b-instruct in LM Studio. Then open Settings and set Vision Model ID to auto or the exact model name.\n\n"
                    f"Technical error: HTTP {exc.code} {exc.reason}\n{details}"
                ), {}, "vision_http_error"
            except Exception as exc:
                return (
                    "Image request failed. Check that LM Studio Local Server is running and that a vision-capable model is loaded.\n\n"
                    f"Technical error: {exc}"
                ), {}, "vision_error"

    def log_usage(self, model, usage, prompt, response, finish, seconds, profile="math"):
        record = {
            "time": now_iso(),
            "provider": "yerel",
            "profile": profile,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", estimate_tokens(prompt)),
            "completion_tokens": usage.get("completion_tokens", estimate_tokens(response)),
            "total_tokens": usage.get("total_tokens", estimate_tokens(prompt) + estimate_tokens(response)),
            "finish_reason": finish,
            "seconds": round(seconds, 2),
        }
        try:
            with TOKEN_LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass


