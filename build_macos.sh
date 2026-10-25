#!/usr/bin/env bash
# macOS .app paketleme betigi (GitHub Actions macos-latest uzerinde kosar).
# Not: "set -u" BILEREK yok — macOS'un bash 3.2'si bos dizi acilimini
# ("${DIZI[@]}") unbound variable sayar ve betigi kirar.
set -eo pipefail

cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "HATA: macOS .app paketi bir Mac uzerinde olusturulmalidir."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt
# requirements-optional.txt'ten yalnizca izinli lisansli paketler: pymupdf
# (AGPL-3.0-or-commercial) BILEREK haric — proje onu dagitmaz, bkz.
# THIRD_PARTY_NOTICES.md 1. bolum. Uygulama pymupdf olmadan da acilir.
"$PYTHON_BIN" -m pip install \
  opencv-python==4.13.0.92 \
  pytesseract==0.3.13 \
  python-docx==1.2.0 \
  python-pptx==1.0.2
"$PYTHON_BIN" -m pip install pyinstaller

APP_NAME="Math Course AI"
rm -rf build/macos "dist/${APP_NAME}.app" "dist/${APP_NAME}-macOS.zip"
mkdir -p build/macos

# Ikon: depoda yalnizca Windows math_course_ai_icon.ico var; .ico macOS'ta
# gecersizdir. .icns uretilebilecek bir PNG eklenirse sips+iconutil ile
# donusturulur, yoksa uygulama ikonsuz paketlenir.
ICON_ARGS=()
ICON_PNG="math_course_ai_icon.png"
if command -v sips >/dev/null && command -v iconutil >/dev/null && [[ -f "$ICON_PNG" ]]; then
  ICONSET="build/macos/MathCourseAI.iconset"
  mkdir -p "$ICONSET"
  for size in 16 32 128 256 512; do
    sips -z "$size" "$size" "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z "$double" "$double" "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o build/macos/MathCourseAI.icns
  ICON_ARGS=(--icon "$PROJECT_ROOT/build/macos/MathCourseAI.icns")
fi

# --specpath kullanildigi icin --add-data yollari MUTLAK olmali.
DATA_ARGS=()
for item in math_course_ai_icon.ico; do
  [[ -f "$item" ]] && DATA_ARGS+=(--add-data "$PROJECT_ROOT/$item:.")
done

"$PYTHON_BIN" -m PyInstaller --noconfirm --clean --onedir --windowed \
  --workpath build/macos/pyinstaller --specpath build/macos \
  --name "$APP_NAME" \
  --osx-bundle-identifier "com.mathcourseai.desktop" \
  "${ICON_ARGS[@]}" "${DATA_ARGS[@]}" \
  --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageTk \
  --hidden-import PIL.ImageDraw --hidden-import docx --hidden-import pptx \
  --hidden-import pytesseract --hidden-import numpy --hidden-import cv2 \
  --hidden-import sympy --hidden-import matplotlib --hidden-import requests \
  --hidden-import app_paths --hidden-import education --hidden-import token_ledger \
  --hidden-import ai_terminal --hidden-import terminal_tutanak \
  --hidden-import nvidia_provider --hidden-import mca_common \
  --hidden-import lm_studio_client --hidden-import science_labs \
  --hidden-import whiteboard --hidden-import pdf_viewer \
  --hidden-import calculator --hidden-import classic_dictionary \
  --hidden-import topic_knowledge --hidden-import topic_knowledge_round2 \
  --hidden-import student_tracker --hidden-import question_packs \
  --hidden-import language_dictionary --hidden-import visual_math_lab \
  --hidden-import visual_lesson_card --hidden-import workspace_docking_manager \
  --hidden-import command_registry --hidden-import ui_preferences \
  --hidden-import embedded_course_simulations --hidden-import embedded_formula_library \
  --hidden-import course_simulation_library --hidden-import ai_code_guard \
  --hidden-import cloud_consent \
  --collect-submodules simulations --hidden-import sympy.parsing.sympy_parser \
  --hidden-import pypdf \
  --collect-all PIL \
  "$PROJECT_ROOT/Math_Course_AI.pyw"

APP_PATH="dist/${APP_NAME}.app"
[[ -d "$APP_PATH" ]] || { echo "HATA: $APP_PATH olusturulamadi."; exit 1; }

ditto -c -k --keepParent "$APP_PATH" "dist/${APP_NAME}-macOS.zip"
echo "Tamamlandi: $APP_PATH"
echo "Dagitim ZIP'i: dist/${APP_NAME}-macOS.zip"
