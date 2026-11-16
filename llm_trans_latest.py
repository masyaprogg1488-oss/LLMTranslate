#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import glob
import time
import base64
import ctypes
import tempfile
import urllib.request
import urllib.parse
import subprocess
import threading
import difflib
import shutil
import json
import re
import html
import math

try:
    import pyperclip
except ImportError:
    pyperclip = None

from openai import OpenAI

from PySide6.QtCore import (
    Qt, QTimer, QSize, QPoint, QRect, QRectF, Signal, QObject, QEvent, QBuffer, QIODevice,
    QPropertyAnimation, QVariantAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QTextCursor, QTextCharFormat, QSyntaxHighlighter, QPainterPath
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractButton,
    QProgressBar, QFrame, QListWidget, QListWidgetItem, QFileDialog, QMenu,
    QSizePolicy, QAbstractItemView, QGraphicsOpacityEffect
)

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
IS_FROZEN = getattr(sys, "frozen", False)

UI_FONT = "Segoe UI" if IS_WIN else ("SF Pro Display" if IS_MAC else "Inter")
MONO_FONT = "Consolas" if IS_WIN else ("Menlo" if IS_MAC else "JetBrains Mono")

if IS_WIN:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("llm.translate.app.v12")
    except Exception:
        pass

THEME_PALETTES = {
    "dark": {
        "bg_root": "#0d0f14",
        "bg_surface": "#13161f",
        "bg_surface_alt": "#10131a",
        "bg_input": "#161a24",
        "bg_hover": "#1e2433",
        "bg_popup": "#151923",
        "bg_btn": "#1a1f2c",
        "bg_btn_hover": "#242b3d",
        "bg_btn_disabled": "#12151e",
        "bg_accent": "#2563eb",
        "bg_accent_hover": "#1d4ed8",
        "bg_danger": "#3a1820",
        "bg_danger_hover": "#6b1d2b",
        "danger_border": "#ef4444",
        "vision_purple": "#a855f7",
        "border": "#222836",
        "border_focus": "#3b82f6",
        "text_main": "#f1f5f9",
        "text_muted": "#94a3b8",
        "text_dim": "#475569",
        "code_bg": "#1e2536",
        "code_fg": "#93c5fd",
        "codeblock_bg": "#090b10",
        "codeblock_fg": "#7dd3fc",
        "scroll_handle": "#2b3245",
        "scroll_hover": "#3d4761",
    },
    "amoled": {
        "bg_root": "#000000",
        "bg_surface": "#000000",
        "bg_surface_alt": "#000000",
        "bg_input": "#000000",
        "bg_hover": "#0f1117",
        "bg_popup": "#050507",
        "bg_btn": "#07080b",
        "bg_btn_hover": "#12141c",
        "bg_btn_disabled": "#030304",
        "bg_accent": "#2563eb",
        "bg_accent_hover": "#1d4ed8",
        "bg_danger": "#260b10",
        "bg_danger_hover": "#4c121d",
        "danger_border": "#ef4444",
        "vision_purple": "#a855f7",
        "border": "#181a20",
        "border_focus": "#3b82f6",
        "text_main": "#ffffff",
        "text_muted": "#8e95a5",
        "text_dim": "#3f4451",
        "code_bg": "#0a0c12",
        "code_fg": "#93c5fd",
        "codeblock_bg": "#030406",
        "codeblock_fg": "#60a5fa",
        "scroll_handle": "#1c1f29",
        "scroll_hover": "#2d3242",
    },
    "light": {
        "bg_root": "#f3f5f9",
        "bg_surface": "#ffffff",
        "bg_surface_alt": "#f8fafc",
        "bg_input": "#ffffff",
        "bg_hover": "#eef2f7",
        "bg_popup": "#ffffff",
        "bg_btn": "#e8edf5",
        "bg_btn_hover": "#dce3ef",
        "bg_btn_disabled": "#eef1f6",
        "bg_accent": "#2563eb",
        "bg_accent_hover": "#1d4ed8",
        "bg_danger": "#fee2e2",
        "bg_danger_hover": "#fecaca",
        "danger_border": "#dc2626",
        "vision_purple": "#7c3aed",
        "border": "#d5dce6",
        "border_focus": "#2563eb",
        "text_main": "#0f172a",
        "text_muted": "#475569",
        "text_dim": "#94a3b8",
        "code_bg": "#eef2ff",
        "code_fg": "#1d4ed8",
        "codeblock_bg": "#f1f5f9",
        "codeblock_fg": "#0f172a",
        "scroll_handle": "#cbd5e1",
        "scroll_hover": "#94a3b8",
    }
}

THEME = dict(THEME_PALETTES["dark"])

LM_HOST, LM_PORT = "127.0.0.1", 1234
LOADED_PREFIX = "✓ "
MODEL_SIZE_SEP = "  •  "
SCALE_OPTIONS = [75, 90, 100, 110, 125, 150]

if IS_FROZEN:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

if IS_WIN:
    BASE_DIR = SCRIPT_DIR
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
    _win_local = os.path.expandvars(r"%LOCALAPPDATA%")
    SYS_CACHE_DIR = os.path.join(_win_local if os.path.isdir(_win_local) else tempfile.gettempdir(), "LLMTranslate", "cache")
elif IS_MAC:
    BASE_DIR = os.path.expanduser("~/Library/Application Support/llm-translate")
    os.makedirs(BASE_DIR, exist_ok=True)
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
    SYS_CACHE_DIR = os.path.expanduser("~/Library/Caches/llm-translate")
else:
    BASE_DIR = os.path.expanduser("~/.config/llm-translate")
    os.makedirs(BASE_DIR, exist_ok=True)
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
    SYS_CACHE_DIR = os.path.expanduser("~/.cache/llm-translate")

FLAGS_CACHE_DIR = os.path.join(SYS_CACHE_DIR, "flags_v2")
UI_ICONS_CACHE_DIR = os.path.join(SYS_CACHE_DIR, "ui_v2")
os.makedirs(FLAGS_CACHE_DIR, exist_ok=True)
os.makedirs(UI_ICONS_CACHE_DIR, exist_ok=True)

CDN_UI_ICON_NAMES = {
    "swap": "arrow-left-right",
    "image": "image-plus",
    "tts_play": "volume-2",
    "tts_stop": "volume-x",
    "play": "send-horizontal",
    "stop": "square",
    "refresh": "refresh-cw",
    "server": "server",
    "model_load": "download",
    "vram_clean": "trash-2",
    "settings": "settings",
    "vision": "eye",
}

UI_STRINGS = {
    "ru": {
        "tip_swap": "Поменять языки местами",
        "tip_tts": "Озвучить перевод",
        "tip_go": "Перевести (Ctrl+Enter)",
        "tip_stop": "Остановить перевод",
        "tip_auto_chk": "Автоперевод при вводе текста",
        "tip_image": "Перевести текст с картинки (файл или Ctrl+V)",
        "tip_remove_img": "Убрать картинку",
        "tip_refresh": "Обновить список моделей LM Studio",
        "tip_server": "Запустить сервер LM Studio",
        "tip_load_model": "Загрузить модель в VRAM",
        "tip_vram": "Очистить VRAM",
        "tip_settings": "Настройки",
        "auto_ai": "Автоопределение (ИИ)",
        "auto_fast": "Автоопределение (Быстрое)",
        "auto_ai_short": "Авто ИИ",
        "auto_fast_short": "Авто",
        "select_lang": "Выберите язык...",
        "select_model": "Выберите модель...",
        "no_models": "Нет моделей в LM Studio",
        "offline_model": "LM Studio офлайн",
        "loading": "Загрузка...",
        "auto_trans_chk": "Автоперевод",
        "smart_search_sw": "Умный поиск",
        "settings_title": "Настройки",
        "settings_pin": "Поверх всех окон",
        "settings_thinking": "Режим размышлений",
        "settings_vision_model": "Vision-модель (для картинок)",
        "vision_auto": "Авто (самая лёгкая по размеру)",
        "no_vision_models": "Нет Vision-моделей",
        "settings_theme": "Тема оформления",
        "theme_dark": "Тёмная",
        "theme_amoled": "AMOLED",
        "theme_light": "Светлая",
        "settings_scale": "Масштаб интерфейса",
        "settings_lang": "Язык интерфейса",
        "server_btn": "Сервер",
        "instant_btn": "⚡ Показать сразу",
        "connecting": "Подключение...",
        "ready": "● Готов",
        "choose_lang_right": "Выберите язык справа",
        "choose_model_bottom": "Выберите модель снизу",
        "copied": "✓ Скопировано",
        "copied_sel": "✓ Выделенное скопировано",
        "stopped": "⏹ Остановлено",
        "tts_speaking": "🔊 Озвучивание...",
        "tts_stopped": "⏹ Озвучка остановлена",
        "tts_empty": "Нет текста для озвучки",
        "model_reset": "Модель сброшена",
        "model_ready": "● Модель готова",
        "searching_lms": "Поиск LM Studio",
        "starting_server": "Запуск сервера LM Studio...",
        "server_failed": "✕ Включи Local Server (:1234)",
        "lms_online": "● LM Studio в сети",
        "vram_check": "Очистка VRAM",
        "vram_cleaned_all": "✓ VRAM очищена",
        "vram_cleaned": "✓ VRAM частично очищена",
        "vram_already_empty": "✓ VRAM уже пуста",
        "vram_exit": "Очистка VRAM...",
        "unloading": "Выгрузка",
        "loading_vram": "Загрузка в VRAM",
        "translating": "Перевод",
        "thinking": "Размышление",
        "typing": "Генерация",
        "polishing": "Отполировка",
        "done": "● Готово",
        "conn_err": "✕ Ошибка связи",
        "api_err": "Ошибка API",
        "dict_variants": "варианты перевода и идиомы:",
        "custom_lang_hint": "Нажмите Enter для своего языка",
        "no_matches": "Нет совпадений",
        "ctx_paste_cur": "Вставить (Ctrl+V)",
        "ctx_paste_rep": "Вставить с заменой",
        "ctx_paste_img": "Вставить картинку из буфера",
        "ctx_open_img": "Открыть картинку из файла...",
        "img_translating": "Распознавание и перевод картинки",
        "no_vision_err": "✕ Нет Vision-модели в LM Studio!",
        "ctx_copy": "Копировать (Ctrl+C)",
        "ctx_cut": "Вырезать (Ctrl+X)",
        "ctx_sel_all": "Выделить всё (Ctrl+A)",
        "ctx_bold": "Жирный (**...**)",
        "ctx_italic": "Курсив (*...*)",
        "ctx_code": "Код (`...`)",
        "ctx_strike": "Зачёркнутый (~~...~~)",
        "ctx_clear": "Очистить всё",
        "ctx_copy_sel": "Копировать выделенное (Ctrl+C)",
        "ctx_copy_all": "Копировать весь перевод",
        "warn_prefix": "⚠ Неверный язык:",
        "mismatch_warn": "⚠ Неверный язык: выбран «{src}», но это «{det}»! (Перевод с «{det}»):",
        "mismatch_status": "⚠ Это {det}, а не {src}!"
    },
    "en": {
        "tip_swap": "Swap languages",
        "tip_tts": "Listen to translation",
        "tip_go": "Translate (Ctrl+Enter)",
        "tip_stop": "Stop translation",
        "tip_auto_chk": "Auto-translate while typing",
        "tip_image": "Translate text from image (file or Ctrl+V)",
        "tip_remove_img": "Remove image",
        "tip_refresh": "Refresh LM Studio models",
        "tip_server": "Start LM Studio server",
        "tip_load_model": "Load model into VRAM",
        "tip_vram": "Clear VRAM",
        "tip_settings": "Settings",
        "auto_ai": "Auto Detect (AI)",
        "auto_fast": "Auto Detect (Fast)",
        "auto_ai_short": "Auto AI",
        "auto_fast_short": "Auto",
        "select_lang": "Select language...",
        "select_model": "Select model...",
        "no_models": "No models in LM Studio",
        "offline_model": "LM Studio Offline",
        "loading": "Loading...",
        "auto_trans_chk": "Auto-translate",
        "smart_search_sw": "Smart search",
        "settings_title": "Settings",
        "settings_pin": "Always on top",
        "settings_thinking": "Thinking mode",
        "settings_vision_model": "Vision model (for images)",
        "vision_auto": "Auto (smallest by size)",
        "no_vision_models": "No Vision models",
        "settings_theme": "Theme",
        "theme_dark": "Dark",
        "theme_amoled": "AMOLED",
        "theme_light": "Light",
        "settings_scale": "UI scale",
        "settings_lang": "Interface language",
        "server_btn": "Server",
        "instant_btn": "⚡ Show instantly",
        "connecting": "Connecting...",
        "ready": "● Ready",
        "choose_lang_right": "Select target language",
        "choose_model_bottom": "Select model below",
        "copied": "✓ Copied",
        "copied_sel": "✓ Selection copied",
        "stopped": "⏹ Stopped",
        "tts_speaking": "🔊 Speaking...",
        "tts_stopped": "⏹ Speech stopped",
        "tts_empty": "No translation to speak",
        "model_reset": "Model reset",
        "model_ready": "● Model ready",
        "searching_lms": "Searching LM Studio",
        "starting_server": "Starting LM Studio server...",
        "server_failed": "✕ Enable Local Server (:1234)",
        "lms_online": "● LM Studio Online",
        "vram_check": "Clearing VRAM",
        "vram_cleaned_all": "✓ VRAM cleared",
        "vram_cleaned": "✓ VRAM partially cleared",
        "vram_already_empty": "✓ VRAM already empty",
        "vram_exit": "Clearing VRAM...",
        "unloading": "Unloading",
        "loading_vram": "Loading into VRAM",
        "translating": "Translating",
        "thinking": "Thinking",
        "typing": "Generating",
        "polishing": "Polishing",
        "done": "● Done",
        "conn_err": "✕ Connection error",
        "api_err": "API Error",
        "dict_variants": "translations & idioms:",
        "custom_lang_hint": "Press Enter for custom language",
        "no_matches": "No matches",
        "ctx_paste_cur": "Paste (Ctrl+V)",
        "ctx_paste_rep": "Paste & replace all",
        "ctx_paste_img": "Paste image from clipboard",
        "ctx_open_img": "Open image file...",
        "img_translating": "Reading & translating image",
        "no_vision_err": "✕ No Vision model in LM Studio!",
        "ctx_copy": "Copy (Ctrl+C)",
        "ctx_cut": "Cut (Ctrl+X)",
        "ctx_sel_all": "Select All (Ctrl+A)",
        "ctx_bold": "Bold (**...**)",
        "ctx_italic": "Italic (*...*)",
        "ctx_code": "Code (`...`)",
        "ctx_strike": "Strikethrough (~~...~~)",
        "ctx_clear": "Clear All",
        "ctx_copy_sel": "Copy selection (Ctrl+C)",
        "ctx_copy_all": "Copy full translation",
        "warn_prefix": "⚠ Wrong language:",
        "mismatch_warn": "⚠ Wrong language: \"{src}\" selected, but detected \"{det}\"! (Translated from \"{det}\"):",
        "mismatch_status": "⚠ Detected {det}, not {src}!"
    }
}

ALL_LANG_PLACEHOLDERS = {UI_STRINGS["ru"]["select_lang"], UI_STRINGS["en"]["select_lang"]}
ALL_MODEL_PLACEHOLDERS = {
    UI_STRINGS["ru"]["select_model"], UI_STRINGS["en"]["select_model"],
    UI_STRINGS["ru"]["no_models"], UI_STRINGS["en"]["no_models"],
    UI_STRINGS["ru"]["offline_model"], UI_STRINGS["en"]["offline_model"],
    UI_STRINGS["ru"]["loading"], UI_STRINGS["en"]["loading"],
    UI_STRINGS["ru"]["vision_auto"], UI_STRINGS["en"]["vision_auto"],
    UI_STRINGS["ru"]["no_vision_models"], UI_STRINGS["en"]["no_vision_models"],
}

LANG_ISO_MAP = {
    "Auto AI": "badge_ai", "Auto Fast": "badge_fast",
    "Russian": "ru", "English": "gb", "German": "de",
    "French": "fr", "Spanish": "es", "Italian": "it", "Portuguese": "pt",
    "Chinese (Simplified)": "cn", "Chinese (Traditional)": "tw", "Japanese": "jp",
    "Korean": "kr", "Ukrainian": "ua", "Belarusian": "by", "Kazakh": "kz",
    "Uzbek": "uz", "Kyrgyz": "kg", "Tajik": "tj", "Turkmen": "tm",
    "Azerbaijani": "az", "Armenian": "am", "Georgian": "ge", "Turkish": "tr",
    "Arabic": "sa", "Hebrew": "il", "Persian": "ir", "Hindi": "in",
    "Bengali": "bd", "Urdu": "pk", "Punjabi": "reg-pa", "Tamil": "reg-ta",
    "Telugu": "reg-te", "Marathi": "reg-mr", "Gujarati": "reg-gu", "Kannada": "reg-kn",
    "Malayalam": "reg-ml", "Sinhala": "lk", "Nepali": "np", "Thai": "th",
    "Vietnamese": "vn", "Indonesian": "id", "Malay": "my", "Tagalog": "ph",
    "Burmese": "mm", "Khmer": "kh", "Lao": "la", "Mongolian": "mn",
    "Polish": "pl", "Czech": "cz", "Slovak": "sk", "Hungarian": "hu",
    "Romanian": "ro", "Bulgarian": "bg", "Serbian": "rs", "Croatian": "hr",
    "Bosnian": "ba", "Slovenian": "si", "Macedonian": "mk", "Albanian": "al",
    "Greek": "gr", "Lithuanian": "lt", "Latvian": "lv", "Estonian": "ee",
    "Dutch": "nl", "Swedish": "se", "Norwegian": "no", "Danish": "dk",
    "Finnish": "fi", "Icelandic": "is", "Irish": "ie", "Welsh": "gb-wls",
    "Scottish Gaelic": "gb-sct", "Basque": "reg-eu", "Catalan": "reg-ca",
    "Galician": "reg-gl", "Maltese": "mt", "Luxembourgish": "lu", "Afrikaans": "za",
    "Swahili": "ke", "Amharic": "et", "Yoruba": "ng", "Igbo": "reg-ig",
    "Hausa": "ne", "Zulu": "reg-zu", "Xhosa": "reg-xh", "Somali": "so",
    "Malagasy": "mg", "Kurdish": "reg-ku", "Pashto": "af",
    "Tatar": "reg-tt", "Bashkir": "reg-ba", "Chuvash": "reg-cv", "Chechen": "reg-ce",
    "Ossetian": "reg-os", "Yakut": "reg-sah", "Buryat": "reg-bua", "Udmurt": "reg-udm",
    "Komi": "reg-kv", "Mari": "reg-chm", "Mordvin": "reg-myv",
    "Yiddish": "reg-yi", "Latin": "va",
    "Ancient Greek": "reg-grc", "Old Church Slavonic": "reg-cu", "Sanskrit": "reg-sa",
    "Esperanto": "reg-eo", "Interlingua": "reg-ia", "Toki Pona": "reg-tok",
    "Maori": "nz", "Hawaiian": "reg-haw", "Samoan": "ws", "Cebuano": "reg-ceb",
    "Javanese": "reg-jv", "Sundanese": "reg-su", "Haitian Creole": "ht",
    "Guarani": "py", "Quechua": "pe",
}

TTS_LANG_CODE_MAP = {
    "Russian": "ru", "English": "en", "German": "de", "French": "fr",
    "Spanish": "es", "Italian": "it", "Portuguese": "pt",
    "Chinese (Simplified)": "zh-CN", "Chinese (Traditional)": "zh-TW",
    "Japanese": "ja", "Korean": "ko", "Ukrainian": "uk", "Belarusian": "be",
    "Kazakh": "kk", "Uzbek": "uz", "Turkish": "tr", "Arabic": "ar",
    "Hebrew": "iw", "Persian": "fa", "Hindi": "hi", "Bengali": "bn",
    "Urdu": "ur", "Tamil": "ta", "Telugu": "te", "Thai": "th",
    "Vietnamese": "vi", "Indonesian": "id", "Malay": "ms", "Tagalog": "tl",
    "Polish": "pl", "Czech": "cs", "Slovak": "sk", "Hungarian": "hu",
    "Romanian": "ro", "Bulgarian": "bg", "Serbian": "sr", "Croatian": "hr",
    "Greek": "el", "Lithuanian": "lt", "Latvian": "lv", "Estonian": "et",
    "Dutch": "nl", "Swedish": "sv", "Norwegian": "no", "Danish": "da",
    "Finnish": "fi", "Icelandic": "is", "Catalan": "ca", "Afrikaans": "af",
    "Swahili": "sw", "Latin": "la", "Esperanto": "eo",
}

TTS_BCP47_MAP = {
    "Russian": "ru-RU", "English": "en-US", "German": "de-DE", "French": "fr-FR",
    "Spanish": "es-ES", "Italian": "it-IT", "Portuguese": "pt-PT",
    "Chinese (Simplified)": "zh-CN", "Chinese (Traditional)": "zh-TW",
    "Japanese": "ja-JP", "Korean": "ko-KR", "Ukrainian": "uk-UA",
    "Polish": "pl-PL", "Turkish": "tr-TR", "Arabic": "ar-SA", "Hindi": "hi-IN",
    "Dutch": "nl-NL", "Swedish": "sv-SE", "Czech": "cs-CZ", "Greek": "el-GR",
}

LANG_DATA = {
    "Auto AI": ("Автоопределение (ИИ)", "auto ai ии нейросеть автоопределение"),
    "Auto Fast": ("Автоопределение (Быстрое)", "auto fast быстрое автоопределение символ"),
    "Russian": ("Русский", "ru русский раша"),
    "English": ("Английский", "en английский инглиш"),
    "German": ("Немецкий", "de немецкий дойч германский"),
    "French": ("Французский", "fr французский"),
    "Spanish": ("Испанский", "es испанский"),
    "Italian": ("Итальянский", "it итальянский"),
    "Portuguese": ("Португальский", "pt португальский"),
    "Chinese (Simplified)": ("Китайский (упр.)", "zh китайский упрощенный"),
    "Chinese (Traditional)": ("Китайский (трад.)", "zh китайский традиционный"),
    "Japanese": ("Японский", "ja японский"),
    "Korean": ("Корейский", "ko корейский"),
    "Ukrainian": ("Украинский", "uk украинский"),
    "Belarusian": ("Белорусский", "be белорусский"),
    "Kazakh": ("Казахский", "kk казахский"),
    "Uzbek": ("Узбекский", "uz узбекский"),
    "Kyrgyz": ("Киргизский", "ky киргизский кыргызский"),
    "Tajik": ("Таджикский", "tg таджикский"),
    "Turkmen": ("Туркменский", "tk туркменский"),
    "Azerbaijani": ("Азербайджанский", "az азербайджанский"),
    "Armenian": ("Армянский", "hy армянский"),
    "Georgian": ("Грузинский", "ka грузинский"),
    "Turkish": ("Турецкий", "tr турецкий"),
    "Arabic": ("Арабский", "ar арабский"),
    "Hebrew": ("Иврит", "he иврит"),
    "Persian": ("Персидский", "fa персидский фарси"),
    "Hindi": ("Хинди", "hi хинди индийский"),
    "Bengali": ("Бенгальский", "bn бенгальский"),
    "Urdu": ("Урду", "ur урду"),
    "Punjabi": ("Панджаби", "pa панджаби"),
    "Tamil": ("Тамильский", "ta тамильский"),
    "Telugu": ("Телугу", "te телугу"),
    "Marathi": ("Маратхи", "mr маратхи"),
    "Gujarati": ("Гуджарати", "gu гуджарати"),
    "Kannada": ("Каннада", "kn каннада"),
    "Malayalam": ("Малаялам", "ml малаялам"),
    "Sinhala": ("Сингальский", "si сингальский"),
    "Nepali": ("Непальский", "ne непальский"),
    "Thai": ("Тайский", "th тайский"),
    "Vietnamese": ("Вьетнамский", "vi вьетнамский"),
    "Indonesian": ("Индонезийский", "id индонезийский"),
    "Malay": ("Малайский", "ms малайский"),
    "Tagalog": ("Тагальский", "tl тагальский филиппинский"),
    "Burmese": ("Бирманский", "my бирманский"),
    "Khmer": ("Кхмерский", "km кхмерский"),
    "Lao": ("Лаосский", "lo лаосский"),
    "Mongolian": ("Монгольский", "mn монгольский"),
    "Polish": ("Польский", "pl польский"),
    "Czech": ("Чешский", "cs чешский"),
    "Slovak": ("Словацкий", "sk словацкий"),
    "Hungarian": ("Венгерский", "hu венгерский"),
    "Romanian": ("Румынский", "ro румынский"),
    "Bulgarian": ("Болгарский", "bg болгарский"),
    "Serbian": ("Сербский", "sr сербский"),
    "Croatian": ("Хорватский", "hr хорватский"),
    "Bosnian": ("Боснийский", "bs боснийский"),
    "Slovenian": ("Словенский", "sl словенский"),
    "Macedonian": ("Македонский", "mk македонский"),
    "Albanian": ("Албанский", "sq албанский"),
    "Greek": ("Греческий", "el греческий"),
    "Lithuanian": ("Литовский", "lt литовский"),
    "Latvian": ("Латышский", "lv латышский"),
    "Estonian": ("Эстонский", "et эстонский"),
    "Dutch": ("Нидерландский", "nl нидерландский голландский"),
    "Swedish": ("Шведский", "sv шведский"),
    "Norwegian": ("Норвежский", "no норвежский"),
    "Danish": ("Датский", "da датский"),
    "Finnish": ("Финский", "fi финский"),
    "Icelandic": ("Исландский", "is исландский"),
    "Irish": ("Ирландский", "ga ирландский"),
    "Welsh": ("Валлийский", "cy валлийский"),
    "Scottish Gaelic": ("Шотландский гэльский", "gd шотландский гэльский"),
    "Basque": ("Баскский", "eu баскский"),
    "Catalan": ("Каталанский", "ca каталанский каталонский"),
    "Galician": ("Галисийский", "gl галисийский"),
    "Maltese": ("Мальтийский", "mt мальтийский"),
    "Luxembourgish": ("Люксембургский", "lb люксембургский"),
    "Afrikaans": ("Африкаанс", "af африкаанс"),
    "Swahili": ("Суахили", "sw суахили"),
    "Amharic": ("Амхарский", "am амхарский"),
    "Yoruba": ("Йоруба", "yo йоруба"),
    "Igbo": ("Игбо", "ig игбо"),
    "Hausa": ("Хауса", "ha хауса"),
    "Zulu": ("Зулу", "zu зулу"),
    "Xhosa": ("Коса", "xh коса"),
    "Somali": ("Сомалийский", "so сомалийский"),
    "Malagasy": ("Малагасийский", "mg малагасийский"),
    "Kurdish": ("Курдский", "ku курдский"),
    "Pashto": ("Пушту", "ps пушту"),
    "Tatar": ("Татарский", "tt татарский"),
    "Bashkir": ("Башкирский", "ba башкирский"),
    "Chuvash": ("Чувашский", "cv чувашский"),
    "Chechen": ("Чеченский", "ce чеченский"),
    "Ossetian": ("Осетинский", "os осетинский"),
    "Yakut": ("Якутский", "sah якутский саха"),
    "Buryat": ("Бурятский", "bua бурятский"),
    "Udmurt": ("Удмуртский", "udm удмуртский"),
    "Komi": ("Коми", "kv коми"),
    "Mari": ("Марийский", "chm марийский"),
    "Mordvin": ("Мордовский", "myv мордовский эрзянский мокшанский"),
    "Yiddish": ("Идиш", "yi идиш"),
    "Latin": ("Латынь", "la латынь латинский"),
    "Ancient Greek": ("Древнегреческий", "grc древнегреческий"),
    "Old Church Slavonic": ("Старославянский", "cu старославянский церковнославянский"),
    "Sanskrit": ("Санскрит", "sa санскрит"),
    "Esperanto": ("Эсперанто", "eo эсперанто"),
    "Interlingua": ("Интерлингва", "ia интерлингва"),
    "Toki Pona": ("Токи пона", "tok токи пона"),
    "Maori": ("Маори", "mi маори"),
    "Hawaiian": ("Гавайский", "haw гавайский"),
    "Samoan": ("Самоанский", "sm самоанский"),
    "Cebuano": ("Себуанский", "ceb себуанский"),
    "Javanese": ("Яванский", "jv яванский"),
    "Sundanese": ("Сунданский", "su сунданский"),
    "Haitian Creole": ("Гаитянский креольский", "ht гаитянский креольский"),
    "Guarani": ("Гуарани", "gn гуарани"),
    "Quechua": ("Кечуа", "qu кечуа"),
}

AUTO_MODES_CANON = {"Auto AI", "Auto Fast"}

RE_LEADING_FLAG_OR_ISO = re.compile(
    r"^(?:[\U0001F1E6-\U0001F1FF]{2}|[\U0001F300-\U0001FAFF\u2600-\u27BF]+|[A-Z]{2}\s+(?=[A-ZА-ЯЁ]))\s*"
)


def strip_flag_prefix(val):
    if not val:
        return ""
    return RE_LEADING_FLAG_OR_ISO.sub("", val.strip()).strip()


LANG_EN_TO_RU = {en: data[0] for en, data in LANG_DATA.items()}
LANG_RU_TO_EN = {data[0].lower(): en for en, data in LANG_DATA.items()}
LANG_MAP = {en: f"{en.lower()} {data[0].lower()} {data[1]}" for en, data in LANG_DATA.items()}
for en, data in LANG_DATA.items():
    LANG_MAP[data[0]] = LANG_MAP[en]

WORLD_LANGUAGES_EN = list(LANG_DATA.keys())
TARGET_LANGUAGES_EN = [l for l in WORLD_LANGUAGES_EN if l not in AUTO_MODES_CANON]

POS_CANONICAL_PAIRS = [
    ("причастие / предикатив", "participle / predicative"),
    ("причастие / прилагательное", "participle / adjective"),
    ("причастие", "participle"),
    ("предикатив", "predicative"),
    ("прилагательное", "adjective"),
    ("существительное", "noun"),
    ("глагол (прошедшее время)", "verb (past tense)"),
    ("глагол / существительное", "verb / noun"),
    ("глагол", "verb"),
    ("наречие", "adverb"),
    ("местоимение", "pronoun"),
    ("предлог", "preposition"),
    ("союз", "conjunction"),
    ("междометие", "interjection"),
    ("частица", "particle"),
    ("числительное", "numeral"),
    ("фразовый глагол", "phrasal verb"),
    ("сленг / разговорное", "slang / colloquial"),
    ("сленг / идиомы", "slang / idioms"),
    ("сленг", "slang"),
    ("разговорное", "colloquial"),
    ("фразеологизмы и идиомы", "idioms & phrases"),
    ("идиомы и фразеологизмы", "idioms & phrases"),
    ("фразеологизмы", "idioms & set phrases"),
    ("идиомы", "idioms"),
    ("устойчивые выражения", "set phrases"),
    ("пословицы и поговорки", "proverbs & sayings"),
    ("исконные аналоги / значение", "native equivalents / meaning"),
    ("исконные аналоги", "native equivalents"),
    ("значение / толкование", "meaning / definition"),
    ("значение", "meaning"),
]

POS_RU_TO_EN = {ru: en for ru, en in POS_CANONICAL_PAIRS}
POS_EN_TO_RU = {en: ru for ru, en in POS_CANONICAL_PAIRS}
POS_TOKEN_RU_TO_EN = {
    "причастие": "participle",
    "предикатив": "predicative",
    "adjective": "adjective",
    "прилагательное": "adjective",
    "существительное": "noun",
    "глагол": "verb",
    "наречие": "adverb",
    "местоимение": "pronoun",
    "междометие": "interjection",
    "сленг": "slang",
    "разговорное": "colloquial",
    "фразеологизмы": "idioms",
    "идиомы": "idioms",
    "исконные аналоги": "native equivalents",
    "значение": "meaning",
    "прошедшее время": "past tense",
    " и ": " & ",
}
POS_TOKEN_EN_TO_RU = {
    "participle": "причастие",
    "predicative": "предикатив",
    "adjective": "прилагательное",
    "noun": "существительное",
    "verb": "глагол",
    "adverb": "наречие",
    "pronoun": "местоимение",
    "interjection": "междометие",
    "slang": "сленг",
    "colloquial": "разговорное",
    "idioms & phrases": "фразеологизмы и идиомы",
    "idioms": "фразеологизмы",
    "phrases": "выражения",
    "set phrases": "устойчивые выражения",
    "native equivalents": "исконные аналоги",
    "meaning": "значение",
    "past tense": "прошедшее время",
    " & ": " и ",
}

CJK_LANGUAGES = {"Chinese (Simplified)", "Chinese (Traditional)", "Japanese", "Korean"}
CYRILLIC_LANGUAGES = {
    "Russian", "Ukrainian", "Belarusian", "Kazakh", "Kyrgyz", "Tajik",
    "Bulgarian", "Serbian", "Macedonian", "Mongolian", "Tatar", "Bashkir",
    "Chuvash", "Chechen", "Ossetian", "Yakut", "Buryat", "Udmurt", "Komi",
    "Mari", "Mordvin", "Old Church Slavonic"
}

RE_CJK_GARBAGE = re.compile(
    r"[\u2e80-\u2eff\u3000-\u303f\u3040-\u30ff\u31c0-\u31ef\u3200-\u32ff"
    r"\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff\uff00-\uffef\ufffd]+"
)
RE_SPECIAL_TOKENS = re.compile(
    r"(?:<\|[^>]*?\|>|<｜[^>]*?｜>|</?s>|<end_of_turn>|<start_of_turn>|\[/?INST\]|</?(?:source_text|translation)>)+",
    flags=re.IGNORECASE
)
RE_THINK_BLOCKS = re.compile(
    r"(?:<think>.*?</think>|<thought>.*?</thought>|◁think▷.*?◁/think▷)",
    flags=re.DOTALL | re.IGNORECASE
)
RE_UNCLOSED_THINK = re.compile(
    r"(?:<think>|<thought>|◁think▷).*$",
    flags=re.DOTALL | re.IGNORECASE
)
RE_CYRILLIC_CHARS = re.compile(r"[а-яА-ЯёЁ]")
RE_EMOJI_CHARS = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]+")

RE_MD_TOKEN = re.compile(
    r"(```[\s\S]*?```)"
    r"|(`[^`\n]+`)"
    r"|(\*\*\*[^\*\n]+\*\*\*)"
    r"|(\*\*[^\*\n]+\*\*|__[^_\n]+__)"
    r"|(\*[^\*\n]+\*|_[^_\n]+_)"
    r"|(~~[^~\n]+~~)"
    r"|(\+\+[^\+\n]+\+\+)"
)

INVALID_LANG_PLACEHOLDERS = {
    "unknown", "auto", "auto detect", "автоопределение", "авто", "none",
    "truelanguageinenglish", "detectedlanguageinenglish", "detectedlanguage",
    "sourcelanguage", "language", "lang", "inputlanguage", "actual_language",
    "sourcelanguageinenglish"
}

LAYOUT_RU_TO_EN = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбю",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,."
)
PHONETIC_RU_TO_EN = {
    "квен": "qwen", "ламах": "llama", "лама": "llama", "дипсик": "deepseek",
    "мистрал": "mistral", "гемма": "gemma", "джема": "gemma", "фи": "phi",
    "айя": "aya", "ая": "aya", "евро": "euro", "вихрь": "vikhr"
}


def fast_detect_language_by_script(text):
    if not text:
        return None
    sample = re.sub(r"[`*_~#\d\s\W_]+", " ", text).strip()[:240]
    if not sample:
        return None

    for ch in sample:
        cp = ord(ch)
        if 0x3040 <= cp <= 0x30FF:
            return "Japanese"
        if 0xAC00 <= cp <= 0xD7AF or 0x1100 <= cp <= 0x11FF:
            return "Korean"
        if 0x4E00 <= cp <= 0x9FFF:
            return "Chinese (Simplified)"
        if 0x0600 <= cp <= 0x06FF:
            return "Arabic"
        if 0x0590 <= cp <= 0x05FF:
            return "Hebrew"
        if 0x0900 <= cp <= 0x097F:
            return "Hindi"
        if 0x0E00 <= cp <= 0x0E7F:
            return "Thai"
        if 0x0370 <= cp <= 0x03FF:
            return "Greek"
        if 0x0530 <= cp <= 0x058F:
            return "Armenian"
        if 0x10A0 <= cp <= 0x10FF:
            return "Georgian"

    cyr_chars = re.findall(r"[а-яА-ЯёЁіїєґўқғңүұһәө]", sample)
    if cyr_chars:
        s_low = sample.lower()
        if any(c in s_low for c in ("і", "ї", "є", "ґ")):
            return "Ukrainian"
        if "ў" in s_low:
            return "Belarusian"
        if any(c in s_low for c in ("қ", "ғ", "ң", "ү", "ұ", "һ", "ә")):
            return "Kazakh"
        return "Russian"

    words = set(re.findall(r"[a-zA-Z\u00C0-\u024F]+", sample.lower()))
    if not words:
        return None

    latin_scores = {
        "Latin": len(words & {"et", "in", "non", "est", "cum", "ad", "per", "sed", "autem", "erat", "deus", "terra", "caelum", "quod", "qui", "quae", "hoc", "ipse", "lux", "fiat"}),
        "German": len(words & {"der", "die", "das", "und", "ist", "nicht", "ich", "ein", "eine", "auf", "für", "mit", "zu", "den", "von"}) + (2 if re.search(r"[äöüß]", sample.lower()) else 0),
        "French": len(words & {"le", "la", "les", "des", "est", "dans", "pour", "pas", "que", "une", "avec", "sur", "je", "nous", "vous"}) + (2 if re.search(r"[àâçéèêëîïôùûüÿœ]", sample.lower()) else 0),
        "Spanish": len(words & {"el", "la", "los", "las", "de", "que", "en", "por", "para", "con", "una", "es", "como", "pero", "yo"}) + (2 if re.search(r"[ñ¿¡áéíóú]", sample.lower()) else 0),
        "Italian": len(words & {"il", "lo", "gli", "che", "non", "per", "sono", "una", "con", "anche", "questo", "alla", "della"}),
        "Portuguese": len(words & {"os", "as", "não", "com", "uma", "para", "por", "mais", "como", "você", "isso"}) + (2 if re.search(r"[ãõçêô]", sample.lower()) else 0),
        "Polish": len(words & {"nie", "się", "jest", "jak", "ale", "czy", "już", "tylko", "bardzo"}) + (2 if re.search(r"[ąćęłńóśźż]", sample.lower()) else 0),
        "Turkish": len(words & {"bir", "ve", "bu", "için", "ile", "değil", "ama", "çok"}) + (2 if re.search(r"[ğışİöüç]", sample.lower()) else 0),
        "English": len(words & {"the", "and", "is", "are", "to", "of", "in", "that", "for", "with", "you", "this", "from", "have", "not", "it", "was"}),
    }
    best_lang, best_sc = max(latin_scores.items(), key=lambda kv: kv[1])
    if best_sc >= 1:
        return best_lang
    return "English"


def transliterate_en_to_ru_phonetic(text):
    t = text.lower()
    digraphs = [
        ("tion", "шн"), ("sion", "жн"), ("ough", "о"), ("ight", "айт"),
        ("sh", "ш"), ("ch", "ч"), ("th", "з"), ("ph", "ф"), ("wh", "в"),
        ("ck", "к"), ("qu", "кв"), ("oo", "у"), ("ee", "и"), ("ea", "и"),
        ("ai", "эй"), ("ay", "эй"), ("ou", "ау"), ("ow", "оу"), ("ng", "нг"),
    ]
    for src, dst in digraphs:
        t = t.replace(src, dst)
    char_map = {
        "a": "э", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф",
        "g": "г", "h": "х", "i": "и", "j": "дж", "k": "к", "l": "л",
        "m": "м", "n": "н", "o": "о", "p": "п", "q": "к", "r": "р",
        "s": "с", "t": "т", "u": "ю", "v": "в", "w": "в", "x": "кс",
        "y": "й", "z": "з"
    }
    return "".join(char_map.get(ch, ch) for ch in t)


def get_win_short_path(path):
    if not IS_WIN or not os.path.exists(path):
        return path
    try:
        buf = ctypes.create_unicode_buffer(512)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 512) > 0:
            return buf.value
    except Exception:
        pass
    return path


def resource_path(relative_path):
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand = os.path.join(meipass, relative_path)
        if os.path.exists(cand):
            return cand
    cand_script = os.path.join(SCRIPT_DIR, relative_path)
    if os.path.exists(cand_script):
        return cand_script
    return os.path.join(BASE_DIR, relative_path)


def find_user_asset(subpath_no_ext):
    """Ищет пользовательскую картинку в icons/<subpath>.(png|svg) рядом со скриптом или внутри PyInstaller bundle."""
    for ext in (".png", ".svg"):
        rel = os.path.join("icons", subpath_no_ext + ext)
        p = resource_path(rel)
        if os.path.isfile(p) and os.path.getsize(p) > 32:
            return p
    return None


def strip_loaded_prefix(val):
    if not val:
        return ""
    s = val.strip()
    if s.startswith(LOADED_PREFIX):
        s = s[len(LOADED_PREFIX):].strip()
    if MODEL_SIZE_SEP in s:
        s = s.split(MODEL_SIZE_SEP, 1)[0].strip()
    return s


def format_bytes_size(size_bytes):
    try:
        b = float(size_bytes)
    except (TypeError, ValueError):
        return ""
    if b <= 0:
        return ""
    gb = b / (1024 ** 3)
    if gb >= 1.0:
        return f"{gb:.1f} GB"
    mb = b / (1024 ** 2)
    return f"{max(1, int(round(mb)))} MB"


def resolve_lms_executable():
    path_bin = shutil.which("lms")
    if path_bin:
        return path_bin
    candidates = [
        os.path.expanduser("~/.lmstudio/bin/lms"),
        os.path.expanduser(r"~\.lmstudio\bin\lms.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\LM-Studio\app\bin\lms.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\LM Studio\resources\app\.webpack\lms.exe"),
        "/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms",
        "/opt/LM Studio/resources/app/.webpack/lms",
        "/usr/local/bin/lms",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "lms"


def resolve_lm_studio_gui_exe():
    if IS_WIN:
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\LM Studio\LM Studio.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\LM-Studio\LM Studio.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\LM Studio\LM Studio.exe"),
            os.path.expanduser(r"~\AppData\Local\Programs\LM Studio\LM Studio.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
    elif IS_MAC:
        mac_path = "/Applications/LM Studio.app/Contents/MacOS/LM Studio"
        if os.path.isfile(mac_path):
            return mac_path
    else:
        which_gui = shutil.which("lm-studio") or shutil.which("lmstudio")
        if which_gui:
            return which_gui
        linux_candidates = [
            "/opt/LM Studio/lm-studio",
            "/opt/lm-studio/lm-studio",
            "/usr/bin/lm-studio",
            os.path.expanduser("~/.local/bin/lm-studio"),
        ]
        for pattern in (
            os.path.expanduser("~/Applications/LM*Studio*.AppImage"),
            os.path.expanduser("~/LM*Studio*.AppImage"),
            os.path.expanduser("~/Downloads/LM*Studio*.AppImage"),
        ):
            linux_candidates.extend(sorted(glob.glob(pattern), reverse=True))
        for c in linux_candidates:
            if os.path.isfile(c):
                return c
    return None


LMS_BIN = resolve_lms_executable()
LM_STUDIO_GUI_EXE = resolve_lm_studio_gui_exe()


def blend_colors(c1_hex, c2_hex, t):
    t = max(0.0, min(1.0, float(t)))
    c1 = QColor(c1_hex)
    c2 = QColor(c2_hex)
    r = int(round(c1.red() + (c2.red() - c1.red()) * t))
    g = int(round(c1.green() + (c2.green() - c1.green()) * t))
    b = int(round(c1.blue() + (c2.blue() - c1.blue()) * t))
    return QColor(r, g, b)


class AnimatedToggleSwitch(QAbstractButton):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont(UI_FONT, 10))
        self._thumb_pos = 0.0
        self._hover_level = 0.0

        self._anim_pos = QVariantAnimation(self)
        self._anim_pos.setDuration(170)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_pos.valueChanged.connect(self._on_pos_changed)

        self._anim_hover = QVariantAnimation(self)
        self._anim_hover.setDuration(130)
        self._anim_hover.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_hover.valueChanged.connect(self._on_hover_changed)

        self.toggled.connect(self._start_toggle_anim)

    def _on_pos_changed(self, val):
        self._thumb_pos = float(val)
        self.update()

    def _on_hover_changed(self, val):
        self._hover_level = float(val)
        self.update()

    def _start_toggle_anim(self, checked):
        self._anim_pos.stop()
        self._anim_pos.setStartValue(self._thumb_pos)
        self._anim_pos.setEndValue(1.0 if checked else 0.0)
        self._anim_pos.start()

    def setChecked(self, checked):
        super().setChecked(checked)
        if not self._anim_pos.state():
            self._thumb_pos = 1.0 if checked else 0.0
            self.update()

    def enterEvent(self, event):
        self._anim_hover.stop()
        self._anim_hover.setStartValue(self._hover_level)
        self._anim_hover.setEndValue(1.0)
        self._anim_hover.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim_hover.stop()
        self._anim_hover.setStartValue(self._hover_level)
        self._anim_hover.setEndValue(0.0)
        self._anim_hover.start()
        super().leaveEvent(event)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        txt_w = fm.horizontalAdvance(self.text()) if self.text() else 0
        h = max(22, fm.height() + 6)
        w = 36 + (8 + txt_w if txt_w > 0 else 0) + 6
        return QSize(w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        sw_w, sw_h = 34.0, 18.0
        y_top = (self.height() - sw_h) / 2.0
        track_rect = QRectF(1.0, y_top, sw_w, sw_h)

        off_bg = blend_colors(THEME["bg_input"], THEME["bg_hover"], self._hover_level * 0.7)
        on_bg = blend_colors(THEME["bg_accent"], THEME["bg_accent_hover"], self._hover_level * 0.6)
        track_col = blend_colors(off_bg.name(), on_bg.name(), self._thumb_pos)

        border_off = blend_colors(THEME["border"], THEME["border_focus"], self._hover_level * 0.75)
        border_col = blend_colors(border_off.name(), THEME["bg_accent"], self._thumb_pos)

        p.setBrush(track_col)
        p.setPen(QPen(border_col, 1.1))
        p.drawRoundedRect(track_rect, sw_h / 2.0, sw_h / 2.0)

        pad = 2.5
        d = sw_h - pad * 2.0
        x_min = track_rect.left() + pad
        x_max = track_rect.right() - pad - d
        cx = x_min + (x_max - x_min) * self._thumb_pos
        thumb_rect = QRectF(cx, y_top + pad, d, d)

        thumb_off = QColor(THEME["text_muted"]) if self._hover_level < 0.5 else QColor(THEME["text_main"])
        thumb_col = blend_colors(thumb_off.name(), "#ffffff", self._thumb_pos)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(thumb_col)
        p.drawEllipse(thumb_rect)

        if self.text():
            txt_col = blend_colors(THEME["text_main"], THEME["border_focus"], self._hover_level * 0.25)
            p.setPen(txt_col)
            p.setFont(self.font())
            txt_rect = QRectF(sw_w + 9.0, 0.0, self.width() - sw_w - 9.0, float(self.height()))
            p.drawText(txt_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())

        p.end()


class AnimatedPillButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active_val = 0.0
        self._hover_val = 0.0
        self._is_active = False

        self._anim_act = QVariantAnimation(self)
        self._anim_act.setDuration(180)
        self._anim_act.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_act.valueChanged.connect(self._on_act_changed)

        self._anim_hov = QVariantAnimation(self)
        self._anim_hov.setDuration(130)
        self._anim_hov.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_hov.valueChanged.connect(self._on_hov_changed)

    def _on_act_changed(self, v):
        self._active_val = float(v)
        self.update()

    def _on_hov_changed(self, v):
        self._hover_val = float(v)
        self.update()

    def set_active_animated(self, active):
        self._is_active = bool(active)
        self._anim_act.stop()
        self._anim_act.setStartValue(self._active_val)
        self._anim_act.setEndValue(1.0 if active else 0.0)
        self._anim_act.start()

    def sync_active_immediate(self, active):
        self._is_active = bool(active)
        self._active_val = 1.0 if active else 0.0
        self.update()

    def enterEvent(self, event):
        self._anim_hov.stop()
        self._anim_hov.setStartValue(self._hover_val)
        self._anim_hov.setEndValue(1.0)
        self._anim_hov.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim_hov.stop()
        self._anim_hov.setStartValue(self._hover_val)
        self._anim_hov.setEndValue(0.0)
        self._anim_hov.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        bg_idle = blend_colors(THEME["bg_btn"], THEME["bg_btn_hover"], self._hover_val)
        bg_act = blend_colors(THEME["bg_accent"], THEME["bg_accent_hover"], self._hover_val * 0.6)
        bg = blend_colors(bg_idle.name(), bg_act.name(), self._active_val)

        brd_idle = blend_colors(THEME["border"], THEME["border_focus"], self._hover_val)
        brd = blend_colors(brd_idle.name(), THEME["bg_accent"], self._active_val)

        p.setBrush(bg)
        p.setPen(QPen(brd, 1.0))
        p.drawRoundedRect(rect, 6.0, 6.0)

        txt_col = blend_colors(THEME["text_main"], "#ffffff", self._active_val)
        p.setPen(txt_col)
        p.setFont(self.font())

        ico = self.icon()
        if not ico.isNull():
            isz = self.iconSize()
            fm = QFontMetrics(self.font())
            tw = fm.horizontalAdvance(self.text())
            total_w = isz.width() + 5 + tw
            sx = (self.width() - total_w) / 2.0
            iy = (self.height() - isz.height()) / 2.0
            ico.paint(p, int(sx), int(iy), isz.width(), isz.height())
            p.drawText(QRectF(sx + isz.width() + 5, 0, tw + 4, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        else:
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())

        p.end()


def _tint_pixmap(src_pm, color_hex, size):
    dpr = 2
    px = size * dpr
    out = QPixmap(px, px)
    out.setDevicePixelRatio(dpr)
    out.fill(Qt.GlobalColor.transparent)

    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    p.drawPixmap(QRect(0, 0, size, size), src_pm)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(out.rect(), QColor(color_hex))
    p.end()
    return QIcon(out)


def create_vector_qicon(name, color_hex="#f1f5f9", size=20):
    user_file = find_user_asset(name)
    if user_file:
        pm = QPixmap(user_file)
        if not pm.isNull():
            if user_file.lower().endswith(".svg"):
                return _tint_pixmap(pm, color_hex, size)
            return QIcon(pm)

    cdn_svg = os.path.join(UI_ICONS_CACHE_DIR, f"{name}.svg")
    if os.path.isfile(cdn_svg) and os.path.getsize(cdn_svg) > 32:
        pm = QPixmap(cdn_svg)
        if not pm.isNull():
            return _tint_pixmap(pm, color_hex, size)

    dpr = 2
    px = size * dpr
    pm = QPixmap(px, px)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color_hex))
    pen.setWidthF(1.65)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    s = float(size)
    if name == "swap":
        p.drawLine(QPoint(int(s * 0.22), int(s * 0.34)), QPoint(int(s * 0.78), int(s * 0.34)))
        p.drawLine(QPoint(int(s * 0.62), int(s * 0.21)), QPoint(int(s * 0.78), int(s * 0.34)))
        p.drawLine(QPoint(int(s * 0.22), int(s * 0.66)), QPoint(int(s * 0.78), int(s * 0.66)))
        p.drawLine(QPoint(int(s * 0.38), int(s * 0.79)), QPoint(int(s * 0.22), int(s * 0.66)))
    elif name in ("tts_play", "tts_stop"):
        p.drawPolygon([
            QPoint(int(s * 0.16), int(s * 0.39)), QPoint(int(s * 0.33), int(s * 0.39)),
            QPoint(int(s * 0.52), int(s * 0.23)), QPoint(int(s * 0.52), int(s * 0.77)),
            QPoint(int(s * 0.33), int(s * 0.61)), QPoint(int(s * 0.16), int(s * 0.61)),
        ])
    elif name == "play":
        p.drawLine(int(s * 0.38), int(s * 0.24), int(s * 0.68), int(s * 0.50))
        p.drawLine(int(s * 0.68), int(s * 0.50), int(s * 0.38), int(s * 0.76))
    elif name == "stop":
        p.setBrush(QBrush(QColor(color_hex)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(s * 0.27, s * 0.27, s * 0.46, s * 0.46), 3.0, 3.0)
    elif name == "refresh":
        p.drawArc(int(s * 0.20), int(s * 0.20), int(s * 0.60), int(s * 0.60), 35 * 16, 285 * 16)
    elif name == "vram_clean":
        p.drawRect(QRectF(s * 0.26, s * 0.30, s * 0.48, s * 0.52))
    elif name == "model_load":
        cx = int(s * 0.50)
        p.drawLine(cx, int(s * 0.18), cx, int(s * 0.65))
        p.drawLine(int(s * 0.31), int(s * 0.47), cx, int(s * 0.65))
        p.drawLine(int(s * 0.69), int(s * 0.47), cx, int(s * 0.65))
    elif name == "server":
        p.drawRoundedRect(QRectF(s * 0.18, s * 0.21, s * 0.64, s * 0.23), 3.0, 3.0)
        p.drawRoundedRect(QRectF(s * 0.18, s * 0.56, s * 0.64, s * 0.23), 3.0, 3.0)
    elif name == "settings":
        p.drawEllipse(QRectF(s * 0.30, s * 0.30, s * 0.40, s * 0.40))
    elif name == "image":
        p.drawRoundedRect(QRectF(s * 0.16, s * 0.22, s * 0.68, s * 0.56), 3.0, 3.0)
    elif name == "vision":
        p.drawEllipse(QRectF(s * 0.20, s * 0.32, s * 0.60, s * 0.36))
        p.drawEllipse(QRectF(s * 0.40, s * 0.40, s * 0.20, s * 0.20))

    p.end()
    return QIcon(pm)


def _apply_rounded_flag_mask(src_pm, w=22, h=15):
    dpr = 2.0
    pw, ph = int(w * dpr), int(h * dpr)
    out = QPixmap(pw, ph)
    out.setDevicePixelRatio(dpr)
    out.fill(Qt.GlobalColor.transparent)

    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0.0, 0.0, float(w), float(h)), 2.5, 2.5)
    p.setClipPath(clip)
    p.drawPixmap(QRect(0, 0, w, h), src_pm)

    p.setClipping(False)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(255, 255, 255, 50), 1.0))
    p.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), 2.5, 2.5)
    p.end()
    return out


def create_flag_pixmap(iso_code, w=22, h=15):
    user_flag = find_user_asset(os.path.join("flags", iso_code))
    if user_flag:
        raw_pm = QPixmap(user_flag)
        if not raw_pm.isNull():
            return _apply_rounded_flag_mask(raw_pm, w, h)

    if not iso_code.startswith("badge_") and not iso_code.startswith("reg-"):
        for ext in ("png", "svg"):
            cached_file = os.path.join(FLAGS_CACHE_DIR, f"{iso_code}.{ext}")
            if os.path.isfile(cached_file) and os.path.getsize(cached_file) > 64:
                raw_pm = QPixmap(cached_file)
                if not raw_pm.isNull():
                    return _apply_rounded_flag_mask(raw_pm, w, h)

    dpr = 2.0
    pw, ph = int(w * dpr), int(h * dpr)
    pm = QPixmap(pw, ph)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0.0, 0.0, float(w), float(h)), 2.5, 2.5)
    p.setClipPath(clip)

    if iso_code == "badge_ai":
        p.fillRect(0, 0, w, h, QColor("#2e1065"))
        p.setPen(QColor("#e9d5ff"))
        p.setFont(QFont(UI_FONT, 7, QFont.Weight.Bold))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "AI")
        p.setClipping(False)
        p.setPen(QPen(QColor("#a855f7"), 1.0))
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), 2.5, 2.5)
        p.end()
        return pm

    if iso_code == "badge_fast":
        p.fillRect(0, 0, w, h, QColor("#172554"))
        p.setPen(QColor("#bfdbfe"))
        p.setFont(QFont(UI_FONT, 6, QFont.Weight.Bold))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "ABC")
        p.setClipping(False)
        p.setPen(QPen(QColor("#3b82f6"), 1.0))
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), 2.5, 2.5)
        p.end()
        return pm

    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    p.setPen(Qt.PenStyle.NoPen)

    if iso_code == "reg-tt":
        p.fillRect(0, 0, w, 6, QColor("#008000"))
        p.fillRect(0, 6, w, 3, QColor("#ffffff"))
        p.fillRect(0, 9, w, h - 9, QColor("#cc0000"))
    elif iso_code == "reg-ba":
        p.fillRect(0, 0, w, 5, QColor("#0072ce"))
        p.fillRect(0, 5, w, 5, QColor("#ffffff"))
        p.fillRect(0, 10, w, h - 10, QColor("#009639"))
        p.setBrush(QColor("#ffcc00"))
        p.drawEllipse(w // 2 - 2, 5, 4, 4)
    elif iso_code == "reg-cv":
        p.fillRect(0, 0, w, h, QColor("#ffdf00"))
        p.fillRect(0, 10, w, h - 10, QColor("#a50021"))
        p.setBrush(QColor("#a50021"))
        p.drawPolygon([QPoint(w // 2, 3), QPoint(w // 2 + 4, 9), QPoint(w // 2 - 4, 9)])
    elif iso_code == "reg-ce":
        p.fillRect(0, 0, w, 8, QColor("#008000"))
        p.fillRect(0, 8, w, 2, QColor("#ffffff"))
        p.fillRect(0, 10, w, h - 10, QColor("#cc0000"))
        p.fillRect(0, 0, 3, h, QColor("#ffffff"))
    elif iso_code == "reg-os":
        p.fillRect(0, 0, w, 5, QColor("#ffffff"))
        p.fillRect(0, 5, w, 5, QColor("#ff0000"))
        p.fillRect(0, 10, w, h - 10, QColor("#ffdf00"))
    elif iso_code == "reg-sah":
        p.fillRect(0, 0, w, 10, QColor("#00a3e0"))
        p.fillRect(0, 10, w, 2, QColor("#ffffff"))
        p.fillRect(0, 12, w, 1, QColor("#cc0000"))
        p.fillRect(0, 13, w, h - 13, QColor("#008000"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(w // 2 - 3, 2, 6, 6)
    elif iso_code == "reg-bua":
        p.fillRect(0, 0, w, 7, QColor("#005bbb"))
        p.fillRect(0, 7, w, 4, QColor("#ffffff"))
        p.fillRect(0, 11, w, h - 11, QColor("#ffd500"))
    elif iso_code == "reg-udm":
        p.fillRect(0, 0, 7, h, QColor("#000000"))
        p.fillRect(7, 0, 8, h, QColor("#ffffff"))
        p.fillRect(15, 0, w - 15, h, QColor("#cc0000"))
        p.fillRect(w // 2 - 1, 4, 2, 7, QColor("#cc0000"))
        p.fillRect(w // 2 - 3, 6, 6, 2, QColor("#cc0000"))
    elif iso_code == "reg-kv":
        p.fillRect(0, 0, w, 5, QColor("#0039a6"))
        p.fillRect(0, 5, w, 5, QColor("#009639"))
        p.fillRect(0, 10, w, h - 10, QColor("#ffffff"))
    elif iso_code == "reg-chm":
        p.fillRect(0, 0, w, 5, QColor("#0039a6"))
        p.fillRect(0, 5, w, 5, QColor("#ffffff"))
        p.fillRect(0, 10, w, h - 10, QColor("#cc0000"))
    elif iso_code == "reg-myv":
        p.fillRect(0, 0, w, 5, QColor("#cc0000"))
        p.fillRect(0, 5, w, 5, QColor("#ffffff"))
        p.fillRect(0, 10, w, h - 10, QColor("#0039a6"))
    elif iso_code == "reg-ca":
        p.fillRect(0, 0, w, h, QColor("#fcdd09"))
        for y in (2, 5, 8, 11):
            p.fillRect(0, y, w, 2, QColor("#da121a"))
    elif iso_code == "reg-eu":
        p.fillRect(0, 0, w, h, QColor("#d52b1e"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor("#009b48"), 2.2))
        p.drawLine(0, 0, w, h)
        p.drawLine(0, h, w, 0)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.fillRect(0, h // 2 - 1, w, 3, QColor("#ffffff"))
        p.fillRect(w // 2 - 1, 0, 3, h, QColor("#ffffff"))
    elif iso_code == "reg-gl":
        p.fillRect(0, 0, w, h, QColor("#ffffff"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor("#0099cc"), 2.6))
        p.drawLine(0, 0, w, h)
    elif iso_code == "gb-sct":
        p.fillRect(0, 0, w, h, QColor("#005eb8"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor("#ffffff"), 2.4))
        p.drawLine(0, 0, w, h)
        p.drawLine(0, h, w, 0)
    elif iso_code == "gb-wls":
        p.fillRect(0, 0, w, h // 2, QColor("#ffffff"))
        p.fillRect(0, h // 2, w, h - h // 2, QColor("#00ab39"))
        p.setBrush(QColor("#d30731"))
        p.drawEllipse(w // 2 - 4, h // 2 - 3, 8, 6)
    elif iso_code == "reg-ku":
        p.fillRect(0, 0, w, 5, QColor("#ed2939"))
        p.fillRect(0, 5, w, 5, QColor("#ffffff"))
        p.fillRect(0, 10, w, h - 10, QColor("#278e43"))
        p.setBrush(QColor("#febd11"))
        p.drawEllipse(w // 2 - 3, h // 2 - 3, 6, 6)
    elif iso_code == "reg-eo":
        p.fillRect(0, 0, w, h, QColor("#009900"))
        p.fillRect(0, 0, 8, 8, QColor("#ffffff"))
        p.setBrush(QColor("#009900"))
        p.drawEllipse(2, 2, 4, 4)
    elif iso_code in ("reg-pa", "reg-ta", "reg-te", "reg-mr", "reg-gu", "reg-kn", "reg-ml", "reg-sa"):
        accents = {
            "reg-pa": "#1d4ed8", "reg-ta": "#dc2626", "reg-te": "#7c3aed",
            "reg-mr": "#d97706", "reg-gu": "#059669", "reg-kn": "#b91c1c",
            "reg-ml": "#0284c7", "reg-sa": "#9333ea"
        }
        p.fillRect(0, 0, w, 5, QColor("#ff9933"))
        p.fillRect(0, 5, w, 5, QColor("#ffffff"))
        p.fillRect(0, 10, w, h - 10, QColor("#138808"))
        p.setBrush(QColor(accents[iso_code]))
        p.drawEllipse(w // 2 - 2, 5, 5, 5)
    else:
        horiz_3 = {
            "ru": ("#ffffff", "#0039a6", "#d52b1e"),
            "de": ("#000000", "#dd0000", "#ffce00"),
            "nl": ("#ae1c28", "#ffffff", "#21468b"),
            "bg": ("#ffffff", "#00966e", "#d62612"),
            "hu": ("#ce2939", "#ffffff", "#477050"),
            "lt": ("#fdb913", "#006a44", "#c1272d"),
            "ee": ("#0072ce", "#000000", "#ffffff"),
            "am": ("#d90012", "#0033a0", "#f2a800"),
            "az": ("#00b5e2", "#ef3340", "#509e2f"),
            "rs": ("#c6363c", "#0c4076", "#ffffff"),
            "hr": ("#ff0000", "#ffffff", "#171796"),
            "si": ("#ffffff", "#005ce6", "#ff0000"),
            "sk": ("#ffffff", "#0b4ea2", "#ee1c25"),
            "lu": ("#ed2939", "#ffffff", "#00a1de"),
            "in": ("#ff9933", "#ffffff", "#138808"),
            "ir": ("#239f40", "#ffffff", "#da0000"),
            "tj": ("#cc0000", "#ffffff", "#006600"),
            "uz": ("#0099b5", "#ffffff", "#1eb53a"),
            "et": ("#078930", "#fcdd09", "#da121a"),
            "ke": ("#000000", "#bb0000", "#006600"),
        }
        vert_3 = {
            "fr": ("#002395", "#ffffff", "#ed2939"),
            "it": ("#009246", "#ffffff", "#ce2b37"),
            "ro": ("#002b7f", "#fcd116", "#ce1126"),
            "ie": ("#169b62", "#ffffff", "#ff883e"),
            "ng": ("#008751", "#ffffff", "#008751"),
            "mn": ("#c4272f", "#015197", "#c4272f"),
            "pe": ("#d91023", "#ffffff", "#d91023"),
            "ne": ("#e05206", "#ffffff", "#0db02b"),
        }
        horiz_2 = {
            "ua": ("#0057b7", "#ffd700"),
            "pl": ("#ffffff", "#dc143c"),
            "id": ("#ff0000", "#ffffff"),
            "ht": ("#00209f", "#d21034"),
        }

        if iso_code in horiz_3:
            c1, c2, c3 = horiz_3[iso_code]
            h1, h2 = h // 3, (2 * h) // 3
            p.fillRect(0, 0, w, h1, QColor(c1))
            p.fillRect(0, h1, w, h2 - h1, QColor(c2))
            p.fillRect(0, h2, w, h - h2, QColor(c3))
        elif iso_code in vert_3:
            c1, c2, c3 = vert_3[iso_code]
            w1, w2 = w // 3, (2 * w) // 3
            p.fillRect(0, 0, w1, h, QColor(c1))
            p.fillRect(w1, 0, w2 - w1, h, QColor(c2))
            p.fillRect(w2, 0, w - w2, h, QColor(c3))
        elif iso_code in horiz_2:
            c1, c2 = horiz_2[iso_code]
            h1 = h // 2
            p.fillRect(0, 0, w, h1, QColor(c1))
            p.fillRect(0, h1, w, h - h1, QColor(c2))
        elif iso_code == "gb":
            p.fillRect(0, 0, w, h, QColor("#012169"))
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setPen(QPen(QColor("#ffffff"), 2.4))
            p.drawLine(0, 0, w, h)
            p.drawLine(0, h, w, 0)
            p.setPen(QPen(QColor("#c8102e"), 1.1))
            p.drawLine(0, 0, w, h)
            p.drawLine(0, h, w, 0)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            p.fillRect(0, h // 2 - 2, w, 4, QColor("#ffffff"))
            p.fillRect(w // 2 - 2, 0, 4, h, QColor("#ffffff"))
            p.fillRect(0, h // 2 - 1, w, 2, QColor("#c8102e"))
            p.fillRect(w // 2 - 1, 0, 2, h, QColor("#c8102e"))
        elif iso_code == "es":
            p.fillRect(0, 0, w, h, QColor("#aa151b"))
            p.fillRect(0, h // 4, w, h // 2, QColor("#f1bf00"))
        elif iso_code == "pt":
            w1 = (2 * w) // 5
            p.fillRect(0, 0, w1, h, QColor("#006600"))
            p.fillRect(w1, 0, w - w1, h, QColor("#ff0000"))
            p.setBrush(QColor("#ffcc00"))
            p.drawEllipse(w1 - 3, h // 2 - 3, 6, 6)
        elif iso_code == "jp":
            p.fillRect(0, 0, w, h, QColor("#ffffff"))
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setBrush(QColor("#bc002d"))
            p.drawEllipse(w // 2 - 4, h // 2 - 4, 8, 8)
        elif iso_code in ("cn", "vn"):
            p.fillRect(0, 0, w, h, QColor("#de2910"))
            p.setBrush(QColor("#ffde00"))
            p.drawEllipse(3, 3, 5, 5)
        elif iso_code == "tw":
            p.fillRect(0, 0, w, h, QColor("#fe0000"))
            p.fillRect(0, 0, w // 2, h // 2, QColor("#000095"))
            p.setBrush(QColor("#ffffff"))
            p.drawEllipse(w // 4 - 2, h // 4 - 2, 4, 4)
        elif iso_code == "kr":
            p.fillRect(0, 0, w, h, QColor("#ffffff"))
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setBrush(QColor("#cd2e3a"))
            p.drawEllipse(w // 2 - 4, h // 2 - 4, 8, 8)
        elif iso_code == "by":
            h1 = (2 * h) // 3
            p.fillRect(0, 0, w, h1, QColor("#c8313e"))
            p.fillRect(0, h1, w, h - h1, QColor("#4aa657"))
            p.fillRect(0, 0, 3, h, QColor("#ffffff"))
        elif iso_code == "kz":
            p.fillRect(0, 0, w, h, QColor("#00afca"))
            p.setBrush(QColor("#fec50c"))
            p.drawEllipse(w // 2 - 3, h // 2 - 3, 6, 6)
        elif iso_code in ("se", "fi", "no", "dk", "is"):
            cross_pal = {
                "se": ("#006aa7", "#fecc02"),
                "fi": ("#ffffff", "#003580"),
                "no": ("#ba0c2f", "#00205b"),
                "dk": ("#c8102e", "#ffffff"),
                "is": ("#02529c", "#dc1e35"),
            }
            bg_c, cr_c = cross_pal[iso_code]
            p.fillRect(0, 0, w, h, QColor(bg_c))
            p.fillRect(w // 3 - 1, 0, 3, h, QColor(cr_c))
            p.fillRect(0, h // 2 - 1, w, 3, QColor(cr_c))
        else:
            h_val = sum((idx + 1) * ord(ch) for idx, ch in enumerate(iso_code))
            pal = ["#1d4ed8", "#047857", "#b91c1c", "#7e22ce", "#0f766e", "#b45309", "#0284c7", "#be123c", "#15803d", "#4338ca"]
            c1 = pal[h_val % len(pal)]
            c2 = "#ffffff" if (h_val % 2 == 0) else "#facc15"
            c3 = pal[(h_val * 3 + 2) % len(pal)]
            p.fillRect(0, 0, w, 5, QColor(c1))
            p.fillRect(0, 5, w, 5, QColor(c2))
            p.fillRect(0, 10, w, h - 10, QColor(c3))

    p.setClipping(False)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(255, 255, 255, 50), 1.0))
    p.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), 2.5, 2.5)
    p.end()
    return pm


def _fetch_first_working_url(urls, timeout=3.5):
    for u in urls:
        try:
            req = urllib.request.Request(
                u,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "*/*"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if data and len(data) > 64:
                return data
        except Exception:
            continue
    return None


def smart_filter_items(query, items, aliases_dict):
    q = query.strip().lower()
    if not q:
        return items

    q_layout = q.translate(LAYOUT_RU_TO_EN)
    q_variants = {q, q_layout}
    for ru_k, en_v in PHONETIC_RU_TO_EN.items():
        if ru_k in q:
            q_variants.add(q.replace(ru_k, en_v))

    scored = []
    for item in items:
        clean_item = strip_flag_prefix(strip_loaded_prefix(item))
        item_low = clean_item.lower()
        alias_low = aliases_dict.get(clean_item, aliases_dict.get(strip_loaded_prefix(item), "")).lower()
        target_pool = f"{item_low} {alias_low}".strip()

        best_score = 0.0
        for qv in q_variants:
            if qv in item_low:
                best_score = max(best_score, 1.0 if item_low.startswith(qv) else 0.92)
            elif qv in alias_low:
                best_score = max(best_score, 0.88)
            else:
                for token in target_pool.split():
                    ratio = difflib.SequenceMatcher(None, qv, token).ratio()
                    if token.startswith(qv[:2]):
                        ratio += 0.12
                    best_score = max(best_score, ratio)

        if best_score >= 0.52:
            scored.append((best_score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored]


class MarkdownInputHighlighter(QSyntaxHighlighter):
    def __init__(self, parent_doc):
        super().__init__(parent_doc)

    def highlightBlock(self, text):
        if not text:
            return
        fmt_bold = QTextCharFormat()
        fmt_bold.setFontWeight(QFont.Weight.Bold)
        fmt_bold.setForeground(QColor(THEME["text_main"]))

        fmt_italic = QTextCharFormat()
        fmt_italic.setFontItalic(True)
        fmt_italic.setForeground(QColor(THEME["text_main"]))

        fmt_code = QTextCharFormat()
        fmt_code.setFontFamilies([MONO_FONT])
        fmt_code.setBackground(QColor(THEME["code_bg"]))
        fmt_code.setForeground(QColor(THEME["code_fg"]))

        fmt_hdr = QTextCharFormat()
        fmt_hdr.setFontWeight(QFont.Weight.Bold)
        fmt_hdr.setForeground(QColor(THEME["border_focus"]))

        fmt_quote = QTextCharFormat()
        fmt_quote.setFontItalic(True)
        fmt_quote.setForeground(QColor(THEME["text_muted"]))

        fmt_dim = QTextCharFormat()
        fmt_dim.setForeground(QColor(THEME["text_dim"]))

        if re.match(r"^#{1,3}\s+", text):
            self.setFormat(0, len(text), fmt_hdr)
            return
        if re.match(r"^>\s+", text):
            self.setFormat(0, len(text), fmt_quote)
            return

        for m in RE_MD_TOKEN.finditer(text):
            st, en = m.span()
            tok = m.group(0)
            if tok.startswith("`"):
                self.setFormat(st, en - st, fmt_code)
            elif tok.startswith("**") or tok.startswith("__"):
                self.setFormat(st, 2, fmt_dim)
                self.setFormat(st + 2, en - st - 4, fmt_bold)
                self.setFormat(en - 2, 2, fmt_dim)
            elif tok.startswith("*") or tok.startswith("_"):
                self.setFormat(st, 1, fmt_dim)
                self.setFormat(st + 1, en - st - 2, fmt_italic)
                self.setFormat(en - 1, 1, fmt_dim)


class SearchableSelector(QFrame):
    selectionChanged = Signal(str)

    def __init__(
        self, root_window, values, default_value,
        aliases=None, prefer_upwards=False, height=32,
        allow_custom=True, editable=True, font_size=12, icon_provider=None,
        min_popup_width=190
    ):
        super().__init__(root_window)
        self.root = root_window
        self.values = list(values)
        self.aliases = aliases or {}
        self.current_val = default_value
        self.prefer_upwards = prefer_upwards
        self.allow_custom = allow_custom
        self.editable = editable
        self.font_size = font_size
        self.icon_provider = icon_provider
        self.min_popup_width = min_popup_width
        self._is_editing = False
        self._icon_size = QSize(22, 15)

        self.setFixedHeight(height)
        self.setObjectName("SelectorBox")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(6)

        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(22, 16)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.icon_provider is None:
            self.lbl_icon.hide()
        layout.addWidget(self.lbl_icon)

        self.edit = QLineEdit()
        self.edit.setFrame(False)
        self.edit.setReadOnly(not self.editable)
        self.edit.setFont(QFont(UI_FONT, self.font_size, QFont.Weight.DemiBold))
        self.edit.setText(default_value)
        self.edit.setCursorPosition(0)
        self.edit.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.edit, 1)

        self.btn_arrow = QPushButton("▾")
        self.btn_arrow.setFixedSize(24, height - 4)
        self.btn_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_arrow.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_arrow.clicked.connect(self._toggle_popup)
        layout.addWidget(self.btn_arrow)

        self.popup = QFrame(self.root)
        self.popup.setObjectName("SelectorPopup")
        self.popup.hide()

        self._anim_geom = QPropertyAnimation(self.popup, b"geometry", self)
        self._anim_geom.setDuration(145)
        self._anim_geom.setEasingCurve(QEasingCurve.Type.OutCubic)

        pop_lay = QVBoxLayout(self.popup)
        pop_lay.setContentsMargins(1, 1, 1, 1)
        pop_lay.setSpacing(0)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(self._icon_size)
        self.list_widget.setSpacing(1)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        self.list_widget.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        pop_lay.addWidget(self.list_widget)

        if self.editable:
            self.edit.textEdited.connect(self._on_text_edited)
            self.edit.returnPressed.connect(self._on_enter)

        self.installEventFilter(self)
        self.lbl_icon.installEventFilter(self)
        self.edit.installEventFilter(self)
        self._update_icon()

    def apply_scale(self, scale_factor, base_h, base_font, base_min_popup=190):
        h = max(24, int(round(base_h * scale_factor)))
        fs = max(8, int(round(base_font * scale_factor)))
        iw = max(16, int(round(22 * scale_factor)))
        ih = max(11, int(round(15 * scale_factor)))
        self._icon_size = QSize(iw, ih)
        self.min_popup_width = max(72, int(round(base_min_popup * scale_factor)))
        self.setFixedHeight(h)
        self.lbl_icon.setFixedSize(iw, ih + 1)
        self.edit.setFont(QFont(UI_FONT, fs, QFont.Weight.DemiBold))
        self.btn_arrow.setFixedSize(max(20, int(round(24 * scale_factor))), max(20, h - 4))
        self.list_widget.setIconSize(self._icon_size)
        self.list_widget.setFont(QFont(UI_FONT, max(8, fs - 1)))
        self._update_icon()

    def eventFilter(self, obj, event):
        if not hasattr(self, "edit"):
            return super().eventFilter(obj, event)
        if obj in (self, self.lbl_icon, self.edit):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                if not self.popup.isVisible():
                    self._start_editing_and_open()
                elif not self.editable:
                    self.close_popup()
                return (obj is not self.edit) or (not self.editable)
            elif obj is self.edit and event.type() == QEvent.Type.KeyPress:
                if not self._is_editing or not self.popup.isVisible():
                    return False
                key = event.key()
                if key == Qt.Key.Key_Down:
                    row = min(self.list_widget.count() - 1, self.list_widget.currentRow() + 1)
                    self.list_widget.setCurrentRow(row)
                    return True
                elif key == Qt.Key.Key_Up:
                    row = max(0, self.list_widget.currentRow() - 1)
                    self.list_widget.setCurrentRow(row)
                    return True
                elif key == Qt.Key.Key_Escape:
                    self.close_popup()
                    return True
            elif obj is self.edit and event.type() == QEvent.Type.FocusOut:
                if self.popup.isVisible():
                    self.close_popup()
        return super().eventFilter(obj, event)

    def _update_icon(self):
        if self.icon_provider is None:
            return
        if self._is_editing and self.editable:
            self.lbl_icon.hide()
            return
        ico = self.icon_provider(self.current_val)
        if ico is not None and not ico.isNull():
            self.lbl_icon.setPixmap(ico.pixmap(self._icon_size))
            self.lbl_icon.show()
        else:
            self.lbl_icon.hide()

    def _start_editing_and_open(self):
        if hasattr(self.root, "_close_all_popups"):
            self.root._close_all_popups(except_widget=self)
        self._is_editing = True
        self._update_icon()
        self.setProperty("focused", True)
        self.style().unpolish(self)
        self.style().polish(self)
        if self.editable:
            self.edit.setCursor(Qt.CursorShape.IBeamCursor)
            self.edit.clear()
        self.open_popup(self.values, animate=True)
        self.edit.setFocus()

    def _toggle_popup(self):
        if self.popup.isVisible():
            self.close_popup()
        else:
            self._start_editing_and_open()

    def _on_text_edited(self, text):
        if not self.edit.hasFocus() or not self._is_editing:
            return
        q = text.strip().lower()
        if not q:
            matches = self.values
        elif getattr(self.root, "use_smart_search", False):
            matches = smart_filter_items(q, self.values, self.aliases)
        else:
            matches = [
                item for item in self.values
                if q in item.lower()
                or q in self.aliases.get(strip_flag_prefix(strip_loaded_prefix(item)), "")
                or q in self.aliases.get(strip_loaded_prefix(item), "")
            ]
        self.open_popup(matches, animate=False)

    def _on_enter(self):
        if not self._is_editing:
            return
        typed = self.edit.text().strip()
        if self.popup.isVisible() and self.list_widget.count() > 0:
            cur_item = self.list_widget.currentItem()
            if cur_item and cur_item.data(Qt.ItemDataRole.UserRole) is not None:
                self.select(cur_item.data(Qt.ItemDataRole.UserRole))
                return
        if self.allow_custom and typed:
            self.select(typed, is_custom=True)
        else:
            self.select(self.current_val)

    def _on_item_clicked(self, item):
        val = item.data(Qt.ItemDataRole.UserRole)
        if val is not None:
            self.select(val)

    def _compute_target_geometry(self):
        top_left = self.mapTo(self.root, QPoint(0, 0))
        box_w = self.width()
        if not self.allow_custom and self.editable and self.parentWidget() is not None:
            box_w = max(box_w, self.parentWidget().width())
        box_w = max(box_w, self.min_popup_width)
        if top_left.x() + box_w > self.root.width() - 8:
            box_w = max(90, self.root.width() - top_left.x() - 8)

        row_h = max(24, self._icon_size.height() + 12)
        count = max(1, self.list_widget.count())
        desired_h = min(count * row_h + 6, 260)
        gap = 4

        space_below = self.root.height() - (top_left.y() + self.height()) - 8
        space_above = top_left.y() - 8

        if (self.prefer_upwards and space_above >= 100) or (space_below < 120 and space_above > space_below):
            h = min(desired_h, max(64, space_above - gap))
            y = top_left.y() - h - gap
            upwards = True
        else:
            h = min(desired_h, max(64, space_below - gap))
            y = top_left.y() + self.height() + gap
            upwards = False

        return QRect(top_left.x(), y, box_w, h), upwards

    def open_popup(self, items, animate=True):
        self.list_widget.clear()
        row_h = max(24, self._icon_size.height() + 12)
        if not items:
            hint = self.root._tr("custom_lang_hint") if self.allow_custom else self.root._tr("no_matches")
            it = QListWidgetItem(hint)
            it.setData(Qt.ItemDataRole.UserRole, None)
            it.setFlags(Qt.ItemFlag.NoItemFlags)
            it.setSizeHint(QSize(0, row_h))
            self.list_widget.addItem(it)
        else:
            cur_clean = strip_flag_prefix(strip_loaded_prefix(self.current_val))
            sel_row = 0
            for idx, val in enumerate(items):
                it = QListWidgetItem(val)
                it.setData(Qt.ItemDataRole.UserRole, val)
                it.setToolTip(val)
                it.setSizeHint(QSize(0, row_h))
                if self.icon_provider is not None:
                    ico = self.icon_provider(val)
                    if ico is not None:
                        it.setIcon(ico)
                self.list_widget.addItem(it)
                if strip_flag_prefix(strip_loaded_prefix(val)) == cur_clean:
                    sel_row = idx
            self.list_widget.setCurrentRow(sel_row)

        target_rect, upwards = self._compute_target_geometry()
        self._anim_geom.stop()

        if animate and not self.popup.isVisible():
            start_h = max(14, int(target_rect.height() * 0.25))
            start_y = (target_rect.bottom() - start_h) if upwards else target_rect.top()
            start_rect = QRect(target_rect.x(), start_y, target_rect.width(), start_h)

            self.popup.setGeometry(start_rect)
            self.popup.show()
            self.popup.raise_()

            self._anim_geom.setStartValue(start_rect)
            self._anim_geom.setEndValue(target_rect)
            self._anim_geom.start()
        else:
            self.popup.setGeometry(target_rect)
            self.popup.show()
            self.popup.raise_()

    def sync_position(self):
        if not self.isVisible() or not self.popup.isVisible():
            return
        target_rect, _ = self._compute_target_geometry()
        self.popup.setGeometry(target_rect)

    def select(self, val, is_custom=False):
        if val in self.values or is_custom:
            self.current_val = val
            if is_custom and val not in self.values:
                self.values.append(val)
        self._finish_editing_state()
        self._anim_geom.stop()
        self.popup.hide()
        self._update_icon()
        self.edit.setText(self.current_val)
        self.edit.setCursorPosition(0)
        self.edit.setToolTip(self.current_val)
        self.edit.clearFocus()
        self.selectionChanged.emit(self.current_val)

    def close_popup(self):
        self._finish_editing_state()
        self._anim_geom.stop()
        self.popup.hide()
        self._update_icon()
        self.edit.setText(self.current_val)
        self.edit.setCursorPosition(0)
        self.edit.setToolTip(self.current_val)
        self.edit.clearFocus()

    def _finish_editing_state(self):
        self._is_editing = False
        self.edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("focused", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def configure_values(self, new_values):
        self.values = list(new_values)

    def get(self):
        return self.current_val

    def set(self, val):
        self.current_val = val
        self._finish_editing_state()
        self._update_icon()
        self.edit.setText(val)
        self.edit.setCursorPosition(0)
        self.edit.setToolTip(val)


class InputTextEdit(QPlainTextEdit):
    submitRequested = Signal()
    imagePasted = Signal(object)

    def keyPressEvent(self, event):
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submitRequested.emit()
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasImage():
            qimg = source.imageData()
            if isinstance(qimg, QImage) and not qimg.isNull():
                self.imagePasted.emit(qimg)
                return
        if source.hasUrls():
            for url in source.urls():
                local = url.toLocalFile()
                if local and os.path.isfile(local) and local.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
                    qimg = QImage(local)
                    if not qimg.isNull():
                        self.imagePasted.emit(qimg)
                        return
        super().insertFromMimeData(source)


class UISignals(QObject):
    statusAnimStart = Signal(str, str)
    statusAnimPhase = Signal(str, str)
    statusAnimStop = Signal(str, str, float)
    modelsUpdated = Signal(list, bool, bool)
    refreshModelLabels = Signal()
    detectedLangUpdated = Signal(str)
    mismatchBannerShown = Signal(int, str)
    typewriterUpdated = Signal(int, str, bool, str, str, float, bool, str, str)
    renderDirectOutput = Signal(str)
    resetGenerationButtons = Signal()
    ttsFinished = Signal()
    flagDownloaded = Signal(str)
    uiIconsDownloaded = Signal()


class LLMTranslateWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui_lang, self.theme_mode, self.ui_scale = self._peek_initial_prefs()
        THEME.update(THEME_PALETTES.get(self.theme_mode, THEME_PALETTES["dark"]))

        self.sig = UISignals()
        self._connect_signals()

        self.setWindowTitle("LLM TRANSLATE")
        self._apply_app_icon()

        self.flag_pixmaps = {}
        for code in sorted(set(LANG_ISO_MAP.values())):
            self.flag_pixmaps[code] = create_flag_pixmap(code)

        self.client = OpenAI(base_url=f"http://{LM_HOST}:{LM_PORT}/v1", api_key="lm-studio", timeout=30.0)
        self.model_id = self._tr("select_model")
        self._saved_config_model = self._tr("select_model")
        self._available_models = []
        self._model_meta = {}
        self._loaded_vram_models = set()
        self._is_online = False
        self._server_booting = False
        self._is_loading_model = False
        self.use_smart_search = False
        self.enable_thinking = False
        self.vision_model_id = ""
        self._attached_image_b64 = ""
        self._attached_image_name = ""
        self.pin_window = False

        self._tts_proc = None
        self._tts_lock = threading.Lock()
        self._tts_stop_event = threading.Event()
        self._is_speaking = False

        self.auto_detect_mode = "ai"
        self.detected_src_lang = None

        self._task_id = 0
        self._model_switch_id = 0
        self._active_stream = None
        self._stream_lock = threading.Lock()
        self._last_edit_time = 0.0
        self._last_translated_state = ("", "", "", "")

        self._anim_running = False
        self._anim_phase_text = ""
        self._anim_color = "#eab308"
        self._anim_start_ts = 0.0
        self._anim_step = 0
        self._raw_status_text = self._tr("connecting")
        self._raw_status_color = THEME["text_muted"]

        self._tw_task_id = -1
        self._tw_target_text = ""
        self._tw_main_target = ""
        self._tw_dict_sections = []
        self._tw_displayed_chars = 0.0
        self._tw_is_dict_mode = False
        self._tw_word = ""
        self._tw_mismatch_warning = ""
        self._tw_mismatch_langs = None
        self._tw_tok_speed = 25.0
        self._tw_stream_finished = False
        self._tw_final_status_msg = ""
        self._tw_final_status_color = "#22c55e"
        self._tw_running = False
        self._dict_dots_step = 0
        self._last_clean_translation = ""

        self._build_ui()
        self._load_config()
        self.apply_scale(self.ui_scale, save=False, resize_window=True)
        self._update_swap_button_state()
        self._sync_vram_button_visibility()

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_status_anim)
        self._anim_timer.start(80)

        self._tw_timer = QTimer(self)
        self._tw_timer.timeout.connect(self._typewriter_tick)
        self._tw_timer.start(25)

        self._watcher_timer = QTimer(self)
        self._watcher_timer.timeout.connect(self._realtime_watcher)
        self._watcher_timer.start(120)

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.timeout.connect(self._auto_reconnect_loop)
        self._reconnect_timer.start(5000)

        QApplication.instance().installEventFilter(self)
        self._start_background_cdn_assets_sync()
        self.fetch_models(auto_start_server=True)

    @staticmethod
    def _set_btn_enabled_with_cursor(btn, enabled):
        btn.setEnabled(enabled)
        btn.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)

    def _connect_signals(self):
        self.sig.statusAnimStart.connect(self._start_status_anim)
        self.sig.statusAnimPhase.connect(self._update_status_anim_phase)
        self.sig.statusAnimStop.connect(self._stop_status_anim)
        self.sig.modelsUpdated.connect(self._update_models_ui)
        self.sig.refreshModelLabels.connect(self._refresh_model_dropdown_labels)
        self.sig.detectedLangUpdated.connect(self._apply_detected_language_ui)
        self.sig.mismatchBannerShown.connect(self._show_instant_mismatch_banner)
        self.sig.typewriterUpdated.connect(self._start_or_update_typewriter)
        self.sig.renderDirectOutput.connect(self._render_direct_text)
        self.sig.resetGenerationButtons.connect(self._reset_gen_buttons)
        self.sig.ttsFinished.connect(self._reset_tts_ui_after_finish)
        self.sig.flagDownloaded.connect(self._on_cdn_flag_ready)
        self.sig.uiIconsDownloaded.connect(self._on_cdn_ui_icons_ready)

    def _start_background_cdn_assets_sync(self):
        def worker():
            downloaded_ui = False
            for local_name, lucide_slug in CDN_UI_ICON_NAMES.items():
                if find_user_asset(local_name):
                    continue
                dest = os.path.join(UI_ICONS_CACHE_DIR, f"{local_name}.svg")
                if os.path.isfile(dest) and os.path.getsize(dest) > 32:
                    continue
                urls = [
                    f"https://unpkg.com/lucide-static@latest/icons/{lucide_slug}.svg",
                    f"https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{lucide_slug}.svg",
                    f"https://api.iconify.design/lucide/{lucide_slug}.svg?width=24&height=24",
                ]
                raw = _fetch_first_working_url(urls, timeout=3.5)
                if raw and b"<svg" in raw:
                    try:
                        with open(dest, "wb") as f:
                            f.write(raw)
                        downloaded_ui = True
                    except Exception:
                        pass
            if downloaded_ui:
                self.sig.uiIconsDownloaded.emit()

            codes = sorted({
                c for c in set(LANG_ISO_MAP.values())
                if not c.startswith("badge_") and not c.startswith("reg-")
            })
            for code in codes:
                if find_user_asset(os.path.join("flags", code)):
                    continue
                dest_png = os.path.join(FLAGS_CACHE_DIR, f"{code}.png")
                dest_svg = os.path.join(FLAGS_CACHE_DIR, f"{code}.svg")
                if (os.path.isfile(dest_png) and os.path.getsize(dest_png) > 64) or (
                    os.path.isfile(dest_svg) and os.path.getsize(dest_svg) > 64
                ):
                    continue

                c_low = code.lower()
                raw_png = _fetch_first_working_url([f"https://flagcdn.com/w40/{c_low}.png"], timeout=2.5)
                if raw_png and raw_png.startswith(b"\x89PNG"):
                    try:
                        with open(dest_png, "wb") as f:
                            f.write(raw_png)
                        self.sig.flagDownloaded.emit(code)
                        continue
                    except Exception:
                        pass

                raw_svg = _fetch_first_working_url([
                    f"https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/4x3/{c_low}.svg",
                    f"https://unpkg.com/flag-icons@7.2.3/flags/4x3/{c_low}.svg",
                ], timeout=3.0)
                if raw_svg and b"<svg" in raw_svg:
                    try:
                        with open(dest_svg, "wb") as f:
                            f.write(raw_svg)
                        self.sig.flagDownloaded.emit(code)
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    def _on_cdn_flag_ready(self, iso_code):
        self.flag_pixmaps[iso_code] = create_flag_pixmap(iso_code)
        self.dd_src._update_icon()
        self.dd_tgt._update_icon()

    def _on_cdn_ui_icons_ready(self):
        self._refresh_button_icons()
        self._refresh_model_dropdown_labels()

    def _apply_app_icon(self):
        for name in ("logo.ico", "logo.png", os.path.join("icons", "logo.ico"), os.path.join("icons", "logo.png")):
            p = resource_path(name)
            if os.path.isfile(p):
                self.setWindowIcon(QIcon(p))
                break

    def _peek_initial_prefs(self):
        lang, theme, scale = "ru", "dark", 100
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("ui_lang") in ("ru", "en"):
                    lang = cfg["ui_lang"]
                if cfg.get("theme_mode") in ("dark", "amoled", "light"):
                    theme = cfg["theme_mode"]
                sc = int(cfg.get("ui_scale", 100))
                if sc in SCALE_OPTIONS:
                    scale = sc
                elif 75 <= sc <= 150:
                    scale = min(SCALE_OPTIONS, key=lambda x: abs(x - sc))
            except Exception:
                pass
        return lang, theme, scale

    def _tr(self, key, **kwargs):
        text = UI_STRINGS.get(self.ui_lang, UI_STRINGS["ru"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _get_flag_qicon_for_label(self, label_text):
        if not label_text or label_text in ALL_LANG_PLACEHOLDERS:
            return None
        clean = strip_flag_prefix(label_text)
        if clean.startswith("Авто ИИ (") or clean.startswith("Auto AI (") or clean in (UI_STRINGS["ru"]["auto_ai"], UI_STRINGS["en"]["auto_ai"]):
            pm = self.flag_pixmaps.get("badge_ai")
            return QIcon(pm.copy()) if pm else None
        if clean.startswith("Авто (") or clean.startswith("Auto (") or clean in (UI_STRINGS["ru"]["auto_fast"], UI_STRINGS["en"]["auto_fast"]):
            pm = self.flag_pixmaps.get("badge_fast")
            return QIcon(pm.copy()) if pm else None

        canon = self._lang_to_canonical(clean)
        iso = LANG_ISO_MAP.get(canon, "badge_fast")
        pm = self.flag_pixmaps.get(iso) or self.flag_pixmaps.get("badge_fast")
        return QIcon(pm.copy()) if pm is not None else None

    def _get_model_qicon_for_label(self, label_text):
        clean = strip_loaded_prefix(label_text)
        if not clean or clean in ALL_MODEL_PLACEHOLDERS:
            return None
        if self._is_model_vision_capable(clean):
            sz = max(14, int(round(18 * (self.ui_scale / 100.0))))
            return create_vector_qicon("vision", THEME["vision_purple"], sz)
        return None

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("CentralRoot")
        self.setCentralWidget(central)

        self.root_grid = QGridLayout(central)
        self.root_grid.setContentsMargins(12, 12, 12, 12)
        self.root_grid.setHorizontalSpacing(8)
        self.root_grid.setVerticalSpacing(8)
        self.root_grid.setColumnStretch(0, 1)
        self.root_grid.setColumnStretch(1, 0)
        self.root_grid.setColumnStretch(2, 1)
        self.root_grid.setRowStretch(1, 1)

        # Row 0: Language Selectors
        self.dd_src = SearchableSelector(
            self, self._get_localized_world_languages(), self._tr("auto_ai"),
            aliases=LANG_MAP, prefer_upwards=False, height=34,
            allow_custom=True, font_size=11, icon_provider=self._get_flag_qicon_for_label
        )
        self.dd_src.selectionChanged.connect(self._on_src_lang_selected)
        self.root_grid.addWidget(self.dd_src, 0, 0)

        self.dd_tgt = SearchableSelector(
            self, self._get_localized_target_languages(), self._tr("select_lang"),
            aliases=LANG_MAP, prefer_upwards=False, height=34,
            allow_custom=True, font_size=11, icon_provider=self._get_flag_qicon_for_label
        )
        self.dd_tgt.selectionChanged.connect(self._on_tgt_lang_selected)
        self.root_grid.addWidget(self.dd_tgt, 0, 2)

        # Row 1, Col 0: Input Panel
        in_box = QWidget()
        in_lay = QVBoxLayout(in_box)
        in_lay.setContentsMargins(0, 0, 0, 0)
        in_lay.setSpacing(6)

        self.img_banner = QFrame()
        self.img_banner.setObjectName("ImageBanner")
        self.img_banner.setFixedHeight(44)
        self.img_banner.hide()
        banner_lay = QHBoxLayout(self.img_banner)
        banner_lay.setContentsMargins(8, 4, 8, 4)
        banner_lay.setSpacing(8)

        self.lbl_img_thumb = QLabel()
        self.lbl_img_thumb.setFixedSize(48, 32)
        self.lbl_img_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_lay.addWidget(self.lbl_img_thumb)

        self.lbl_img_vis_icon = QLabel()
        self.lbl_img_vis_icon.setFixedSize(20, 20)
        self.lbl_img_vis_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_lay.addWidget(self.lbl_img_vis_icon)

        self.lbl_img_info = QLabel()
        self.lbl_img_info.setFont(QFont(UI_FONT, 10, QFont.Weight.DemiBold))
        banner_lay.addWidget(self.lbl_img_info, 1)

        self.btn_img_remove = QPushButton("✕")
        self.btn_img_remove.setObjectName("DangerBtn")
        self.btn_img_remove.setFixedSize(26, 26)
        self.btn_img_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_img_remove.clicked.connect(self.clear_attached_image)
        banner_lay.addWidget(self.btn_img_remove)

        in_lay.addWidget(self.img_banner)

        self.t_in = InputTextEdit()
        self.t_in.setObjectName("EditorIn")
        self.t_in.setFont(QFont(UI_FONT, 12))
        self.t_in.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.t_in.customContextMenuRequested.connect(self._show_in_context_menu)
        self.t_in.textChanged.connect(self._mark_edited)
        self.t_in.submitRequested.connect(self._force_trigger)
        self.t_in.imagePasted.connect(self._attach_qimage)
        self.md_highlighter = MarkdownInputHighlighter(self.t_in.document())
        in_lay.addWidget(self.t_in, 1)

        self.root_grid.addWidget(in_box, 1, 0)

        # Row 1, Col 1: Center Action Bar
        self.mid_bar = QWidget()
        self.mid_bar.setFixedWidth(40)
        mid_lay = QVBoxLayout(self.mid_bar)
        mid_lay.setContentsMargins(0, 0, 0, 0)
        mid_lay.setSpacing(6)

        self.btn_swap = QPushButton()
        self.btn_swap.setFixedSize(38, 34)
        self._set_btn_enabled_with_cursor(self.btn_swap, False)
        self.btn_swap.clicked.connect(self.swap_languages)
        mid_lay.addWidget(self.btn_swap)

        self.btn_img = QPushButton()
        self.btn_img.setFixedSize(38, 34)
        self._set_btn_enabled_with_cursor(self.btn_img, True)
        self.btn_img.clicked.connect(self.select_image_file)
        mid_lay.addWidget(self.btn_img)

        self.btn_tts = QPushButton()
        self.btn_tts.setFixedSize(38, 34)
        self._set_btn_enabled_with_cursor(self.btn_tts, True)
        self.btn_tts.clicked.connect(self.toggle_tts)
        mid_lay.addWidget(self.btn_tts)

        mid_lay.addStretch(1)

        self.btn_go = QPushButton()
        self.btn_go.setObjectName("AccentBtn")
        self.btn_go.setFixedSize(38, 86)
        self._set_btn_enabled_with_cursor(self.btn_go, True)
        self.btn_go.clicked.connect(self._force_trigger)
        mid_lay.addWidget(self.btn_go)

        mid_lay.addStretch(1)

        # Кнопка остановки скрыта в простое и появляется с красным контуром только во время перевода
        self.btn_stop = QPushButton()
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setFixedSize(38, 34)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_translation)
        self.btn_stop.hide()
        mid_lay.addWidget(self.btn_stop)

        self.root_grid.addWidget(self.mid_bar, 1, 1)

        # Row 1, Col 2: Output Panel
        out_box = QWidget()
        out_lay = QGridLayout(out_box)
        out_lay.setContentsMargins(0, 0, 0, 0)

        self.t_out = QTextEdit()
        self.t_out.setObjectName("EditorOut")
        self.t_out.setReadOnly(True)
        self.t_out.setFont(QFont(UI_FONT, 12))
        self.t_out.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.t_out.customContextMenuRequested.connect(self._show_out_context_menu)
        out_lay.addWidget(self.t_out, 0, 0)

        self.btn_instant = QPushButton(self._tr("instant_btn"))
        self.btn_instant.setObjectName("AccentBtn")
        self.btn_instant.setFixedHeight(28)
        self.btn_instant.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_instant.clicked.connect(self.skip_typewriter_animation)
        self.btn_instant.hide()
        out_lay.addWidget(
            self.btn_instant, 0, 0,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
        )

        self.root_grid.addWidget(out_box, 1, 2)

        # Row 2: Thin Progress Line
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ThinProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.root_grid.addWidget(self.progress_bar, 2, 0, 1, 3)

        # Row 3, Col 0: Bottom Left Status
        bot_left = QWidget()
        bl_lay = QHBoxLayout(bot_left)
        bl_lay.setContentsMargins(2, 0, 2, 0)
        bl_lay.setSpacing(10)

        self.chk_auto = AnimatedToggleSwitch(self._tr("auto_trans_chk"))
        self.chk_auto.setChecked(True)
        self.chk_auto.toggled.connect(lambda _: self._save_config())
        bl_lay.addWidget(self.chk_auto)

        self.lbl_status = QLabel(self._tr("connecting"))
        self.lbl_status.setFont(QFont(UI_FONT, 10, QFont.Weight.DemiBold))
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.lbl_status.setMinimumWidth(40)
        bl_lay.addWidget(self.lbl_status, 1)

        self.root_grid.addWidget(bot_left, 3, 0)

        # Row 3, Col 2: Bottom Right Controls
        bot_right = QWidget()
        br_lay = QHBoxLayout(bot_right)
        br_lay.setContentsMargins(0, 0, 0, 0)
        br_lay.setSpacing(4)

        self.dd_model = SearchableSelector(
            self, [self._tr("select_model")], self._tr("select_model"),
            prefer_upwards=True, height=30, allow_custom=False, font_size=10,
            icon_provider=self._get_model_qicon_for_label
        )
        self.dd_model.selectionChanged.connect(self.set_model)
        br_lay.addWidget(self.dd_model, 1)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setFixedSize(30, 30)
        self._set_btn_enabled_with_cursor(self.btn_refresh, True)
        self.btn_refresh.clicked.connect(lambda: self.fetch_models(auto_start_server=False))
        br_lay.addWidget(self.btn_refresh)

        self.btn_server = QPushButton(self._tr("server_btn"))
        self.btn_server.setObjectName("ServerBtn")
        self.btn_server.setFixedHeight(30)
        self._set_btn_enabled_with_cursor(self.btn_server, True)
        self.btn_server.clicked.connect(self.start_lm_studio_server_manual)
        br_lay.addWidget(self.btn_server)

        self.btn_load_model = QPushButton()
        self.btn_load_model.setFixedSize(30, 30)
        self._set_btn_enabled_with_cursor(self.btn_load_model, True)
        self.btn_load_model.clicked.connect(self.load_selected_model_to_vram)
        br_lay.addWidget(self.btn_load_model)

        self.btn_vram = QPushButton("VRAM")
        self.btn_vram.setObjectName("DangerBtn")
        self.btn_vram.setFixedHeight(30)
        self._set_btn_enabled_with_cursor(self.btn_vram, True)
        self.btn_vram.clicked.connect(self.unload_vram)
        br_lay.addWidget(self.btn_vram)

        self.btn_settings = QPushButton()
        self.btn_settings.setFixedSize(30, 30)
        self._set_btn_enabled_with_cursor(self.btn_settings, True)
        self.btn_settings.clicked.connect(self._toggle_settings_popup)
        br_lay.addWidget(self.btn_settings)

        self.root_grid.addWidget(bot_right, 3, 2)

        # Settings Floating Card
        self._build_settings_popup()
        self._refresh_all_tooltips()
        self._refresh_button_icons()

    def _build_settings_popup(self):
        self.settings_card = QFrame(self)
        self.settings_card.setObjectName("SettingsCard")
        self.settings_card.setFixedWidth(320)
        self.settings_card.hide()

        self._set_opacity = QGraphicsOpacityEffect(self.settings_card)
        self._set_opacity.setOpacity(0.0)
        self.settings_card.setGraphicsEffect(self._set_opacity)

        self._set_fade = QPropertyAnimation(self._set_opacity, b"opacity", self)
        self._set_fade.setDuration(140)
        self._set_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._set_closing = False
        self._set_fade.finished.connect(self._on_settings_fade_finished)

        lay = QVBoxLayout(self.settings_card)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)

        self.lbl_set_title = QLabel(self._tr("settings_title"))
        self.lbl_set_title.setFont(QFont(UI_FONT, 10, QFont.Weight.Bold))
        lay.addWidget(self.lbl_set_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("SeparatorLine")
        lay.addWidget(sep)

        self.chk_pin = AnimatedToggleSwitch(self._tr("settings_pin"))
        self.chk_pin.toggled.connect(self._toggle_pin)
        lay.addWidget(self.chk_pin)

        self.chk_smart = AnimatedToggleSwitch(self._tr("smart_search_sw"))
        self.chk_smart.toggled.connect(self._toggle_smart_search)
        lay.addWidget(self.chk_smart)

        self.chk_thinking = AnimatedToggleSwitch(self._tr("settings_thinking"))
        self.chk_thinking.toggled.connect(self._toggle_thinking)
        lay.addWidget(self.chk_thinking)

        self.lbl_set_vision = QLabel(self._tr("settings_vision_model"))
        self.lbl_set_vision.setFont(QFont(UI_FONT, 9, QFont.Weight.DemiBold))
        lay.addWidget(self.lbl_set_vision)

        vis_choices, vis_default = self._get_vision_dropdown_items()
        self.dd_vision_model = SearchableSelector(
            self, vis_choices, vis_default,
            prefer_upwards=True, height=28, allow_custom=False, font_size=10,
            icon_provider=self._get_model_qicon_for_label
        )
        self.dd_vision_model.selectionChanged.connect(self._on_vision_model_selected)
        lay.addWidget(self.dd_vision_model)

        self.lbl_set_theme = QLabel(self._tr("settings_theme"))
        self.lbl_set_theme.setFont(QFont(UI_FONT, 9, QFont.Weight.DemiBold))
        lay.addWidget(self.lbl_set_theme)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(6)
        self.btn_theme_dark = AnimatedPillButton(self._tr("theme_dark"))
        self.btn_theme_amoled = AnimatedPillButton(self._tr("theme_amoled"))
        self.btn_theme_light = AnimatedPillButton(self._tr("theme_light"))
        for mode_id, btn in (("dark", self.btn_theme_dark), ("amoled", self.btn_theme_amoled), ("light", self.btn_theme_light)):
            btn.setFixedHeight(26)
            btn.setFont(QFont(UI_FONT, 10, QFont.Weight.DemiBold))
            btn.clicked.connect(lambda checked=False, m=mode_id: self.apply_theme(m))
            theme_row.addWidget(btn)
        lay.addLayout(theme_row)

        scale_row = QHBoxLayout()
        self.lbl_set_scale = QLabel(self._tr("settings_scale"))
        self.lbl_set_scale.setFont(QFont(UI_FONT, 10))
        scale_row.addWidget(self.lbl_set_scale, 1)

        scale_items = [f"{p}%" for p in SCALE_OPTIONS]
        self.dd_scale = SearchableSelector(
            self, scale_items, f"{self.ui_scale}%",
            prefer_upwards=True, height=26, allow_custom=False, editable=False,
            font_size=10, min_popup_width=92
        )
        self.dd_scale.setFixedWidth(92)
        self.dd_scale.selectionChanged.connect(self._on_scale_selected)
        scale_row.addWidget(self.dd_scale)
        lay.addLayout(scale_row)

        lang_row = QHBoxLayout()
        self.lbl_set_lang = QLabel(self._tr("settings_lang"))
        self.lbl_set_lang.setFont(QFont(UI_FONT, 10))
        lang_row.addWidget(self.lbl_set_lang, 1)

        self.btn_lang_ru = AnimatedPillButton("RU")
        self.btn_lang_ru.setIcon(QIcon(self.flag_pixmaps["ru"].copy()))
        self.btn_lang_ru.setIconSize(QSize(20, 14))
        self.btn_lang_ru.setFixedSize(58, 26)
        self.btn_lang_ru.setFont(QFont(UI_FONT, 10, QFont.Weight.DemiBold))
        self.btn_lang_ru.clicked.connect(lambda: self.set_ui_language("ru"))
        lang_row.addWidget(self.btn_lang_ru)

        self.btn_lang_en = AnimatedPillButton("EN")
        self.btn_lang_en.setIcon(QIcon(self.flag_pixmaps["gb"].copy()))
        self.btn_lang_en.setIconSize(QSize(20, 14))
        self.btn_lang_en.setFixedSize(58, 26)
        self.btn_lang_en.setFont(QFont(UI_FONT, 10, QFont.Weight.DemiBold))
        self.btn_lang_en.clicked.connect(lambda: self.set_ui_language("en"))
        lang_row.addWidget(self.btn_lang_en)

        lay.addLayout(lang_row)

    def _on_scale_selected(self, label):
        try:
            pct = int(label.replace("%", "").strip())
            self.apply_scale(pct, save=True, resize_window=True)
        except Exception:
            pass

    def apply_scale(self, scale_pct, save=True, resize_window=False):
        scale_pct = max(75, min(150, int(scale_pct)))
        self.ui_scale = scale_pct
        sf = scale_pct / 100.0

        # Учитываем доступную геометрию экрана (важно при 2K + системном масштабе 125%)
        avail_w, avail_h = 1920, 1080
        scr = self.screen() or QApplication.primaryScreen()
        if scr is not None:
            ag = scr.availableGeometry()
            avail_w, avail_h = ag.width(), ag.height()

        min_w = min(max(680, int(round(880 * sf))), max(640, avail_w - 40))
        min_h = min(max(420, int(round(500 * sf))), max(400, avail_h - 60))
        self.setMinimumSize(min_w, min_h)
        if resize_window:
            target_w = min(max(min_w, int(round(1040 * sf))), max(min_w, avail_w - 40))
            target_h = min(max(min_h, int(round(590 * sf))), max(min_h, avail_h - 60))
            self.resize(target_w, target_h)

        margin = max(8, int(round(12 * sf)))
        spacing = max(5, int(round(8 * sf)))
        self.root_grid.setContentsMargins(margin, margin, margin, margin)
        self.root_grid.setHorizontalSpacing(spacing)
        self.root_grid.setVerticalSpacing(spacing)

        self.dd_src.apply_scale(sf, 34, 11, base_min_popup=200)
        self.dd_tgt.apply_scale(sf, 34, 11, base_min_popup=200)
        self.dd_model.apply_scale(sf, 30, 10, base_min_popup=240)
        self.dd_vision_model.apply_scale(sf, 28, 10, base_min_popup=240)
        self.dd_scale.apply_scale(sf, 26, 10, base_min_popup=86)
        self.dd_scale.setFixedWidth(max(78, int(round(92 * sf))))

        editor_fs = max(9, int(round(12 * sf)))
        self.t_in.setFont(QFont(UI_FONT, editor_fs))
        self.t_out.setFont(QFont(UI_FONT, editor_fs))

        mid_w = max(32, int(round(40 * sf)))
        btn_w = max(30, int(round(38 * sf)))
        btn_h = max(28, int(round(34 * sf)))
        go_h = max(64, int(round(86 * sf)))
        self.mid_bar.setFixedWidth(mid_w)
        for b in (self.btn_swap, self.btn_img, self.btn_tts, self.btn_stop):
            b.setFixedSize(btn_w, btn_h)
        self.btn_go.setFixedSize(btn_w, go_h)

        bot_h = max(26, int(round(30 * sf)))
        for b in (self.btn_refresh, self.btn_load_model, self.btn_settings):
            b.setFixedSize(bot_h, bot_h)
        self.btn_server.setFixedHeight(bot_h)
        self.btn_vram.setFixedHeight(bot_h)
        self.btn_instant.setFixedHeight(max(24, int(round(28 * sf))))

        small_fs = max(8, int(round(10 * sf)))
        title_fs = max(9, int(round(10 * sf)))
        sub_fs = max(8, int(round(9 * sf)))
        self.chk_auto.setFont(QFont(UI_FONT, small_fs))
        self.lbl_status.setFont(QFont(UI_FONT, small_fs, QFont.Weight.DemiBold))

        # Масштабируем карточку настроек и все её элементы
        self.settings_card.setFixedWidth(max(280, int(round(320 * sf))))
        self.lbl_set_title.setFont(QFont(UI_FONT, title_fs, QFont.Weight.Bold))
        for sw in (self.chk_pin, self.chk_smart, self.chk_thinking):
            sw.setFont(QFont(UI_FONT, small_fs))
        for lbl in (self.lbl_set_vision, self.lbl_set_theme):
            lbl.setFont(QFont(UI_FONT, sub_fs, QFont.Weight.DemiBold))
        for lbl in (self.lbl_set_scale, self.lbl_set_lang):
            lbl.setFont(QFont(UI_FONT, small_fs))

        pill_h = max(24, int(round(26 * sf)))
        for b in (self.btn_theme_dark, self.btn_theme_amoled, self.btn_theme_light):
            b.setFixedHeight(pill_h)
            b.setFont(QFont(UI_FONT, small_fs, QFont.Weight.DemiBold))

        lang_btn_w = max(52, int(round(58 * sf)))
        lang_ico_w = max(16, int(round(20 * sf)))
        lang_ico_h = max(11, int(round(14 * sf)))
        for b in (self.btn_lang_ru, self.btn_lang_en):
            b.setFixedSize(lang_btn_w, pill_h)
            b.setIconSize(QSize(lang_ico_w, lang_ico_h))
            b.setFont(QFont(UI_FONT, small_fs, QFont.Weight.DemiBold))

        self._apply_stylesheet()
        self._refresh_button_icons()
        self._apply_elided_status_text()
        if self.settings_card.isVisible():
            self._sync_settings_popup_position()
        if save:
            self._save_config()

    def _on_settings_fade_finished(self):
        if self._set_closing:
            self.settings_card.hide()
            self._set_closing = False

    def _hide_settings_card_animated(self):
        self.dd_vision_model.close_popup()
        self.dd_scale.close_popup()
        if not self.settings_card.isVisible():
            return
        self._set_fade.stop()
        self._set_closing = True
        self._set_fade.setStartValue(self._set_opacity.opacity())
        self._set_fade.setEndValue(0.0)
        self._set_fade.start()

    def _refresh_button_icons(self):
        fg = THEME["text_main"]
        dim = THEME["text_dim"]
        sf = self.ui_scale / 100.0
        sz_mid = max(14, int(round(18 * sf)))
        sz_go = max(16, int(round(20 * sf)))
        sz_bot = max(13, int(round(16 * sf)))

        self.btn_swap.setIcon(create_vector_qicon("swap", fg if self.btn_swap.isEnabled() else dim, sz_mid))
        self.btn_swap.setIconSize(QSize(sz_mid, sz_mid))
        self.btn_img.setIcon(create_vector_qicon("image", "#ffffff" if self._attached_image_b64 else fg, sz_mid))
        self.btn_img.setIconSize(QSize(sz_mid, sz_mid))
        self.btn_tts.setIcon(create_vector_qicon("tts_stop" if self._is_speaking else "tts_play", "#ffffff" if self._is_speaking else fg, sz_mid))
        self.btn_tts.setIconSize(QSize(sz_mid, sz_mid))
        self.btn_go.setIcon(create_vector_qicon("play", "#ffffff" if self.btn_go.isEnabled() else dim, sz_go))
        self.btn_go.setIconSize(QSize(sz_go, sz_go))

        stop_col = "#dc2626" if self.theme_mode == "light" else "#ffffff"
        self.btn_stop.setIcon(create_vector_qicon("stop", stop_col, sz_mid))
        self.btn_stop.setIconSize(QSize(sz_mid, sz_mid))

        self.btn_refresh.setIcon(create_vector_qicon("refresh", fg, sz_bot))
        self.btn_refresh.setIconSize(QSize(sz_bot, sz_bot))
        self.btn_server.setIcon(create_vector_qicon("server", fg, sz_bot))
        self.btn_server.setIconSize(QSize(sz_bot, sz_bot))
        self.btn_load_model.setIcon(create_vector_qicon("model_load", fg if self.btn_load_model.isEnabled() else dim, sz_bot))
        self.btn_load_model.setIconSize(QSize(sz_bot, sz_bot))
        self.btn_vram.setIcon(create_vector_qicon("vram_clean", "#ef4444" if self.theme_mode == "light" else "#ffffff", sz_bot))
        self.btn_vram.setIconSize(QSize(sz_bot, sz_bot))
        self.btn_settings.setIcon(create_vector_qicon("settings", fg, sz_bot))
        self.btn_settings.setIconSize(QSize(sz_bot, sz_bot))

        vis_sz = max(14, int(round(18 * sf)))
        self.lbl_img_vis_icon.setPixmap(create_vector_qicon("vision", THEME["vision_purple"], vis_sz).pixmap(vis_sz, vis_sz))

    def _apply_stylesheet(self):
        t = THEME
        sf = self.ui_scale / 100.0
        btn_fs = max(9, int(round(11 * sf)))
        btn_pad_h = max(6, int(round(8 * sf)))
        qss = f"""
        QMainWindow, QWidget#CentralRoot {{
            background-color: {t['bg_root']};
            color: {t['text_main']};
        }}
        QFrame#SelectorBox {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: 6px;
        }}
        QFrame#SelectorBox:hover {{
            border: 1px solid {t['border_focus']};
        }}
        QFrame#SelectorBox[focused="true"] {{
            border: 1px solid {t['border_focus']};
        }}
        QFrame#SelectorBox QLineEdit {{
            background: transparent;
            color: {t['text_main']};
            border: none;
            selection-background-color: {t['bg_accent']};
        }}
        QFrame#SelectorBox QPushButton {{
            background: transparent;
            color: {t['text_muted']};
            border: none;
            border-radius: 4px;
            padding: 0px;
        }}
        QFrame#SelectorBox QPushButton:hover {{
            background-color: {t['bg_hover']};
            color: {t['text_main']};
        }}
        QFrame#SelectorPopup {{
            background-color: {t['bg_popup']};
            border: 1px solid {t['border_focus']};
            border-radius: 6px;
        }}
        QListWidget {{
            background-color: {t['bg_popup']};
            color: {t['text_main']};
            border: none;
            outline: none;
            padding: 2px;
        }}
        QListWidget::item {{
            padding: 2px 8px;
            border-radius: 4px;
        }}
        QListWidget::item:selected {{
            background-color: {t['bg_accent']};
            color: #ffffff;
        }}
        QListWidget::item:hover:!selected {{
            background-color: {t['bg_hover']};
        }}
        QPlainTextEdit#EditorIn {{
            background-color: {t['bg_surface']};
            color: {t['text_main']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 10px;
            selection-background-color: {t['bg_accent']};
            selection-color: #ffffff;
        }}
        QPlainTextEdit#EditorIn:focus {{
            border: 1px solid {t['border_focus']};
        }}
        QTextEdit#EditorOut {{
            background-color: {t['bg_surface_alt']};
            color: {t['text_main']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 10px;
            selection-background-color: {t['bg_accent']};
            selection-color: #ffffff;
        }}
        QFrame#ImageBanner {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border_focus']};
            border-radius: 6px;
        }}
        QPushButton {{
            background-color: {t['bg_btn']};
            color: {t['text_main']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            padding: 0 {btn_pad_h}px;
            font-family: "{UI_FONT}";
            font-size: {btn_fs}px;
            font-weight: 600;
        }}
        QPushButton:hover:enabled {{
            background-color: {t['bg_btn_hover']};
            border: 1px solid {t['border_focus']};
        }}
        QPushButton:disabled {{
            background-color: {t['bg_btn_disabled']};
            color: {t['text_dim']};
            border: 1px solid {t['border']};
        }}
        QPushButton#AccentBtn {{
            background-color: {t['bg_accent']};
            color: #ffffff;
            border: none;
        }}
        QPushButton#AccentBtn:hover:enabled {{
            background-color: {t['bg_accent_hover']};
        }}
        QPushButton#AccentBtn:disabled {{
            background-color: {t['bg_btn_disabled']};
            color: {t['text_dim']};
            border: 1px solid {t['border']};
        }}
        QPushButton#DangerBtn {{
            background-color: {t['bg_danger']};
            color: {"#ef4444" if self.theme_mode == "light" else "#ffffff"};
            border: 1px solid {t['border']};
        }}
        QPushButton#DangerBtn:hover:enabled {{
            background-color: {t['bg_danger_hover']};
            border: 1px solid {t['danger_border']};
        }}
        QPushButton#StopBtn {{
            background-color: {t['bg_danger']};
            color: {"#dc2626" if self.theme_mode == "light" else "#ffffff"};
            border: 1.5px solid {t['danger_border']};
            padding: 0px;
        }}
        QPushButton#StopBtn:hover:enabled {{
            background-color: {t['bg_danger_hover']};
            border: 1.5px solid #ff5555;
        }}
        QProgressBar#ThinProgress {{
            background-color: {t['border']};
            border: none;
            border-radius: 1px;
        }}
        QProgressBar#ThinProgress::chunk {{
            background-color: {t['bg_accent']};
            border-radius: 1px;
        }}
        QFrame#SettingsCard {{
            background-color: {t['bg_popup']};
            border: 1px solid {t['border_focus']};
            border-radius: 8px;
        }}
        QFrame#SeparatorLine {{
            color: {t['border']};
        }}
        QLabel {{
            color: {t['text_main']};
        }}
        QMenu {{
            background-color: {t['bg_popup']};
            color: {t['text_main']};
            border: 1px solid {t['border']};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 5px 18px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {t['bg_accent']};
            color: #ffffff;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['scroll_handle']};
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t['scroll_hover']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            height: 0px;
        }}
        """
        self.setStyleSheet(qss)
        self._update_settings_active_buttons(animated=False)

    def _update_settings_active_buttons(self, animated=True):
        for mode_id, btn in (("dark", self.btn_theme_dark), ("amoled", self.btn_theme_amoled), ("light", self.btn_theme_light)):
            if animated:
                btn.set_active_animated(self.theme_mode == mode_id)
            else:
                btn.sync_active_immediate(self.theme_mode == mode_id)

        if animated:
            self.btn_lang_ru.set_active_animated(self.ui_lang == "ru")
            self.btn_lang_en.set_active_animated(self.ui_lang == "en")
        else:
            self.btn_lang_ru.sync_active_immediate(self.ui_lang == "ru")
            self.btn_lang_en.sync_active_immediate(self.ui_lang == "en")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            gp = event.globalPosition().toPoint()
            local_pt = self.mapFromGlobal(gp)
            all_selectors = [self.dd_src, self.dd_tgt, self.dd_model, self.dd_vision_model, self.dd_scale]
            for sel in all_selectors:
                if sel.popup.isVisible():
                    if not sel.popup.geometry().contains(local_pt) and not sel.geometry().contains(sel.parentWidget().mapFrom(self, local_pt)):
                        sel.close_popup()
            if self.settings_card.isVisible():
                btn_rect = QRect(self.btn_settings.mapTo(self, QPoint(0, 0)), self.btn_settings.size())
                vis_pop_contains = self.dd_vision_model.popup.isVisible() and self.dd_vision_model.popup.geometry().contains(local_pt)
                sc_pop_contains = self.dd_scale.popup.isVisible() and self.dd_scale.popup.geometry().contains(local_pt)
                if not self.settings_card.geometry().contains(local_pt) and not btn_rect.contains(local_pt) and not vis_pop_contains and not sc_pop_contains:
                    self._hide_settings_card_animated()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for sel in (self.dd_src, self.dd_tgt, self.dd_model, self.dd_vision_model, self.dd_scale):
            if sel.popup.isVisible():
                sel.sync_position()
        if self.settings_card.isVisible():
            self._sync_settings_popup_position()
        self._apply_elided_status_text()

    def _close_all_popups(self, except_widget=None):
        for sel in (self.dd_src, self.dd_tgt, self.dd_model, self.dd_vision_model, self.dd_scale):
            if sel is not except_widget:
                sel.close_popup()
        if except_widget not in ("settings", self.dd_vision_model, self.dd_scale):
            self._hide_settings_card_animated()

    def _toggle_settings_popup(self):
        if self.settings_card.isVisible() and not self._set_closing:
            self._hide_settings_card_animated()
        else:
            self._close_all_popups(except_widget="settings")
            self.settings_card.adjustSize()
            self._sync_settings_popup_position()
            self._set_fade.stop()
            self._set_closing = False
            self._set_opacity.setOpacity(0.0)
            self.settings_card.show()
            self.settings_card.raise_()
            self._set_fade.setStartValue(0.0)
            self._set_fade.setEndValue(1.0)
            self._set_fade.start()

    def _sync_settings_popup_position(self):
        self.settings_card.adjustSize()
        pw = self.settings_card.width()
        ph = self.settings_card.height()
        btn_pos = self.btn_settings.mapTo(self, QPoint(0, 0))
        x = min(max(8, btn_pos.x() + self.btn_settings.width() - pw), max(8, self.width() - pw - 8))
        y = max(8, btn_pos.y() - ph - 6)
        self.settings_card.move(x, y)

    def apply_theme(self, mode):
        if mode not in THEME_PALETTES:
            return
        self.theme_mode = mode
        THEME.update(THEME_PALETTES[mode])
        self._apply_stylesheet()
        self._update_settings_active_buttons(animated=True)
        self._refresh_button_icons()
        self._refresh_model_dropdown_labels()
        self.md_highlighter.rehighlight()
        for sw in (self.chk_auto, self.chk_pin, self.chk_smart, self.chk_thinking):
            sw.update()
        if self._tw_main_target or self._tw_mismatch_warning:
            show_dict = self._tw_stream_finished and int(self._tw_displayed_chars) >= len(self._tw_main_target)
            self._render_phased_output(
                self._tw_main_target[:int(self._tw_displayed_chars)],
                self._tw_dict_sections if show_dict else [],
                self._tw_is_dict_mode,
                self._tw_word,
                self._tw_mismatch_warning,
                dict_pending=(self._tw_is_dict_mode and not self._tw_stream_finished and int(self._tw_displayed_chars) >= len(self._tw_main_target))
            )
        self._save_config()

    def set_ui_language(self, new_lang):
        if new_lang not in ("ru", "en") or new_lang == self.ui_lang:
            return
        src_canon = self.auto_detect_mode if self.auto_detect_mode else self._lang_to_canonical(self.dd_src.get())
        tgt_raw = self.dd_tgt.get()
        tgt_is_ph = tgt_raw in ALL_LANG_PLACEHOLDERS
        tgt_canon = "" if tgt_is_ph else self._lang_to_canonical(tgt_raw)

        self.ui_lang = new_lang
        self.chk_auto.setText(self._tr("auto_trans_chk"))
        self.chk_auto.updateGeometry()
        self.btn_server.setText(self._tr("server_btn"))
        self.btn_instant.setText(self._tr("instant_btn"))

        self.lbl_set_title.setText(self._tr("settings_title"))
        self.chk_pin.setText(self._tr("settings_pin"))
        self.chk_smart.setText(self._tr("smart_search_sw"))
        self.chk_thinking.setText(self._tr("settings_thinking"))
        self.lbl_set_vision.setText(self._tr("settings_vision_model"))
        self.lbl_set_theme.setText(self._tr("settings_theme"))
        self.btn_theme_dark.setText(self._tr("theme_dark"))
        self.btn_theme_amoled.setText(self._tr("theme_amoled"))
        self.btn_theme_light.setText(self._tr("theme_light"))
        self.lbl_set_scale.setText(self._tr("settings_scale"))
        self.lbl_set_lang.setText(self._tr("settings_lang"))

        self._refresh_all_tooltips()

        self.dd_src.configure_values(self._get_localized_world_languages())
        self.dd_tgt.configure_values(self._get_localized_target_languages())

        if self.auto_detect_mode:
            self.dd_src.set(self._format_auto_detect_display(self.auto_detect_mode, self.detected_src_lang))
        else:
            self.dd_src.set(self._lang_to_display(src_canon))

        if tgt_is_ph or not tgt_canon:
            self.dd_tgt.set(self._tr("select_lang"))
        else:
            self.dd_tgt.set(self._lang_to_display(tgt_canon))

        cur_mod = strip_loaded_prefix(self.dd_model.get())
        if cur_mod in ALL_MODEL_PLACEHOLDERS:
            if not self._is_online:
                self.dd_model.set(self._tr("offline_model"))
            else:
                self.dd_model.set(self._tr("select_model"))
                self.model_id = self._tr("select_model")

        if self._attached_image_b64:
            self._update_image_banner_ui()

        if not self._anim_running:
            if self._tw_mismatch_langs:
                _, st_msg = self._build_mismatch_texts(*self._tw_mismatch_langs)
                self._set_status_raw(st_msg, "#f59e0b")
            elif self._is_online:
                if self._is_valid_model_selected():
                    self._set_status_raw(self._tr("lms_online"), "#22c55e")
                else:
                    self._set_status_raw(self._tr("choose_model_bottom"), "#eab308")
            else:
                self._set_status_raw(self._tr("server_failed"), "#ef4444")

        self._refresh_model_dropdown_labels()
        self._update_settings_active_buttons(animated=True)
        if self.settings_card.isVisible():
            self._sync_settings_popup_position()
        self._save_config()

    def _refresh_all_tooltips(self):
        self.btn_swap.setToolTip(self._tr("tip_swap"))
        self.btn_img.setToolTip(self._tr("tip_image"))
        self.btn_img_remove.setToolTip(self._tr("tip_remove_img"))
        self.btn_tts.setToolTip(self._tr("tip_tts"))
        self.btn_go.setToolTip(self._tr("tip_go"))
        self.btn_stop.setToolTip(self._tr("tip_stop"))
        self.chk_auto.setToolTip(self._tr("tip_auto_chk"))
        self.btn_refresh.setToolTip(self._tr("tip_refresh"))
        self.btn_server.setToolTip(self._tr("tip_server"))
        self.btn_load_model.setToolTip(self._tr("tip_load_model"))
        self.btn_vram.setToolTip(self._tr("tip_vram"))
        self.btn_settings.setToolTip(self._tr("tip_settings"))

    def _lang_to_canonical(self, val):
        if not val:
            return ""
        clean = strip_flag_prefix(val)
        if clean in ALL_LANG_PLACEHOLDERS:
            return ""
        if clean in ("Auto AI", "Автоопределение (ИИ)", "Auto Detect (AI)", "Auto Detect", "Автоопределение") or clean.startswith("Авто ИИ (") or clean.startswith("Auto AI ("):
            return "Auto AI"
        if clean in ("Auto Fast", "Автоопределение (Быстрое)", "Auto Detect (Fast)") or clean.startswith("Авто (") or clean.startswith("Auto ("):
            return "Auto Fast"
        if clean in LANG_DATA:
            return clean
        low = clean.lower()
        if low in LANG_RU_TO_EN:
            return LANG_RU_TO_EN[low]
        for en_k, (ru_v, _) in LANG_DATA.items():
            if en_k.lower() == low or ru_v.lower() == low:
                return en_k
        return clean

    def _lang_to_display(self, canon_lang):
        if not canon_lang or canon_lang in ALL_LANG_PLACEHOLDERS:
            return self._tr("select_lang")
        canon = self._lang_to_canonical(canon_lang)
        if canon == "Auto AI":
            return self._tr("auto_ai")
        if canon == "Auto Fast":
            return self._tr("auto_fast")
        return LANG_EN_TO_RU.get(canon, canon) if self.ui_lang == "ru" else canon

    def _format_auto_detect_display(self, mode, detected_canon=None):
        if mode == "fast":
            if not detected_canon:
                return self._tr("auto_fast")
            return f"{self._tr('auto_fast_short')} ({self._lang_to_display(detected_canon)})"
        else:
            if not detected_canon:
                return self._tr("auto_ai")
            return f"{self._tr('auto_ai_short')} ({self._lang_to_display(detected_canon)})"

    def _get_localized_world_languages(self):
        return [self._lang_to_display(k) for k in WORLD_LANGUAGES_EN]

    def _get_localized_target_languages(self):
        return [self._lang_to_display(k) for k in TARGET_LANGUAGES_EN]

    def _translate_pos_header(self, raw_header):
        if not raw_header:
            return ""
        h = raw_header.strip().lower()
        if self.ui_lang == "en":
            if h in POS_RU_TO_EN:
                return POS_RU_TO_EN[h]
            res = h
            for ru_k, en_v in POS_TOKEN_RU_TO_EN.items():
                res = res.replace(ru_k, en_v)
            return res
        else:
            if h in POS_EN_TO_RU:
                return POS_EN_TO_RU[h]
            res = h
            for en_k, ru_v in POS_TOKEN_EN_TO_RU.items():
                res = res.replace(en_k, ru_v)
            return res

    def _build_mismatch_texts(self, src_canon, det_canon):
        src_disp = self._lang_to_display(src_canon)
        det_disp = self._lang_to_display(det_canon)
        return (
            self._tr("mismatch_warn", src=src_disp, det=det_disp),
            self._tr("mismatch_status", det=det_disp, src=src_disp)
        )

    def _load_config(self):
        if not os.path.isfile(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            self.dd_src.configure_values(self._get_localized_world_languages())
            self.dd_tgt.configure_values(self._get_localized_target_languages())

            src_canon = self._lang_to_canonical(cfg.get("src_lang", "Auto AI"))
            if not src_canon or src_canon == "Auto AI":
                self.auto_detect_mode = "ai"
                self.dd_src.set(self._format_auto_detect_display("ai", None))
            elif src_canon == "Auto Fast":
                self.auto_detect_mode = "fast"
                self.dd_src.set(self._format_auto_detect_display("fast", None))
            else:
                self.auto_detect_mode = None
                self.dd_src.set(self._lang_to_display(src_canon))

            tgt_raw = cfg.get("tgt_lang", "")
            if not tgt_raw or tgt_raw in ALL_LANG_PLACEHOLDERS:
                self.dd_tgt.set(self._tr("select_lang"))
            else:
                self.dd_tgt.set(self._lang_to_display(self._lang_to_canonical(tgt_raw)))

            saved_model = strip_loaded_prefix(cfg.get("model_id", self._tr("select_model")))
            if saved_model and saved_model not in ALL_MODEL_PLACEHOLDERS:
                self._saved_config_model = saved_model

            self.chk_auto.setChecked(bool(cfg.get("auto_translate", True)))
            self.enable_thinking = bool(cfg.get("enable_thinking", False))
            self.chk_thinking.setChecked(self.enable_thinking)

            saved_vis = strip_loaded_prefix(cfg.get("vision_model_id", ""))
            self.vision_model_id = saved_vis if saved_vis not in ALL_MODEL_PLACEHOLDERS else ""

            self.use_smart_search = bool(cfg.get("smart_search", False))
            self.chk_smart.setChecked(self.use_smart_search)

            self.pin_window = bool(cfg.get("pin_window", False))
            self.chk_pin.setChecked(self.pin_window)
            self._apply_topmost_flag()
        except Exception:
            pass

    def _save_config(self):
        try:
            if self.auto_detect_mode == "ai":
                src_val = "Auto AI"
            elif self.auto_detect_mode == "fast":
                src_val = "Auto Fast"
            else:
                src_val = self._lang_to_canonical(self.dd_src.get())
            tgt_raw = self.dd_tgt.get()
            tgt_val = "" if tgt_raw in ALL_LANG_PLACEHOLDERS else self._lang_to_canonical(tgt_raw)
            clean_m = strip_loaded_prefix(self.model_id)
            model_val = clean_m if clean_m not in ALL_MODEL_PLACEHOLDERS else self._saved_config_model
            cfg = {
                "ui_lang": self.ui_lang,
                "theme_mode": self.theme_mode,
                "ui_scale": self.ui_scale,
                "src_lang": src_val,
                "tgt_lang": tgt_val,
                "model_id": model_val,
                "auto_translate": self.chk_auto.isChecked(),
                "enable_thinking": self.enable_thinking,
                "vision_model_id": self.vision_model_id,
                "smart_search": self.use_smart_search,
                "pin_window": self.pin_window
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _apply_topmost_flag(self):
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.pin_window)
        if was_visible:
            self.show()

    def _toggle_pin(self):
        self.pin_window = self.chk_pin.isChecked()
        self._apply_topmost_flag()
        self._save_config()

    def _toggle_smart_search(self):
        self.use_smart_search = self.chk_smart.isChecked()
        self._save_config()

    def _toggle_thinking(self):
        self.enable_thinking = self.chk_thinking.isChecked()
        self._save_config()
        has_content = bool(self.t_in.toPlainText().strip() or self._attached_image_b64)
        if self.chk_auto.isChecked() and self._is_online and has_content:
            self._force_trigger()

    def _is_model_vision_capable(self, model_name):
        clean = strip_loaded_prefix(model_name)
        if not clean or clean in ALL_MODEL_PLACEHOLDERS:
            return False
        meta = self._model_meta.get(clean, {})
        if meta.get("vision"):
            return True
        low = clean.lower()
        return any(k in low for k in (
            "vision", "-vl", "vl-", "llava", "pixtral", "minicpm-v", "gemma-3", "gemma3",
            "qwen2-vl", "qwen2.5-vl", "qwen3-vl", "internvl", "moondream", "idefics", "molmo"
        ))

    def _get_available_vision_models(self):
        vis = [m for m in self._available_models if self._is_model_vision_capable(m)]
        vis.sort(key=lambda m: (
            self._model_meta.get(m, {}).get("size_bytes") or float("inf"),
            m.lower()
        ))
        return vis

    def _get_vision_dropdown_items(self):
        vis_models = self._get_available_vision_models()
        auto_lbl = self._tr("vision_auto")
        if not vis_models:
            return [self._tr("no_vision_models")], self._tr("no_vision_models")
        formatted = [auto_lbl] + [self._format_model_display(m) for m in vis_models]
        if self.vision_model_id and self.vision_model_id in vis_models:
            default_val = self._format_model_display(self.vision_model_id)
        else:
            default_val = auto_lbl
        return formatted, default_val

    def _on_vision_model_selected(self, val):
        clean = strip_loaded_prefix(val)
        if clean in ALL_MODEL_PLACEHOLDERS or clean == self._tr("vision_auto") or clean == self._tr("no_vision_models"):
            self.vision_model_id = ""
        else:
            self.vision_model_id = clean
        self._save_config()
        if self._attached_image_b64:
            self._update_image_banner_ui()
            if self.chk_auto.isChecked() and self._is_online:
                self._force_trigger()

    def _resolve_effective_vision_model(self):
        active_clean = strip_loaded_prefix(self.model_id)
        if active_clean and active_clean not in ALL_MODEL_PLACEHOLDERS and self._is_model_vision_capable(active_clean):
            return active_clean

        vis_models = self._get_available_vision_models()
        if self.vision_model_id and self.vision_model_id in vis_models:
            return self.vision_model_id

        if vis_models:
            return vis_models[0]
        return None

    def _format_model_display(self, model_name):
        clean = strip_loaded_prefix(model_name)
        if clean in ALL_MODEL_PLACEHOLDERS or not clean:
            return clean
        prefix = LOADED_PREFIX if clean in self._loaded_vram_models else ""
        meta = self._model_meta.get(clean, {})
        size_str = meta.get("size_str", "")
        suffix = f"{MODEL_SIZE_SEP}{size_str}" if size_str else ""
        return f"{prefix}{clean}{suffix}"

    def _sync_server_button_visibility(self):
        self.btn_server.setVisible(not self._is_online)

    def _sync_vram_button_visibility(self):
        clean_cur = strip_loaded_prefix(self.model_id)
        valid_selected = self._is_valid_model_selected()
        cur_is_loaded = valid_selected and (clean_cur in self._loaded_vram_models)
        any_loaded = len(self._loaded_vram_models) > 0

        if not self._is_online:
            self.btn_vram.hide()
            self.btn_load_model.hide()
        elif cur_is_loaded or (not valid_selected and any_loaded):
            self.btn_load_model.hide()
            self.btn_vram.show()
        elif valid_selected and not cur_is_loaded:
            self.btn_vram.hide()
            self.btn_load_model.show()
        else:
            self.btn_vram.hide()
            self.btn_load_model.hide()

    def _refresh_model_dropdown_labels(self):
        self._sync_vram_button_visibility()
        if not self._is_online or not self._available_models:
            return
        placeholder = self._tr("select_model")
        formatted_list = [placeholder] + [self._format_model_display(m) for m in self._available_models]
        self.dd_model.configure_values(formatted_list)
        if self._is_valid_model_selected():
            self.dd_model.set(self._format_model_display(self.model_id))
        else:
            self.dd_model.set(placeholder)

        vis_choices, vis_default = self._get_vision_dropdown_items()
        self.dd_vision_model.configure_values(vis_choices)
        self.dd_vision_model.set(vis_default)
        if self._attached_image_b64:
            self._update_image_banner_ui()

    def _on_src_lang_selected(self, val):
        canon = self._lang_to_canonical(val)
        if canon == "Auto AI":
            self.auto_detect_mode = "ai"
            self.detected_src_lang = None
            self.dd_src.set(self._format_auto_detect_display("ai", None))
        elif canon == "Auto Fast":
            self.auto_detect_mode = "fast"
            self.detected_src_lang = None
            self.dd_src.set(self._format_auto_detect_display("fast", None))
        else:
            self.auto_detect_mode = None
            self.detected_src_lang = None
            self.dd_src.set(self._lang_to_display(canon))
        self._update_swap_button_state()
        self._save_config()
        if self.chk_auto.isChecked():
            self._force_trigger()

    def _on_tgt_lang_selected(self, val):
        if val not in ALL_LANG_PLACEHOLDERS:
            canon = self._lang_to_canonical(val)
            if canon in AUTO_MODES_CANON:
                self.dd_tgt.set(self._tr("select_lang"))
            else:
                self.dd_tgt.set(self._lang_to_display(canon))
        self._update_swap_button_state()
        self._save_config()
        if self.chk_auto.isChecked():
            self._force_trigger()

    def _get_effective_src_mode(self):
        if self.auto_detect_mode == "ai":
            return "Auto AI"
        if self.auto_detect_mode == "fast":
            return "Auto Fast"
        return self._lang_to_canonical(self.dd_src.get())

    def _get_effective_tgt_lang(self):
        raw = self.dd_tgt.get()
        if raw in ALL_LANG_PLACEHOLDERS or not raw:
            return ""
        return self._lang_to_canonical(raw)

    def _is_valid_model_selected(self):
        clean = strip_loaded_prefix(self.model_id)
        return bool(clean) and clean not in ALL_MODEL_PLACEHOLDERS

    def _update_swap_button_state(self):
        tgt_canon = self._get_effective_tgt_lang()
        if not tgt_canon or tgt_canon in AUTO_MODES_CANON:
            self._set_btn_enabled_with_cursor(self.btn_swap, False)
            self._refresh_button_icons()
            return
        if self.auto_detect_mode:
            can_swap = bool(self.detected_src_lang) and (self.detected_src_lang != tgt_canon)
        else:
            src_canon = self._get_effective_src_mode()
            can_swap = bool(src_canon) and (src_canon not in AUTO_MODES_CANON) and (src_canon != tgt_canon)
        self._set_btn_enabled_with_cursor(self.btn_swap, can_swap)
        self._refresh_button_icons()

    def _apply_elided_status_text(self):
        avail_w = max(40, self.lbl_status.width() - 4)
        fm = QFontMetrics(self.lbl_status.font())
        elided = fm.elidedText(self._raw_status_text, Qt.TextElideMode.ElideRight, avail_w)
        self.lbl_status.setText(elided)
        self.lbl_status.setToolTip(self._raw_status_text)
        self.lbl_status.setStyleSheet(f"color: {self._raw_status_color};")

    def _set_status_raw(self, text, color):
        self._raw_status_text = text
        self._raw_status_color = color
        self._apply_elided_status_text()

    def _start_status_anim(self, phase_text, color="#eab308"):
        self._anim_phase_text = phase_text
        self._anim_color = color
        self._anim_start_ts = time.monotonic()
        self._anim_running = True
        self.progress_bar.setRange(0, 0)

    def _update_status_anim_phase(self, phase_text, color="#3b82f6"):
        self._anim_phase_text = phase_text
        self._anim_color = color

    def _stop_status_anim(self, final_text, color="#22c55e", bar_fill=1.0):
        self._anim_running = False
        self._set_status_raw(final_text, color)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(bar_fill * 100))

    def _tick_status_anim(self):
        if not self._anim_running:
            return
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner = frames[self._anim_step % len(frames)]
        elapsed = time.monotonic() - self._anim_start_ts
        unit = "s" if self.ui_lang == "en" else "с"
        self._set_status_raw(f"{spinner} {self._anim_phase_text} ({elapsed:.1f}{unit})", self._anim_color)
        self._anim_step += 1

    def _mark_edited(self):
        self._last_edit_time = time.monotonic()

    def _realtime_watcher(self):
        current_text = self.t_in.toPlainText().strip()
        has_img = bool(self._attached_image_b64)
        state_key = f"[IMG:{len(self._attached_image_b64)}]{current_text}" if has_img else current_text
        elapsed = time.monotonic() - self._last_edit_time

        if not current_text and not has_img:
            if self._last_translated_state[0] != "" or self.detected_src_lang is not None:
                self._abort_active_stream()
                self.stop_tts()
                self._last_translated_state = ("", "", "", "")
                self._last_clean_translation = ""
                self._tw_mismatch_langs = None
                if self.auto_detect_mode:
                    self.detected_src_lang = None
                    self.dd_src.set(self._format_auto_detect_display(self.auto_detect_mode, None))
                self._update_swap_button_state()
                self.t_out.clear()
                self.btn_instant.hide()
                self._stop_status_anim(self._tr("ready"), "#22c55e" if self._is_online else THEME["text_muted"], 0.0)
        elif self.chk_auto.isChecked() and self._is_online:
            tgt_canon = self._get_effective_tgt_lang()
            if not tgt_canon:
                self._stop_status_anim(self._tr("choose_lang_right"), "#eab308", 0.0)
            elif not has_img and not self._is_valid_model_selected():
                self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
            elif has_img and not self._resolve_effective_vision_model():
                self._stop_status_anim(self._tr("no_vision_err"), "#ef4444", 0.0)
            else:
                src_mode = self._get_effective_src_mode()
                eff_mod = self._resolve_effective_vision_model() if has_img else strip_loaded_prefix(self.model_id)
                current_state = (state_key, src_mode, tgt_canon, f"{eff_mod}:{int(self.enable_thinking)}")
                if current_state != self._last_translated_state and elapsed >= 0.35:
                    self._last_translated_state = current_state
                    self.start_translation()

    def _auto_reconnect_loop(self):
        if not self._is_online and not self._server_booting:
            self.fetch_models(silent=True, auto_start_server=False)

    def _force_trigger(self):
        text = self.t_in.toPlainText().strip()
        has_img = bool(self._attached_image_b64)
        if not text and not has_img:
            return
        tgt_canon = self._get_effective_tgt_lang()
        if not tgt_canon:
            self._stop_status_anim(self._tr("choose_lang_right"), "#eab308", 0.0)
            return
        if has_img:
            eff_mod = self._resolve_effective_vision_model()
            if not eff_mod:
                self._stop_status_anim(self._tr("no_vision_err"), "#ef4444", 0.0)
                return
        else:
            if not self._is_valid_model_selected():
                self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
                return
            eff_mod = strip_loaded_prefix(self.model_id)
        src_mode = self._get_effective_src_mode()
        state_key = f"[IMG:{len(self._attached_image_b64)}]{text}" if has_img else text
        self._last_translated_state = (state_key, src_mode, tgt_canon, f"{eff_mod}:{int(self.enable_thinking)}")
        self.start_translation()

    def _attach_qimage(self, qimg, name="Clipboard"):
        if qimg is None or qimg.isNull():
            return False
        w, h = qimg.width(), qimg.height()
        max_dim = 1568
        if max(w, h) > max_dim:
            qimg = qimg.scaled(max_dim, max_dim, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        qimg.save(buf, "JPEG", 88)
        b64_str = base64.b64encode(bytes(buf.data())).decode("ascii")
        buf.close()

        thumb_pm = QPixmap.fromImage(qimg).scaled(48, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbl_img_thumb.setPixmap(thumb_pm)
        self._attached_image_b64 = b64_str
        self._attached_image_name = f"{name} ({w}x{h})"
        self._update_image_banner_ui()
        self.btn_img.setObjectName("AccentBtn")
        self.btn_img.style().unpolish(self.btn_img)
        self.btn_img.style().polish(self.btn_img)
        self._refresh_button_icons()
        self._mark_edited()
        if self.chk_auto.isChecked():
            QTimer.singleShot(60, self._force_trigger)
        return True

    def _update_image_banner_ui(self):
        if not self._attached_image_b64:
            self.img_banner.hide()
            return
        vis_mod = self._resolve_effective_vision_model()
        if vis_mod:
            sz = self._model_meta.get(vis_mod, {}).get("size_str", "")
            sz_part = f" ({sz})" if sz else ""
            vis_tag = f"  →  {vis_mod}{sz_part}"
            self.lbl_img_vis_icon.show()
        else:
            vis_tag = f"  →  {self._tr('no_vision_models')}"
            self.lbl_img_vis_icon.hide()
        self.lbl_img_info.setText(f"{self._attached_image_name}{vis_tag}")
        self.img_banner.show()

    def clear_attached_image(self):
        if not self._attached_image_b64:
            return
        self._attached_image_b64 = ""
        self._attached_image_name = ""
        self.img_banner.hide()
        self.btn_img.setObjectName("")
        self.btn_img.style().unpolish(self.btn_img)
        self.btn_img.style().polish(self.btn_img)
        self._refresh_button_icons()
        self._mark_edited()

    def select_image_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image" if self.ui_lang == "en" else "Выберите изображение",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All files (*.*)"
        )
        if path and os.path.isfile(path):
            qimg = QImage(path)
            if not qimg.isNull():
                self._attach_qimage(qimg, name=os.path.basename(path))

    def _try_paste_image_from_clipboard(self):
        cb = QApplication.clipboard()
        qimg = cb.image()
        if not qimg.isNull():
            return self._attach_qimage(qimg, name="Clipboard")
        md = cb.mimeData()
        if md and md.hasUrls():
            for u in md.urls():
                local = u.toLocalFile()
                if local and os.path.isfile(local) and local.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
                    qi = QImage(local)
                    if not qi.isNull():
                        return self._attach_qimage(qi, name=os.path.basename(local))
        return False

    def _show_in_context_menu(self, pos):
        menu = QMenu(self)
        menu.setCursor(Qt.CursorShape.PointingHandCursor)
        menu.addAction(self._tr("ctx_paste_cur"), self.t_in.paste)
        menu.addAction(self._tr("ctx_paste_rep"), self._paste_replace_all)
        menu.addAction(self._tr("ctx_paste_img"), self._try_paste_image_from_clipboard)
        menu.addAction(self._tr("ctx_open_img"), self.select_image_file)
        menu.addSeparator()
        menu.addAction(self._tr("ctx_copy"), self.t_in.copy)
        menu.addAction(self._tr("ctx_cut"), self.t_in.cut)
        menu.addAction(self._tr("ctx_sel_all"), self.t_in.selectAll)
        menu.addSeparator()
        menu.addAction(self._tr("ctx_bold"), lambda: self._wrap_selection("**", "**"))
        menu.addAction(self._tr("ctx_italic"), lambda: self._wrap_selection("*", "*"))
        menu.addAction(self._tr("ctx_code"), lambda: self._wrap_selection("`", "`"))
        menu.addAction(self._tr("ctx_strike"), lambda: self._wrap_selection("~~", "~~"))
        menu.addSeparator()
        menu.addAction(self._tr("ctx_clear"), self.clear_all)
        menu.exec(self.t_in.mapToGlobal(pos))

    def _show_out_context_menu(self, pos):
        menu = QMenu(self)
        menu.setCursor(Qt.CursorShape.PointingHandCursor)
        menu.addAction(self._tr("ctx_copy_sel"), self._copy_out_selection_or_all)
        menu.addAction(self._tr("ctx_copy_all"), self.copy_output)
        menu.addSeparator()
        menu.addAction(self._tr("ctx_sel_all"), self.t_out.selectAll)
        menu.exec(self.t_out.mapToGlobal(pos))

    def _paste_replace_all(self):
        cb = QApplication.clipboard()
        txt = cb.text()
        if txt:
            self.t_in.setPlainText(txt)
            if self.chk_auto.isChecked():
                self._force_trigger()
        else:
            self._try_paste_image_from_clipboard()

    def _wrap_selection(self, pre, suf):
        cur = self.t_in.textCursor()
        sel = cur.selectedText()
        cur.insertText(f"{pre}{sel}{suf}")
        if not sel:
            cur.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(suf))
            self.t_in.setTextCursor(cur)

    def _copy_out_selection_or_all(self):
        sel = self.t_out.textCursor().selectedText()
        if sel.strip():
            QApplication.clipboard().setText(sel.replace("\u2029", "\n"))
            self._stop_status_anim(self._tr("copied_sel"), "#3b82f6", 1.0)
        else:
            self.copy_output()

    def copy_output(self):
        main_trans = self._extract_clean_main_output()
        if main_trans:
            QApplication.clipboard().setText(main_trans)
            self._stop_status_anim(self._tr("copied"), "#3b82f6", 1.0)

    def _extract_clean_main_output(self):
        if self._last_clean_translation:
            return self._last_clean_translation
        text = self.t_out.toPlainText().strip()
        if not text:
            return ""
        for wp in (UI_STRINGS["ru"]["warn_prefix"], UI_STRINGS["en"]["warn_prefix"]):
            if text.startswith(wp) and "\n\n" in text:
                text = text.split("\n\n", 1)[1].strip()
        for dv in (UI_STRINGS["ru"]["dict_variants"], UI_STRINGS["en"]["dict_variants"]):
            if f" — {dv}\n" in text:
                return text.split("\n\n")[0].strip()
        return text

    def _abort_active_stream(self):
        self._task_id += 1
        self._tw_running = False
        self.btn_instant.hide()
        with self._stream_lock:
            st = self._active_stream
            self._active_stream = None
        if st is not None:
            try:
                st.close()
            except Exception:
                pass

    def clear_all(self):
        self._abort_active_stream()
        self.stop_tts()
        self._last_translated_state = ("", "", "", "")
        self._last_clean_translation = ""
        self._tw_main_target = ""
        self._tw_dict_sections = []
        self._tw_mismatch_warning = ""
        self._tw_mismatch_langs = None
        self._tw_final_status_msg = ""
        if self.auto_detect_mode:
            self.detected_src_lang = None
            self.dd_src.set(self._format_auto_detect_display(self.auto_detect_mode, None))
        self._update_swap_button_state()
        self.clear_attached_image()
        self.t_in.clear()
        self.t_out.clear()
        self._reset_gen_buttons()
        self._stop_status_anim(self._tr("ready"), "#22c55e" if self._is_online else THEME["text_muted"], 0.0)

    def swap_languages(self):
        tgt_canon = self._get_effective_tgt_lang()
        if not tgt_canon or tgt_canon in AUTO_MODES_CANON:
            return
        src_canon = self.detected_src_lang if self.auto_detect_mode else self._get_effective_src_mode()
        if not src_canon or src_canon in AUTO_MODES_CANON:
            return

        self.skip_typewriter_animation()
        self.stop_tts()
        self.auto_detect_mode = None
        self.detected_src_lang = None
        self.dd_src.set(self._lang_to_display(tgt_canon))
        self.dd_tgt.set(self._lang_to_display(src_canon))
        self._update_swap_button_state()
        self._save_config()

        main_part = self._extract_clean_main_output()
        if main_part:
            self.t_in.setPlainText(main_part)
        if self.chk_auto.isChecked():
            self._force_trigger()

    # --- LM Studio CLI & Server Management ---
    def _run_lms_cmd(self, args_list, timeout=15):
        try:
            return subprocess.run(
                [LMS_BIN] + args_list,
                shell=False,
                timeout=timeout,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WIN else 0
            )
        except Exception:
            return None

    def _boot_local_lm_studio_server(self):
        self._server_booting = True
        try:
            self._run_lms_cmd(["daemon", "up"], timeout=8)
            self._run_lms_cmd(["server", "start", "--port", str(LM_PORT), "--cors"], timeout=8)
            self._run_lms_cmd(["server", "start"], timeout=6)

            for _ in range(6):
                for host in (LM_HOST, "localhost"):
                    try:
                        c = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=2.0)
                        c.models.list()
                        return True
                    except Exception:
                        pass
                time.sleep(0.7)

            if LM_STUDIO_GUI_EXE and os.path.isfile(LM_STUDIO_GUI_EXE):
                try:
                    if IS_WIN:
                        si = subprocess.STARTUPINFO()
                        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        si.wShowWindow = 7
                        subprocess.Popen([LM_STUDIO_GUI_EXE, "--minimized"], startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        subprocess.Popen([LM_STUDIO_GUI_EXE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                except Exception:
                    pass

                for _ in range(12):
                    time.sleep(1.0)
                    self._run_lms_cmd(["server", "start", "--port", str(LM_PORT), "--cors"], timeout=5)
                    for host in (LM_HOST, "localhost"):
                        try:
                            c = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=2.0)
                            c.models.list()
                            return True
                        except Exception:
                            pass
            return False
        finally:
            self._server_booting = False

    def start_lm_studio_server_manual(self):
        if self._server_booting:
            return
        self._start_status_anim(self._tr("starting_server"), "#eab308")

        def worker():
            ok = self._boot_local_lm_studio_server()
            if ok:
                QTimer.singleShot(0, lambda: self.fetch_models(silent=False, auto_start_server=False))
            else:
                self.sig.statusAnimStop.emit(self._tr("server_failed"), "#ef4444", 0.0)

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _resolve_disk_model_size(model_key, rel_path=""):
        roots = [
            os.path.expanduser("~/.lmstudio/models"),
            os.path.expanduser("~/.cache/lm-studio/models"),
        ]
        if IS_WIN:
            roots.extend([
                os.path.expandvars(r"%USERPROFILE%\.lmstudio\models"),
                os.path.expandvars(r"%USERPROFILE%\.cache\lm-studio\models"),
            ])
        for root in roots:
            if not os.path.isdir(root):
                continue
            if rel_path:
                cand = os.path.join(root, rel_path)
                if os.path.isfile(cand):
                    try:
                        return os.path.getsize(cand)
                    except Exception:
                        pass
            tail = model_key.split("/")[-1].lower()
            if not tail:
                continue
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if fn.lower().endswith((".gguf", ".safetensors", ".bin")) and tail in fn.lower():
                        try:
                            return os.path.getsize(os.path.join(dirpath, fn))
                        except Exception:
                            pass
        return 0

    def _query_lms_ls_downloaded_models(self, known_api_names=None):
        models = []
        meta_map = {}
        res = self._run_lms_cmd(["ls", "--json"], timeout=6)
        if res and res.stdout:
            try:
                data = json.loads(res.stdout)
                if isinstance(data, list):
                    for item in data:
                        m_key = item.get("modelKey") or item.get("id") or item.get("path")
                        if not m_key or "embed" in m_key.lower():
                            continue
                        models.append(m_key)
                        size_bytes = item.get("sizeBytes") or item.get("size") or 0
                        rel_path = item.get("path") or ""
                        if not size_bytes:
                            size_bytes = self._resolve_disk_model_size(m_key, rel_path)
                        size_str = format_bytes_size(size_bytes)
                        if not size_str and item.get("paramsString"):
                            size_str = str(item.get("paramsString"))
                        meta_map[m_key] = {
                            "size_bytes": size_bytes,
                            "size_str": size_str,
                            "vision": bool(item.get("vision", False)),
                            "path": rel_path,
                        }
            except Exception:
                pass

        for api_name in (known_api_names or []):
            if api_name not in meta_map:
                sz = self._resolve_disk_model_size(api_name)
                meta_map[api_name] = {
                    "size_bytes": sz,
                    "size_str": format_bytes_size(sz),
                    "vision": any(v in api_name.lower() for v in ("vision", "-vl", "vl-", "llava", "pixtral", "minicpm-v", "gemma-3")),
                    "path": "",
                }

        self._model_meta.update(meta_map)
        return models

    def _query_lms_ps_loaded_models(self):
        loaded = set()
        try:
            res = self._run_lms_cmd(["ps"], timeout=5)
            if not res:
                return loaded
            out = (res.stdout or "") + "\n" + (res.stderr or "")
            out_low = out.lower()
            if "no loaded models" in out_low:
                return set()
            tokens_in_ps = set(re.findall(r"[a-z0-9_.\-/]+", out_low))
            for m in self._available_models:
                m_low = m.lower()
                if m_low in tokens_in_ps or re.search(rf"(?<![a-z0-9_.\-/]){re.escape(m_low)}(?![a-z0-9_.\-/])", out_low):
                    loaded.add(m)
        except Exception:
            pass
        return loaded

    def _verified_unload_single_model(self, target_model):
        clean_target = strip_loaded_prefix(target_model)
        if not clean_target or clean_target in ALL_MODEL_PLACEHOLDERS or clean_target not in self._loaded_vram_models:
            return
        for _ in range(2):
            self._run_lms_cmd(["unload", clean_target], timeout=10)
            if clean_target not in self._query_lms_ps_loaded_models():
                break
        self._loaded_vram_models.discard(clean_target)

    def _verified_unload_all_vram(self, timeout_per_step=8):
        if not self._loaded_vram_models:
            return True
        self._run_lms_cmd(["unload", "--all"], timeout=timeout_per_step)
        remaining = self._query_lms_ps_loaded_models()
        if remaining:
            for m in list(remaining):
                self._run_lms_cmd(["unload", m], timeout=timeout_per_step)
            remaining = self._query_lms_ps_loaded_models()
        self._loaded_vram_models = remaining
        return len(remaining) == 0

    def _ensure_model_loaded_in_vram(self, target_model, unload_others=True):
        clean_target = strip_loaded_prefix(target_model)
        if not clean_target or clean_target in ALL_MODEL_PLACEHOLDERS:
            return False

        currently_loaded = self._query_lms_ps_loaded_models()
        self._loaded_vram_models = currently_loaded
        if clean_target in currently_loaded:
            self.sig.refreshModelLabels.emit()
            return True

        if unload_others and currently_loaded:
            self._verified_unload_all_vram(timeout_per_step=8)

        self._run_lms_cmd(["load", clean_target, "-y"], timeout=60)

        for _ in range(10):
            loaded_now = self._query_lms_ps_loaded_models()
            if clean_target in loaded_now:
                self._loaded_vram_models = loaded_now
                self.sig.refreshModelLabels.emit()
                return True
            time.sleep(0.4)

        self._loaded_vram_models.add(clean_target)
        self.sig.refreshModelLabels.emit()
        return True

    def set_model(self, selected_label):
        new_model = strip_loaded_prefix(selected_label)
        old_model = strip_loaded_prefix(self.model_id)
        self.model_id = new_model
        self._model_switch_id += 1
        switch_id = self._model_switch_id

        if new_model not in ALL_MODEL_PLACEHOLDERS:
            self._saved_config_model = new_model
        self._save_config()
        self._refresh_model_dropdown_labels()

        should_unload_old = (
            old_model and old_model != new_model
            and old_model not in ALL_MODEL_PLACEHOLDERS
            and old_model in self._loaded_vram_models
        )

        if should_unload_old:
            def swap_vram():
                self._abort_active_stream()
                self.sig.statusAnimStart.emit(f"{self._tr('unloading')} {old_model}", "#eab308")
                self._verified_unload_single_model(old_model)
                if self._model_switch_id != switch_id:
                    return
                self.sig.refreshModelLabels.emit()
                if new_model in ALL_MODEL_PLACEHOLDERS:
                    self.sig.statusAnimStop.emit(self._tr("model_reset"), THEME["text_muted"], 0.0)
                else:
                    self.sig.statusAnimStop.emit(self._tr("model_ready"), "#22c55e", 0.0)
                    if self.chk_auto.isChecked():
                        QTimer.singleShot(0, self._force_trigger)
            threading.Thread(target=swap_vram, daemon=True).start()
        else:
            if new_model in ALL_MODEL_PLACEHOLDERS:
                self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
            else:
                self._stop_status_anim(self._tr("model_ready"), "#22c55e", 0.0)
                if self.chk_auto.isChecked():
                    self._force_trigger()

    def fetch_models(self, silent=False, auto_start_server=True):
        if not silent:
            self._start_status_anim(self._tr("searching_lms"), "#3b82f6")

        def task():
            for host in (LM_HOST, "localhost"):
                try:
                    test_client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=2.5)
                    models = test_client.models.list()
                    names = [m.id for m in models.data if "embed" not in m.id.lower()]
                    cli_names = self._query_lms_ls_downloaded_models(known_api_names=names)
                    if not names:
                        names = cli_names
                    self.client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=30.0)
                    if names:
                        self._available_models = names
                        self._loaded_vram_models = self._query_lms_ps_loaded_models()
                        self.sig.modelsUpdated.emit(names, True, silent)
                    else:
                        self._available_models = []
                        self._loaded_vram_models = set()
                        self.sig.modelsUpdated.emit([self._tr("no_models")], False, silent)
                    return
                except Exception:
                    continue

            if auto_start_server and not silent:
                self.sig.statusAnimPhase.emit(self._tr("starting_server"), "#eab308")
                if self._boot_local_lm_studio_server():
                    for host in (LM_HOST, "localhost"):
                        try:
                            test_client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=3.0)
                            models = test_client.models.list()
                            names = [m.id for m in models.data if "embed" not in m.id.lower()]
                            cli_names = self._query_lms_ls_downloaded_models(known_api_names=names)
                            if not names:
                                names = cli_names
                            self.client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=30.0)
                            if names:
                                self._available_models = names
                                self._loaded_vram_models = self._query_lms_ps_loaded_models()
                                self.sig.modelsUpdated.emit(names, True, silent)
                                return
                        except Exception:
                            continue

            self._loaded_vram_models = set()
            self.sig.modelsUpdated.emit([self._tr("offline_model")], False, silent)

        threading.Thread(target=task, daemon=True).start()

    def _update_models_ui(self, names, online, silent=False):
        self._is_online = online
        self._sync_server_button_visibility()
        self._sync_vram_button_visibility()
        if online:
            self._available_models = list(names)
            clean_cur = strip_loaded_prefix(self.model_id)
            if clean_cur in names:
                self.model_id = clean_cur
            elif self._saved_config_model in names:
                self.model_id = self._saved_config_model
            else:
                self.model_id = self._tr("select_model")

            self._refresh_model_dropdown_labels()
            if self._is_valid_model_selected():
                self._stop_status_anim(self._tr("lms_online"), "#22c55e", 0.0)
            else:
                self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
        else:
            self.dd_model.configure_values(names)
            self.dd_model.set(names[0])
            self.model_id = ""
            if not silent:
                self._stop_status_anim(self._tr("server_failed"), "#ef4444", 0.0)

    def load_selected_model_to_vram(self):
        if self._is_loading_model or not self._is_online or not self._is_valid_model_selected():
            return
        target_model = strip_loaded_prefix(self.model_id)
        if target_model in self._loaded_vram_models:
            self._sync_vram_button_visibility()
            return

        self._is_loading_model = True
        self._set_btn_enabled_with_cursor(self.btn_load_model, False)
        self._refresh_button_icons()
        self._start_status_anim(f"{self._tr('loading_vram')}: {target_model}", "#eab308")

        def task():
            try:
                self._ensure_model_loaded_in_vram(target_model, unload_others=True)
                self.sig.statusAnimStop.emit(self._tr("model_ready"), "#22c55e", 1.0)
                if self.chk_auto.isChecked() and (self.t_in.toPlainText().strip() or self._attached_image_b64):
                    QTimer.singleShot(0, self._force_trigger)
            finally:
                self._is_loading_model = False
                QTimer.singleShot(0, self._on_load_model_btn_done)

        threading.Thread(target=task, daemon=True).start()

    def _on_load_model_btn_done(self):
        self._set_btn_enabled_with_cursor(self.btn_load_model, True)
        self._refresh_button_icons()

    def unload_vram(self):
        if not self._loaded_vram_models:
            self._sync_vram_button_visibility()
            self._stop_status_anim(self._tr("vram_already_empty"), "#22c55e", 0.0)
            return

        def task():
            self._abort_active_stream()
            self.sig.statusAnimStart.emit(self._tr("vram_check"), "#eab308")
            all_clean = self._verified_unload_all_vram()
            self.sig.refreshModelLabels.emit()
            if all_clean:
                self.sig.statusAnimStop.emit(self._tr("vram_cleaned_all"), "#22c55e", 0.0)
            else:
                self.sig.statusAnimStop.emit(self._tr("vram_cleaned"), "#eab308", 0.0)

        threading.Thread(target=task, daemon=True).start()

    def stop_translation(self):
        self._abort_active_stream()
        self._reset_gen_buttons()
        self._stop_status_anim(self._tr("stopped"), "#eab308", 0.0)

    def _reset_gen_buttons(self):
        self._set_btn_enabled_with_cursor(self.btn_go, True)
        self.btn_stop.hide()
        self._refresh_button_icons()

    # --- TTS ---
    @staticmethod
    def _split_tts_sentences(text, max_len=180):
        raw_parts = re.split(r"(?<=[.!?;\n])\s+", text)
        chunks = []
        for part in raw_parts:
            part = part.strip()
            if not part:
                continue
            while len(part) > max_len:
                cut = part.rfind(" ", 0, max_len)
                if cut <= 0:
                    cut = max_len
                chunks.append(part[:cut].strip())
                part = part[cut:].strip()
            if part:
                chunks.append(part)
        return chunks if chunks else [text[:max_len]]

    @staticmethod
    def _fetch_tts_mp3_bytes(chunk, tl_code):
        url = (
            "https://translate.googleapis.com/translate_tts"
            f"?ie=UTF-8&client=gtx&tl={urllib.parse.quote(tl_code)}&q={urllib.parse.quote(chunk)}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://translate.google.com/"
            }
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read()
        return data if (data and len(data) >= 256) else None

    def toggle_tts(self):
        if self._is_speaking:
            self.stop_tts(show_status=True)
            return

        text_to_speak = self._extract_clean_main_output()
        if not text_to_speak:
            self._stop_status_anim(self._tr("tts_empty"), "#eab308", 0.0)
            return

        clean_speech = re.sub(r"[*_`~+#>]", "", text_to_speak).strip()
        if not clean_speech:
            return

        tgt_canon = self._get_effective_tgt_lang() or "English"
        tl_code = TTS_LANG_CODE_MAP.get(tgt_canon, "en")
        bcp47 = TTS_BCP47_MAP.get(tgt_canon, "en-US")

        self._tts_stop_event.clear()
        self._is_speaking = True
        self.btn_tts.setObjectName("AccentBtn")
        self.btn_tts.style().unpolish(self.btn_tts)
        self.btn_tts.style().polish(self.btn_tts)
        self._refresh_button_icons()
        self._stop_status_anim(self._tr("tts_speaking"), "#3b82f6", 1.0)

        def tts_worker():
            played_online = False
            tmp_mp3 = os.path.join(tempfile.gettempdir(), f"llm_tts_{os.getpid()}.mp3")
            try:
                sentences = self._split_tts_sentences(clean_speech, max_len=180)
                audio_buffers = [None] * len(sentences)
                ready_events = [threading.Event() for _ in sentences]

                def prefetch_idx(i, text_chunk):
                    try:
                        if not self._tts_stop_event.is_set():
                            audio_buffers[i] = self._fetch_tts_mp3_bytes(text_chunk, tl_code)
                    except Exception:
                        audio_buffers[i] = None
                    finally:
                        ready_events[i].set()

                for i, ch in enumerate(sentences):
                    threading.Thread(target=prefetch_idx, args=(i, ch), daemon=True).start()

                for i in range(len(sentences)):
                    if self._tts_stop_event.is_set():
                        break
                    ready_events[i].wait(timeout=3.5)
                    audio_bytes = audio_buffers[i]
                    if not audio_bytes:
                        break

                    with open(tmp_mp3, "wb") as f:
                        f.write(audio_bytes)

                    if IS_WIN:
                        ctypes.windll.winmm.mciSendStringW("close llm_tts", None, 0, 0)
                        short_p = get_win_short_path(tmp_mp3)
                        buf = ctypes.create_unicode_buffer(256)
                        rc = ctypes.windll.winmm.mciSendStringW(f'open "{short_p}" type mpegvideo alias llm_tts', buf, 256, 0)
                        if rc != 0:
                            break
                        ctypes.windll.winmm.mciSendStringW("setaudio llm_tts volume to 1000", None, 0, 0)
                        ctypes.windll.winmm.mciSendStringW("status llm_tts length", buf, 256, 0)
                        total_ms = int(buf.value) if buf.value.isdigit() else 0
                        if ctypes.windll.winmm.mciSendStringW("play llm_tts from 0", None, 0, 0) != 0:
                            ctypes.windll.winmm.mciSendStringW("close llm_tts", None, 0, 0)
                            break

                        played_online = True
                        start_t = time.monotonic()
                        max_wait = (total_ms / 1000.0 + 0.4) if total_ms > 0 else 15.0
                        while not self._tts_stop_event.is_set():
                            if time.monotonic() - start_t > max_wait:
                                break
                            ctypes.windll.winmm.mciSendStringW("status llm_tts position", buf, 256, 0)
                            if total_ms > 0 and buf.value.isdigit() and int(buf.value) >= total_ms - 35:
                                break
                            time.sleep(0.03)
                        ctypes.windll.winmm.mciSendStringW("close llm_tts", None, 0, 0)
                    elif IS_MAC:
                        played_online = True
                        proc = subprocess.Popen(["afplay", tmp_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        with self._tts_lock:
                            self._tts_proc = proc
                        while proc.poll() is None and not self._tts_stop_event.is_set():
                            time.sleep(0.03)
                        if proc.poll() is None:
                            proc.kill()
                    else:
                        for player in (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_mp3], ["mpg123", "-q", tmp_mp3]):
                            if shutil.which(player[0]):
                                played_online = True
                                proc = subprocess.Popen(player, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                with self._tts_lock:
                                    self._tts_proc = proc
                                while proc.poll() is None and not self._tts_stop_event.is_set():
                                    time.sleep(0.03)
                                if proc.poll() is None:
                                    proc.kill()
                                break
            except Exception:
                pass
            finally:
                if IS_WIN:
                    try:
                        ctypes.windll.winmm.mciSendStringW("close llm_tts", None, 0, 0)
                    except Exception:
                        pass
                if os.path.exists(tmp_mp3):
                    try:
                        os.remove(tmp_mp3)
                    except Exception:
                        pass

            if not played_online and not self._tts_stop_event.is_set():
                proc = None
                try:
                    if IS_WIN:
                        b64_orig = base64.b64encode(clean_speech.encode("utf-8")).decode("ascii")
                        phonetic_ru = transliterate_en_to_ru_phonetic(clean_speech)
                        b64_phon = base64.b64encode(phonetic_ru.encode("utf-8")).decode("ascii")
                        lang_prefix = bcp47.split("-")[0].lower()
                        ps_script = (
                            f"$orig = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{b64_orig}')); "
                            f"$phon = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{b64_phon}')); "
                            "Add-Type -AssemblyName System.Speech; "
                            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                            "$s.SetOutputToDefaultAudioDevice(); "
                            "$s.Volume = 100; "
                            "$matched = $false; "
                            "foreach ($v in $s.GetInstalledVoices()) { "
                            f"  if ($v.Enabled -and $v.VoiceInfo.Culture.Name.ToLower().StartsWith('{lang_prefix}')) {{ "
                            "    $s.SelectVoice($v.VoiceInfo.Name); $matched = $true; break "
                            "  } "
                            "} "
                            "if ($matched) { $s.Speak($orig) } "
                            "elseif ($s.Voice.Culture.Name.ToLower().StartsWith('ru') -and $orig -notmatch '[а-яА-ЯёЁ]') { $s.Speak($phon) } "
                            "else { $s.Speak($orig) }"
                        )
                        proc = subprocess.Popen(
                            ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_script],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        with self._tts_lock:
                            self._tts_proc = proc
                        while proc.poll() is None and not self._tts_stop_event.is_set():
                            time.sleep(0.04)
                        if proc.poll() is None:
                            proc.kill()
                    elif IS_MAC:
                        proc = subprocess.Popen(["say", clean_speech], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        with self._tts_lock:
                            self._tts_proc = proc
                        proc.wait()
                    else:
                        lang_short = bcp47.split("-")[0]
                        for cmd in (["spd-say", "-w", "-l", lang_short, clean_speech], ["espeak-ng", "-v", lang_short, clean_speech]):
                            if shutil.which(cmd[0]):
                                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                with self._tts_lock:
                                    self._tts_proc = proc
                                proc.wait()
                                break
                except Exception:
                    pass
                finally:
                    with self._tts_lock:
                        if self._tts_proc is proc:
                            self._tts_proc = None

            self.sig.ttsFinished.emit()

        threading.Thread(target=tts_worker, daemon=True).start()

    def _reset_tts_ui_after_finish(self):
        if not self._is_speaking:
            return
        self._is_speaking = False
        self.btn_tts.setObjectName("")
        self.btn_tts.style().unpolish(self.btn_tts)
        self.btn_tts.style().polish(self.btn_tts)
        self._refresh_button_icons()
        if not self._anim_running:
            if self._tw_final_status_msg:
                self._stop_status_anim(self._tw_final_status_msg, self._tw_final_status_color, 1.0)
            else:
                self._stop_status_anim(self._tr("done"), "#22c55e", 1.0)

    def stop_tts(self, show_status=False):
        self._tts_stop_event.set()
        if IS_WIN:
            try:
                ctypes.windll.winmm.mciSendStringW("close llm_tts", None, 0, 0)
            except Exception:
                pass
        with self._tts_lock:
            proc = self._tts_proc
            self._tts_proc = None
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
        if self._is_speaking:
            self._is_speaking = False
            self.btn_tts.setObjectName("")
            self.btn_tts.style().unpolish(self.btn_tts)
            self.btn_tts.style().polish(self.btn_tts)
            self._refresh_button_icons()
            if show_status and not self._anim_running:
                self._stop_status_anim(self._tr("tts_stopped"), "#eab308", 0.0)

    # --- Text Processing & Parsing ---
    def _normalize_lang_name(self, raw_lang):
        if not raw_lang:
            return None
        clean = strip_flag_prefix(raw_lang).strip(" <>[].,:;\"'").lower()
        if not clean or clean in INVALID_LANG_PLACEHOLDERS or "language" in clean:
            return None
        for k in TARGET_LANGUAGES_EN:
            if k.lower() == clean:
                return k
        if clean in LANG_RU_TO_EN:
            return LANG_RU_TO_EN[clean]
        for k, (ru_name, aliases) in LANG_DATA.items():
            if k not in AUTO_MODES_CANON and (clean in k.lower() or clean == ru_name.lower() or clean in aliases.lower().split()):
                return k
        return raw_lang.strip(" <>[].,:;\"'").title()

    def _apply_detected_language_ui(self, detected_lang):
        norm = self._normalize_lang_name(detected_lang)
        if not norm:
            return None
        self.detected_src_lang = norm
        if self.auto_detect_mode:
            self.dd_src.set(self._format_auto_detect_display(self.auto_detect_mode, norm))
        self._update_swap_button_state()
        return norm

    def _clean_output_text(self, text, tgt_lang, src_text=""):
        text = RE_THINK_BLOCKS.sub("", text)
        text = RE_UNCLOSED_THINK.sub("", text)
        text = re.sub(r"<lang>[^<\n]{1,45}</?lang>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"</?lang>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^\s*<lang>[^\n]*$", "", text, flags=re.IGNORECASE)
        text = RE_SPECIAL_TOKENS.sub("", text)

        if tgt_lang not in CJK_LANGUAGES:
            text = RE_CJK_GARBAGE.sub("", text)
            text = re.sub(r"\n\s*[,.\s]+\s*$", "", text)

        if src_text:
            if not RE_EMOJI_CHARS.search(src_text):
                text = RE_EMOJI_CHARS.sub("", text)
            if "**" not in src_text and "__" not in src_text and "*" not in src_text:
                parts = re.split(r"(```[\s\S]*?```|`[^`\n]+`)", text)
                for idx_p in range(0, len(parts), 2):
                    parts[idx_p] = re.sub(r"\*{1,3}([^*\n]+?)\*{1,3}", r"\1", parts[idx_p])
                text = "".join(parts)

        return text.strip()

    def _parse_dict_response(self, raw_text, word):
        cleaned_raw = re.sub(r"</?[a-zA-Z]*$", "", raw_text).strip()
        if not cleaned_raw:
            return "", []

        input_word_low = re.sub(r"[*_`~+.,:;!?'\"()\[\]]", "", word).strip().lower()

        main_match = re.search(r"<main>\s*(.*?)\s*(?:</main>|<dict>|\n\s*\[|$)", cleaned_raw, flags=re.DOTALL | re.IGNORECASE)
        dict_match = re.search(r"<dict>\s*(.*?)\s*(?:</dict>|$)", cleaned_raw, flags=re.DOTALL | re.IGNORECASE)

        if main_match:
            main_raw = main_match.group(1).strip().rstrip(":.")
            if dict_match:
                dict_block = dict_match.group(1).strip()
            else:
                after_main = cleaned_raw[main_match.end():]
                dict_block = re.sub(r"</?(?:main|dict|lang)>", "", after_main, flags=re.IGNORECASE).strip()
        else:
            cleaned_no_tags = re.sub(r"</?(?:main|dict|lang)>", "", cleaned_raw, flags=re.IGNORECASE).strip()
            lines = [l.strip() for l in cleaned_no_tags.split("\n") if l.strip()]
            first_line = lines[0] if lines else ""
            if first_line.startswith("[") and "]" in first_line:
                main_raw = ""
                dict_block = "\n".join(lines)
            else:
                main_raw = first_line.rstrip(":.")
                dict_block = "\n".join(lines[1:]) if len(lines) > 1 else ""

        main_raw = re.sub(r"^(?:translation|перевод|main|основной перевод)\s*:\s*", "", main_raw, flags=re.IGNORECASE).strip()

        inline_br_in_main = re.search(r"(\[[^\[\]\n]{2,45}\].*)$", main_raw, flags=re.DOTALL)
        if inline_br_in_main:
            extra_dict = inline_br_in_main.group(1).strip()
            main_raw = main_raw[:inline_br_in_main.start()].strip().rstrip(",;:")
            dict_block = (extra_dict + "\n" + dict_block).strip()

        for sep in (" — ", " – ", " - ", ": "):
            if sep in main_raw:
                left_p, right_p = main_raw.split(sep, 1)
                if left_p.strip().lower() == input_word_low and right_p.strip():
                    main_raw = right_p.strip()
                    break

        overflow_syns = []
        if ("," in main_raw or ";" in main_raw) and len(word.split()) <= 2:
            parts = [p.strip().rstrip(":") for p in re.split(r"[,;]", main_raw) if p.strip()]
            main_word = parts[0] if parts else main_raw
            overflow_syns = parts[1:]
        else:
            main_word = main_raw

        if dict_block.strip().lower() in ("none", "нет", "-", "n/a", "null", "empty"):
            dict_block = ""

        if dict_block:
            dict_block = re.sub(r"(?<!^)\s*(\[[^\[\]\n]{2,45}\])", r"\n\1", dict_block)

        sections = []
        for line in dict_block.split("\n"):
            clean_line = line.replace("**", "").replace("##", "").lstrip("-•* ").strip()
            if not clean_line or clean_line.lower() in ("none", "нет", "n/a"):
                continue
            if re.match(r"^(?:варианты перевода(?: и идиомы| и фразеологизмы)?|translations?(?: & idioms)?|dictionary|словарь)\s*:?\s*$", clean_line, flags=re.IGNORECASE):
                continue

            bracket_m = re.match(r"^\[(.*?)\]\s*:?\s*(.*)$", clean_line)
            if bracket_m:
                pos_name = bracket_m.group(1).strip().rstrip(":")
                syns_str = bracket_m.group(2).strip().rstrip(":")
                if syns_str.lower() not in ("none", "нет", "-", "n/a"):
                    sections.append((pos_name, [syns_str] if syns_str else []))
                continue

            if ":" in clean_line:
                pos_part, syn_part = clean_line.split(":", 1)
                pos_part = pos_part.strip().rstrip(":")
                syn_part = syn_part.strip().rstrip(":")
                if syn_part.lower() in ("none", "нет", "-", "n/a"):
                    continue
                if pos_part and len(pos_part) <= 42 and syn_part:
                    sections.append((pos_part, [syn_part]))
                    continue
                elif pos_part and len(pos_part) <= 42 and not syn_part:
                    sections.append((pos_part, []))
                    continue

            if sections:
                sections[-1][1].append(clean_line.rstrip(":"))
            else:
                sections.append((None, [clean_line.rstrip(":")]))

        if overflow_syns:
            overflow_str = ", ".join(overflow_syns)
            if sections:
                sections[0][1].insert(0, overflow_str)
            else:
                sections.append((None, [overflow_str]))

        valid_sections = []
        seen_headers = set()
        forbidden_meta = {"grammatical", "translation", "none"}

        for pos_h, syns_list in sections:
            h_low = (pos_h or "").lower()
            is_idiom_or_native_sec = any(
                k in h_low for k in (
                    "фразеологизм", "идиом", "idiom", "phras", "устойчив",
                    "выражени", "сленг", "slang", "исконн", "native", "значени", "meaning", "аналог"
                )
            )
            filtered_syns = []
            seen_words = {main_word.lower(), input_word_low}

            for s_line in syns_list:
                s_line_clean = re.sub(r"\[[^\[\]]*\]", "", s_line).strip()
                if not s_line_clean:
                    continue

                if is_idiom_or_native_sec:
                    idiom_items = []
                    for item in re.split(r"[;,]", s_line_clean) if ";" not in s_line_clean else s_line_clean.split(";"):
                        cl = item.strip().rstrip(".")
                        cl_low = cl.lower()
                        if cl and cl_low not in seen_words and cl_low not in ("none", "нет", "-"):
                            seen_words.add(cl_low)
                            idiom_items.append(cl)
                    if idiom_items:
                        sep_join = "; " if "—" in s_line_clean or "-" in s_line_clean else ", "
                        filtered_syns.append(sep_join.join(idiom_items))
                else:
                    items = []
                    for item in re.split(r"[,;]", s_line_clean):
                        cl = re.sub(r"\(.*?\)", "", item).strip().rstrip(":.")
                        cl_low = cl.lower()
                        if (
                            cl and cl_low not in seen_words
                            and "synonym" not in cl_low
                            and not any(fm in cl_low for fm in forbidden_meta)
                        ):
                            seen_words.add(cl_low)
                            items.append(cl)
                    if items:
                        filtered_syns.append(", ".join(items))

            if filtered_syns:
                if h_low and h_low in seen_headers:
                    for ex_h, ex_list in valid_sections:
                        if (ex_h or "").lower() == h_low:
                            ex_list.extend(filtered_syns)
                            break
                else:
                    if h_low:
                        seen_headers.add(h_low)
                    valid_sections.append((pos_h, filtered_syns))

        clean_main_cmp = re.sub(r"[*_`~+.,:;!?'\"()\[\]]", "", main_word).strip().lower()
        if (not clean_main_cmp or clean_main_cmp == input_word_low) and valid_sections:
            first_line_str = valid_sections[0][1][0]
            first_cand = re.split(r"[,;—–-]", first_line_str)[0].strip()
            if first_cand and first_cand.lower() != input_word_low:
                main_word = first_cand

        return main_word, valid_sections

    def _is_dict_output_broken(self, cleaned_text, input_word, tgt_lang):
        if not cleaned_text:
            return True
        main_word, _ = self._parse_dict_response(cleaned_text, input_word)
        clean_cand = re.sub(r"[*_`~+.,:;!?'\"()\[\]]", "", main_word).strip().lower()
        clean_inp = re.sub(r"[*_`~+.,:;!?'\"()\[\]]", "", input_word).strip().lower()
        if not clean_cand or clean_cand == clean_inp:
            return True
        if tgt_lang in CYRILLIC_LANGUAGES and not RE_CYRILLIC_CHARS.search(clean_cand):
            return True
        return False

    def _split_into_chunks(self, text, max_chars=1800):
        if len(text) <= max_chars:
            return [text]
        paragraphs = text.split("\n")
        chunks, current = [], ""
        for p in paragraphs:
            if len(current) + len(p) + 1 <= max_chars:
                current += (p + "\n")
            else:
                if current:
                    chunks.append(current.rstrip("\n"))
                current = p + "\n"
        if current:
            chunks.append(current.rstrip("\n"))
        return chunks

    def _show_instant_mismatch_banner(self, task_id, mismatch_warning):
        if task_id != self._task_id or not mismatch_warning:
            return
        self._tw_mismatch_warning = mismatch_warning
        if not self._tw_running and not self._tw_main_target:
            self._render_phased_output("", [], self._tw_is_dict_mode, self._tw_word, mismatch_warning, dict_pending=False)

    def _start_or_update_typewriter(self, task_id, target_text, is_dict_mode, word, mismatch_warning, tok_speed, stream_finished=False, final_msg="", final_color="#22c55e"):
        if task_id != self._task_id:
            return
        self._tw_task_id = task_id
        self._tw_target_text = target_text
        self._tw_is_dict_mode = is_dict_mode
        self._tw_word = word
        if mismatch_warning:
            self._tw_mismatch_warning = mismatch_warning

        if is_dict_mode:
            main_w, valid_secs = self._parse_dict_response(target_text, word)
            self._tw_main_target = main_w
            self._tw_dict_sections = valid_secs
        else:
            cleaned_main = re.sub(r"</?[a-zA-Z]*$", "", target_text).strip()
            self._tw_main_target = cleaned_main
            self._tw_dict_sections = []

        if self._tw_displayed_chars > len(self._tw_main_target):
            self._tw_displayed_chars = float(len(self._tw_main_target))

        if tok_speed > 0:
            self._tw_tok_speed = tok_speed
        self._tw_stream_finished = stream_finished
        if final_msg:
            self._tw_final_status_msg = final_msg
            self._tw_final_status_color = final_color

        self._tw_running = True

    def skip_typewriter_animation(self):
        if not self._tw_main_target and not self._tw_target_text:
            self.btn_instant.hide()
            return
        self._tw_displayed_chars = float(len(self._tw_main_target))
        self.btn_instant.hide()
        self._render_phased_output(
            self._tw_main_target,
            self._tw_dict_sections if self._tw_stream_finished else [],
            self._tw_is_dict_mode,
            self._tw_word,
            self._tw_mismatch_warning,
            dict_pending=(self._tw_is_dict_mode and not self._tw_stream_finished)
        )
        if self._tw_stream_finished:
            self._tw_running = False
            if self._tw_final_status_msg:
                self._stop_status_anim(self._tw_final_status_msg, self._tw_final_status_color, 1.0)

    def _typewriter_tick(self):
        if not self._tw_running or self._tw_task_id != self._task_id:
            if self.btn_instant.isVisible():
                self.btn_instant.hide()
            return

        total_main_len = len(self._tw_main_target)
        cur_len = int(self._tw_displayed_chars)

        if cur_len < total_main_len:
            if total_main_len <= 35:
                chars_per_sec = 42.0
            elif total_main_len <= 140:
                chars_per_sec = 75.0
            else:
                chars_per_sec = max(95.0, min(self._tw_tok_speed * 2.8, 250.0))

            step = max(1.0, chars_per_sec * 0.025)
            self._tw_displayed_chars = min(float(total_main_len), self._tw_displayed_chars + step)
            new_len = int(self._tw_displayed_chars)

            partial_main = self._tw_main_target[:new_len]
            main_done_now = (new_len >= total_main_len)
            show_dict_now = (main_done_now and self._tw_stream_finished)
            show_pending_dots = (self._tw_is_dict_mode and main_done_now and not self._tw_stream_finished)

            self._dict_dots_step += 1
            self._render_phased_output(
                partial_main,
                self._tw_dict_sections if show_dict_now else [],
                self._tw_is_dict_mode,
                self._tw_word,
                self._tw_mismatch_warning,
                dict_pending=show_pending_dots
            )

            remaining = total_main_len - new_len
            if (self._tw_stream_finished and remaining > 8) or remaining > 45:
                self.btn_instant.show()
                self.btn_instant.raise_()
            else:
                self.btn_instant.hide()
        else:
            self.btn_instant.hide()
            if self._tw_stream_finished:
                self._tw_running = False
                self._render_phased_output(
                    self._tw_main_target,
                    self._tw_dict_sections,
                    self._tw_is_dict_mode,
                    self._tw_word,
                    self._tw_mismatch_warning,
                    dict_pending=False
                )
                if self._tw_final_status_msg:
                    self._stop_status_anim(self._tw_final_status_msg, self._tw_final_status_color, 1.0)
            else:
                self._dict_dots_step += 1
                self._render_phased_output(
                    self._tw_main_target,
                    [],
                    self._tw_is_dict_mode,
                    self._tw_word,
                    self._tw_mismatch_warning,
                    dict_pending=self._tw_is_dict_mode
                )

    def _render_direct_text(self, text):
        self.t_out.setPlainText(text)

    def _format_inline_md_html(self, line):
        esc = html.escape(line)
        esc = re.sub(
            r"`([^`\n]+)`",
            rf"<code style='background:{THEME['code_bg']};color:{THEME['code_fg']};font-family:{MONO_FONT};padding:1px 4px;'>\1</code>",
            esc
        )
        esc = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<b><i>\1</i></b>", esc)
        esc = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", esc)
        esc = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", esc)
        esc = re.sub(r"~~([^~]+)~~", r"<s>\1</s>", esc)
        return esc

    def _md_to_html(self, text):
        segments = re.split(r"(```[\s\S]*?```)", text)
        out_parts = []
        for seg in segments:
            if not seg:
                continue
            if seg.startswith("```") and seg.endswith("```") and len(seg) >= 6:
                inner = seg[3:-3]
                lang_label = ""
                if "\n" in inner:
                    first_ln, rest_code = inner.split("\n", 1)
                    if re.match(r"^[a-zA-Z0-9_+\-#]{1,18}$", first_ln.strip()):
                        lang_label = first_ln.strip().upper()
                        inner = rest_code
                inner = html.escape(inner.strip("\r\n"))
                hdr = f"<div style='color:{THEME['text_muted']};font-size:10px;font-weight:bold;'>{lang_label}</div>" if lang_label else ""
                out_parts.append(
                    f"<div style='background:{THEME['codeblock_bg']};color:{THEME['codeblock_fg']};"
                    f"font-family:{MONO_FONT};font-size:13px;padding:8px;margin:4px 0;white-space:pre-wrap;'>"
                    f"{hdr}{inner}</div>"
                )
            else:
                lines_html = []
                for ln in seg.split("\n"):
                    h_m = re.match(r"^#{1,3}\s+(.+)$", ln)
                    q_m = re.match(r"^>\s+(.+)$", ln)
                    if h_m:
                        lines_html.append(f"<span style='font-size:17px;font-weight:bold;color:{THEME['border_focus']};'>{self._format_inline_md_html(h_m.group(1))}</span>")
                    elif q_m:
                        lines_html.append(f"<span style='color:{THEME['text_muted']};font-style:italic;'>▎ {self._format_inline_md_html(q_m.group(1))}</span>")
                    else:
                        lines_html.append(self._format_inline_md_html(ln))
                out_parts.append("<br>".join(lines_html))
        return "".join(out_parts)

    def _render_phased_output(self, main_text_part, dict_sections_to_show, is_dict_mode, word="", mismatch_warning="", dict_pending=False):
        sb = self.t_out.verticalScrollBar()
        old_scroll = sb.value()
        base_px = max(10, int(round(15 * (self.ui_scale / 100.0))))

        blocks = []
        if mismatch_warning:
            blocks.append(f"<div style='color:#f59e0b;font-weight:bold;margin-bottom:10px;'>{html.escape(mismatch_warning)}</div>")

        if main_text_part:
            self._last_clean_translation = main_text_part
            blocks.append(f"<div style='color:{THEME['text_main']};font-size:{base_px}px;'>{self._md_to_html(main_text_part)}</div>")

        if is_dict_mode:
            if dict_sections_to_show:
                blocks.append(f"<div style='margin-top:14px;color:{THEME['text_muted']};font-style:italic;font-size:{max(9, base_px - 2)}px;'>{html.escape(word)} — {html.escape(self._tr('dict_variants'))}</div>")
                for pos_h, syns_list in dict_sections_to_show:
                    if pos_h:
                        loc_h = self._translate_pos_header(pos_h)
                        h_low = loc_h.lower()
                        if any(k in h_low for k in ("исконн", "native", "значени", "meaning", "аналог")):
                            col = "#10b981"
                        elif any(k in h_low for k in ("фразеологизм", "идиом", "idiom", "phras")):
                            col = "#a855f7"
                        else:
                            col = THEME["border_focus"]
                        blocks.append(f"<div style='margin-top:8px;color:{col};font-weight:bold;font-size:{max(10, base_px - 1)}px;'>{html.escape(loc_h)}</div>")
                    for s_line in syns_list:
                        blocks.append(f"<div style='margin-left:14px;color:{THEME['text_main']};font-size:{max(9, base_px - 2)}px;'>{html.escape(s_line)}</div>")
            elif dict_pending and main_text_part:
                wave_frames = ["•  ·  ·", "·  •  ·", "·  ·  •", "·  •  ·"]
                dots = wave_frames[self._dict_dots_step % len(wave_frames)]
                blocks.append(f"<div style='margin-top:14px;color:{THEME['text_muted']};font-style:italic;font-size:{max(9, base_px - 2)}px;'>{html.escape(word)} — {html.escape(self._tr('dict_variants'))}</div>")
                blocks.append(f"<div style='margin-top:6px;color:{THEME['border_focus']};font-weight:bold;font-size:{base_px + 1}px;'>{dots}</div>")

        self.t_out.setHtml("".join(blocks))
        if self._tw_running:
            sb.setValue(sb.maximum())
        else:
            sb.setValue(old_scroll)

    # --- Prompts & OpenAI API ---
    def _build_prompts(self, text, src_mode, tgt_lang, is_dict_mode):
        has_emojis = bool(RE_EMOJI_CHARS.search(text))
        emoji_rule = (
            "Preserve any emojis/emoticons from the input in their exact contextual places."
            if has_emojis else
            "STRICT EMOJI BAN: The input contains NO emojis. NEVER add or invent emojis/emoticons."
        )
        src_hint = f"from {src_mode} " if src_mode and src_mode not in AUTO_MODES_CANON else ""
        cat_lang = "Russian" if self.ui_lang == "ru" else "English"
        idiom_header = "[фразеологизмы и идиомы]" if self.ui_lang == "ru" else "[idioms & phrases]"
        native_header = "[исконные аналоги / значение]" if self.ui_lang == "ru" else "[native equivalents / meaning]"

        lang_detect_instruction = (
            "Identify the TRUE language of the source text by its vocabulary and grammar (NOT just the alphabet! "
            "For example: 'In principio creavit Deus caelum et terram' is Latin -> <lang>Latin</lang>; "
            "'Bonjour le monde' is French -> <lang>French</lang>; 'Hello world' is English -> <lang>English</lang>)."
        )

        if is_dict_mode:
            sys_prompt = (
                f"You are an authoritative bilingual translator, lexicographer, and etymology/slang expert translating {src_hint}into {tgt_lang}.\n"
                f"STRICT RULES:\n"
                f"1. Line 1: {lang_detect_instruction} Output the language name in English inside <lang>...</lang>.\n"
                f"2. Line 2: Inside <main>...</main>, output ONLY the single best, most natural translation in {tgt_lang}. NEVER repeat the untranslated source word inside <main>!\n"
                f"3. Inside <dict>...</dict>, put EVERY category on its OWN NEW LINE starting with `[Category Name]` in {cat_lang}. Include {native_header} if slang/loanword, and {idiom_header} ONLY if genuine idioms exist. Leave <dict></dict> empty if no variants are needed.\n"
                f"4. {emoji_rule}"
            )
            user_instruction = (
                f"Translate \"{text}\" {src_hint}into {tgt_lang}:\n"
                f"<lang>TrueLanguageInEnglish</lang>\n"
                f"<main>Best translation in {tgt_lang}</main>\n"
                f"<dict>\n"
                f"[Part of speech in {cat_lang}] synonym 1, synonym 2\n"
                f"</dict>"
            )
            return sys_prompt, [user_instruction]

        has_md = bool(RE_MD_TOKEN.search(text) or re.search(r"(?:^|\n)(?:#{1,3}|>)\s+", text))
        md_rule = (
            f"3. MARKDOWN & CODE BLOCKS: Preserve existing formatting markers (`inline code`, ```code blocks```, **bold**, *italic*, # headers, > quotes). "
            f"Inside code blocks, keep syntax intact and translate only string literals/comments into {tgt_lang}."
            if has_md else
            "3. STRICT PLAIN TEXT: The source text has NO bold or italic formatting. NEVER add **bold** or *italic* asterisks. Output clean plain text."
        )

        lang_rule = (
            f"1. LANGUAGE DETECTION: {lang_detect_instruction} Output `<lang>TrueLanguageInEnglish</lang>` on line 1, then immediately translate the text into {tgt_lang}."
        )

        raw_chunks = self._split_into_chunks(text, max_chars=1800)
        chunks = [
            f"Translate the text inside <source_text> {src_hint}into {tgt_lang}. Every sentence must be translated:\n"
            f"<source_text>\n{c}\n</source_text>"
            for c in raw_chunks
        ]

        sys_prompt = (
            f"You are an elite literary and technical translator translating {src_hint}into {tgt_lang}.\n"
            f"CRITICAL RULES:\n"
            f"{lang_rule}\n"
            f"2. 100% PURE {tgt_lang.upper()} TRANSLATION: Translate accurately and idiomatically into {tgt_lang}.\n"
            f"{md_rule}\n"
            f"4. EMOJI POLICY: {emoji_rule}\n"
            f"5. Output ONLY `<lang>...</lang>` on line 1 followed by the translation in {tgt_lang}."
        )
        if self.enable_thinking:
            sys_prompt += "\n6. THINKING MODE ENABLED: Reason briefly inside <think>...</think> before outputting <lang>...</lang> and the translation."
        else:
            sys_prompt += "\n6. DIRECT OUTPUT: Do NOT output <think> tags. Start immediately with <lang>...</lang> and the translation."

        return sys_prompt, chunks

    def _build_vision_prompts(self, extra_text, src_mode, tgt_lang):
        src_hint = f"from {src_mode} " if src_mode and src_mode not in AUTO_MODES_CANON else ""
        sys_prompt = (
            f"You are an elite OCR and visual localization translator into {tgt_lang}.\n"
            f"CRITICAL RULES:\n"
            f"1. LANGUAGE DETECTION: On line 1, output the true detected source language of the image text in English inside <lang>...</lang> tags (distinguish Latin, English, French, Spanish, etc. by vocabulary).\n"
            f"2. ACCURATE OCR & TRANSLATION: Read all visible text in the image and translate it accurately {src_hint}into pure {tgt_lang}.\n"
            f"3. Output ONLY <lang>...</lang> on line 1 followed immediately by the translated text. Do not describe the image."
        )
        user_instr = f"Extract and translate all text from this image {src_hint}into {tgt_lang}."
        if extra_text:
            user_instr += f"\nAdditional context:\n{extra_text}"
        if not self.enable_thinking:
            sys_prompt += "\n4. DIRECT OUTPUT: Do NOT output <think> blocks."
        return sys_prompt, [user_instr]

    def _create_chat_completion_universal(self, model_name, sys_prompt, user_payload, stream=True, temperature=0.0, image_b64=""):
        if image_b64:
            user_content = [
                {"type": "text", "text": user_payload},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        else:
            user_content = user_payload

        messages_std = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_content}
        ]
        stop_tokens = ["</source_text>", "<|im_end|>", "<|eot_id|>", "<|END_OF_TURN_TOKEN|>"]
        reasoning_effort = "medium" if self.enable_thinking else "none"

        try:
            return self.client.chat.completions.create(
                model=model_name,
                messages=messages_std,
                stream=stream,
                temperature=temperature,
                top_p=0.85,
                frequency_penalty=0.05,
                presence_penalty=0.0,
                stop=stop_tokens,
                extra_body={"reasoning_effort": reasoning_effort}
            )
        except Exception as e1:
            err_str = str(e1).lower()
            if any(k in err_str for k in ("reasoning", "extra", "unrecognized", "400", "system")):
                try:
                    return self.client.chat.completions.create(
                        model=model_name,
                        messages=messages_std,
                        stream=stream,
                        temperature=temperature,
                        stop=stop_tokens
                    )
                except Exception:
                    pass

            if image_b64:
                merged_content = [
                    {"type": "text", "text": f"{sys_prompt}\n\n{user_payload}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            else:
                merged_content = f"{sys_prompt}\n\n{user_payload}"
            return self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": merged_content}],
                stream=stream,
                temperature=temperature
            )

    def start_translation(self):
        text = self.t_in.toPlainText().strip()
        image_b64 = self._attached_image_b64
        has_img = bool(image_b64)
        tgt_lang = self._get_effective_tgt_lang()
        if (not text and not has_img) or not tgt_lang:
            return

        if has_img:
            active_model = self._resolve_effective_vision_model()
            if not active_model:
                self._stop_status_anim(self._tr("no_vision_err"), "#ef4444", 0.0)
                return
            self._update_image_banner_ui()
        else:
            if not self._is_valid_model_selected():
                return
            active_model = strip_loaded_prefix(self.model_id)

        self._abort_active_stream()
        self.stop_tts()
        current_task = self._task_id

        self._tw_task_id = current_task
        self._tw_target_text = ""
        self._tw_main_target = ""
        self._tw_dict_sections = []
        self._tw_mismatch_warning = ""
        self._tw_mismatch_langs = None
        self._tw_displayed_chars = 0.0
        self._tw_stream_finished = False
        self._tw_final_status_msg = ""
        self._tw_running = False
        self._dict_dots_step = 0
        self.t_out.clear()

        self._set_btn_enabled_with_cursor(self.btn_go, False)
        self.btn_stop.show()
        self._refresh_button_icons()

        src_mode = self._get_effective_src_mode()
        fast_guessed_lang = None
        if self.auto_detect_mode == "fast" and text:
            fast_guessed_lang = fast_detect_language_by_script(text)
            if fast_guessed_lang:
                self._apply_detected_language_ui(fast_guessed_lang)

        if active_model not in self._loaded_vram_models:
            self._start_status_anim(f"{self._tr('loading_vram')}: {active_model}", "#eab308")
        elif has_img:
            self._start_status_anim(self._tr("img_translating"), "#3b82f6")
        else:
            self._start_status_anim(self._tr("translating"), "#3b82f6")

        plain_probe = re.sub(r"[*_`~+]", "", text).strip()
        words = plain_probe.split()
        is_dict_mode = (
            (not has_img)
            and 1 <= len(words) <= 6
            and len(plain_probe) <= 65
            and "\n" not in plain_probe
            and not any(plain_probe.endswith(p) for p in (".", "!", "?", ";", ":"))
        )
        self._tw_is_dict_mode = is_dict_mode
        self._tw_word = plain_probe

        effective_prompt_src = fast_guessed_lang if (self.auto_detect_mode == "fast" and fast_guessed_lang) else src_mode
        if has_img:
            sys_prompt, chunks = self._build_vision_prompts(text, effective_prompt_src, tgt_lang)
        else:
            sys_prompt, chunks = self._build_prompts(text, effective_prompt_src, tgt_lang, is_dict_mode)

        def ai_worker():
            local_stream = None
            completed_chunks_text = ""
            try:
                if active_model not in self._loaded_vram_models:
                    self.sig.statusAnimPhase.emit(f"{self._tr('loading_vram')}: {active_model}", "#eab308")
                    self._ensure_model_loaded_in_vram(active_model, unload_others=True)
                    if self._task_id != current_task:
                        return
                    self.sig.statusAnimPhase.emit(
                        self._tr("img_translating") if has_img else self._tr("translating"),
                        "#3b82f6"
                    )

                total_tokens = 0
                gen_start_ts = None
                detected_lang_final = fast_guessed_lang
                mismatch_banner = ""

                for idx, payload in enumerate(chunks):
                    if self._task_id != current_task:
                        return

                    local_stream = self._create_chat_completion_universal(
                        active_model, sys_prompt, payload, stream=True, temperature=0.0,
                        image_b64=(image_b64 if has_img else "")
                    )
                    with self._stream_lock:
                        self._active_stream = local_stream

                    chunk_accumulated = ""
                    try:
                        for part in local_stream:
                            if self._task_id != current_task:
                                return
                            delta = part.choices[0].delta if (part.choices and len(part.choices) > 0) else None
                            if delta is None:
                                continue

                            content_piece = getattr(delta, "content", None) or ""
                            reasoning_piece = getattr(delta, "reasoning_content", None) or ""

                            if content_piece or reasoning_piece:
                                now_ts = time.monotonic()
                                if gen_start_ts is None:
                                    gen_start_ts = now_ts
                                    if active_model not in self._loaded_vram_models:
                                        self._loaded_vram_models.add(active_model)
                                        self.sig.refreshModelLabels.emit()

                                total_tokens += 1
                                chunk_accumulated += content_piece

                                elapsed_so_far = max(now_ts - gen_start_ts, 0.05)
                                live_speed = total_tokens / elapsed_so_far

                                in_think = bool(reasoning_piece and not content_piece) or (
                                    ("<think>" in chunk_accumulated or "<thought>" in chunk_accumulated)
                                    and not ("</think>" in chunk_accumulated or "</thought>" in chunk_accumulated)
                                )
                                if in_think:
                                    self.sig.statusAnimPhase.emit(f"{self._tr('thinking')} ({live_speed:.0f} tok/s)", "#a855f7")
                                else:
                                    self.sig.statusAnimPhase.emit(f"{self._tr('typing')} ({live_speed:.0f} tok/s)", "#3b82f6")

                                if detected_lang_final is None and idx == 0:
                                    lang_m = re.search(r"<lang>\s*([^<\n]{1,40}?)\s*</?lang>", chunk_accumulated, flags=re.IGNORECASE)
                                    if lang_m:
                                        raw_det = lang_m.group(1).strip()
                                        detected_lang_final = self._normalize_lang_name(raw_det)
                                        if detected_lang_final:
                                            self.sig.detectedLangUpdated.emit(detected_lang_final)
                                            if not self.auto_detect_mode and src_mode.lower() != detected_lang_final.lower():
                                                self._tw_mismatch_langs = (src_mode, detected_lang_final)
                                                mismatch_banner, _ = self._build_mismatch_texts(src_mode, detected_lang_final)
                                                self.sig.mismatchBannerShown.emit(current_task, mismatch_banner)

                                live_clean = self._clean_output_text(chunk_accumulated, tgt_lang, src_text=text)
                                if live_clean:
                                    full_preview = (completed_chunks_text + "\n\n" + live_clean).strip() if completed_chunks_text else live_clean
                                    self.sig.typewriterUpdated.emit(
                                        current_task, full_preview, is_dict_mode, plain_probe,
                                        mismatch_banner, live_speed, False, "", "#22c55e"
                                    )
                    except Exception:
                        if not chunk_accumulated:
                            raise

                    cleaned_final = self._clean_output_text(chunk_accumulated, tgt_lang, src_text=text)

                    if is_dict_mode and self._task_id == current_task and self._is_dict_output_broken(cleaned_final, plain_probe, tgt_lang):
                        self.sig.statusAnimPhase.emit(self._tr("polishing"), "#a855f7")
                        retry_prompt = (
                            f"Translate \"{plain_probe}\" into {tgt_lang}. "
                            f"Output:\n<main>best translation in {tgt_lang}</main>\n<dict></dict>"
                        )
                        retry_res = self._create_chat_completion_universal(
                            active_model, "You are a strict bilingual dictionary.", retry_prompt, stream=False, temperature=0.1
                        )
                        if retry_res and retry_res.choices and retry_res.choices[0].message.content:
                            cand_retry = self._clean_output_text(retry_res.choices[0].message.content, tgt_lang, src_text=text)
                            if not self._is_dict_output_broken(cand_retry, plain_probe, tgt_lang):
                                cleaned_final = cand_retry

                    if not is_dict_mode and not has_img and self._task_id == current_task:
                        raw_chunk_src = re.sub(r"^.*?<source_text>\s*", "", payload, flags=re.DOTALL).replace("</source_text>", "").strip()
                        unchanged_echo = (
                            not cleaned_final
                            or cleaned_final.strip().lower() == raw_chunk_src.strip().lower()
                            or (tgt_lang in CYRILLIC_LANGUAGES and not RE_CYRILLIC_CHARS.search(cleaned_final) and len(raw_chunk_src) > 3)
                        )
                        if unchanged_echo:
                            self.sig.statusAnimPhase.emit(self._tr("polishing"), "#a855f7")
                            direct_sys = f"Translate the user's text accurately into {tgt_lang}. Output ONLY the translation."
                            direct_res = self._create_chat_completion_universal(
                                active_model, direct_sys, raw_chunk_src, stream=False, temperature=0.1
                            )
                            if direct_res and direct_res.choices and direct_res.choices[0].message.content:
                                cand_direct = self._clean_output_text(direct_res.choices[0].message.content, tgt_lang, src_text=text)
                                if cand_direct:
                                    cleaned_final = cand_direct

                    completed_chunks_text = (completed_chunks_text + "\n\n" + cleaned_final).strip() if completed_chunks_text else cleaned_final

                if self._task_id == current_task:
                    elapsed_gen = max((time.monotonic() - (gen_start_ts or time.monotonic())), 0.05)
                    speed = total_tokens / elapsed_gen if gen_start_ts else 25.0
                    if self._tw_mismatch_langs:
                        mismatch_banner, final_msg = self._build_mismatch_texts(*self._tw_mismatch_langs)
                        final_col = "#f59e0b"
                    else:
                        final_msg = f"{self._tr('done')} ({speed:.0f} tok/s)" if speed > 1 else self._tr("done")
                        final_col = "#22c55e"

                    self.sig.typewriterUpdated.emit(
                        current_task, completed_chunks_text, is_dict_mode, plain_probe,
                        mismatch_banner, speed, True, final_msg, final_col
                    )

            except Exception as e:
                if self._task_id != current_task:
                    return
                if completed_chunks_text:
                    self.sig.typewriterUpdated.emit(
                        current_task, completed_chunks_text, is_dict_mode, plain_probe,
                        "", 25.0, True, self._tr("done"), "#22c55e"
                    )
                    return
                err_msg = str(e)
                err_low = err_msg.lower()
                if any(k in err_low for k in ("connection", "refused", "connecterror", "timed out", "unreachable")):
                    self._is_online = False
                    QTimer.singleShot(0, self._sync_server_button_visibility)
                    QTimer.singleShot(0, self._sync_vram_button_visibility)
                self.sig.renderDirectOutput.emit(f"{self._tr('api_err')}:\n{err_msg}")
                self.sig.statusAnimStop.emit(self._tr("conn_err"), "#ef4444", 0.0)
            finally:
                if local_stream is not None:
                    try:
                        local_stream.close()
                    except Exception:
                        pass
                if self._task_id == current_task:
                    with self._stream_lock:
                        self._active_stream = None
                    self.sig.resetGenerationButtons.emit()

        threading.Thread(target=ai_worker, daemon=True).start()

    def closeEvent(self, event):
        self._save_config()
        self._abort_active_stream()
        self.stop_tts()
        if self._loaded_vram_models:
            self._set_status_raw(self._tr("vram_exit"), "#eab308")
            QApplication.processEvents()
            self._verified_unload_all_vram(timeout_per_step=5)
        event.accept()
        os._exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LLMTranslateWindow()
    win.show()
    sys.exit(app.exec())