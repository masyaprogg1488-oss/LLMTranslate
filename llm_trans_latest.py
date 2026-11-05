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
import tkinter as tk
import tkinter.font as tkfont

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import customtkinter as ctk
from openai import OpenAI

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

UI_FONT = "Segoe UI" if IS_WIN else ("SF Pro Display" if IS_MAC else "Sans")
MONO_FONT = "Consolas" if IS_WIN else ("Menlo" if IS_MAC else "Monospace")

if IS_WIN:
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
            new_mode = (mode.value & ~0x0040) | 0x0080
            kernel32.SetConsoleMode(h_stdin, new_mode)
    except Exception:
        pass
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("llm.translate.app.v13")
    except Exception:
        pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

THEME = {
    "bg_root": "#0f1117",
    "bg_card_in": "#161922",
    "bg_card_out": "#12151c",
    "bg_dd": "#171b24",
    "bg_dd_hover": "#1e2430",
    "bg_popup": "#151821",
    "bg_btn": "#1e232e",
    "bg_btn_hover": "#2a3140",
    "bg_accent": "#2563eb",
    "bg_accent_hover": "#1d4ed8",
    "bg_server": "#1e3a8a",
    "bg_server_online": "#172554",
    "bg_server_hover": "#2563eb",
    "bg_danger": "#3f1a20",
    "bg_danger_hover": "#7f1d1d",
    "border_subtle": "#262b38",
    "border_focus": "#3b82f6",
    "text_main": "#f3f4f6",
    "text_muted": "#9ca3af",
    "text_dim": "#6b7280",
}

LM_HOST, LM_PORT = "127.0.0.1", 1234
LOADED_PREFIX = "✓ "

if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

if IS_WIN:
    BASE_DIR = SCRIPT_DIR
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
    ICONS_DIR = os.path.join(BASE_DIR, "icons")
else:
    APP_CONFIG_DIR = os.path.expanduser("~/.config/llm-translate")
    APP_CACHE_DIR = os.path.expanduser("~/.cache/llm-translate")
    os.makedirs(APP_CONFIG_DIR, exist_ok=True)
    os.makedirs(APP_CACHE_DIR, exist_ok=True)
    BASE_DIR = APP_CONFIG_DIR
    CONFIG_PATH = os.path.join(APP_CONFIG_DIR, "config.json")
    ICONS_DIR = os.path.join(APP_CACHE_DIR, "icons")

FLAGS_DIR = os.path.join(ICONS_DIR, "flags")

UI_STRINGS = {
    "ru": {
        "tip_swap": "Поменять языки местами",
        "tip_tts": "Озвучить перевод",
        "tip_go": "Перевести (Ctrl+Enter)",
        "tip_stop": "Остановить перевод",
        "tip_auto_chk": "Авто. перевод при вводе текста",
        "tip_refresh": "Обновить список моделей LM Studio",
        "tip_server": "Запустить сервер LM Studio",
        "tip_load_model": "Загрузить модель",
        "tip_vram": "Очистить VRAM",
        "tip_settings": "Настройки",
        "splash_sub": "Локальный нейросетевой переводчик",
        "splash_init": "Инициализация...",
        "splash_env": "Подготовка графической среды...",
        "splash_tex": "Генерация встроенных ассетов...",
        "splash_ui": "Сборка главного окна...",
        "splash_cfg": "Чтение конфигурации config.json...",
        "splash_start": "Запуск приложения...",
        "auto_detect": "Автоопределение",
        "auto_short": "Авто",
        "select_lang": "Выберите язык...",
        "select_model": "Выберите модель...",
        "no_models": "Нет моделей в LM Studio",
        "offline_model": "LM Studio офлайн",
        "loading": "Загрузка...",
        "auto_trans_chk": "Автоперевод",
        "smart_search_sw": "Умный поиск",
        "settings_title": "Настройки приложения",
        "settings_pin": "Поверх всех окон",
        "settings_lang": "Язык программы",
        "server_btn": "Сервер",
        "instant_btn": "⚡ Ответить сразу",
        "connecting": "Подключение...",
        "ready": "● Готов",
        "choose_lang_right": "Выберите язык справа",
        "choose_model_bottom": "Выберите модель снизу",
        "copied": "✓ Скопировано",
        "copied_sel": "✓ Скопировано выделенное",
        "stopped": "⏹ Остановлено",
        "tts_speaking": "🔊 Озвучивание...",
        "tts_stopped": "⏹ Озвучка остановлена",
        "tts_empty": "Нет текста для озвучки",
        "model_reset": "Модель сброшена",
        "model_ready": "● Модель готова",
        "searching_lms": "Поиск LM Studio",
        "starting_server": "Запуск сервера LM Studio...",
        "server_started": "● Сервер запущен!",
        "server_failed": "✕ Включи Local Server (:1234)",
        "lms_online": "● LM Studio в сети",
        "vram_check": "Проверка и очистка VRAM",
        "vram_cleaned_all": "✓ VRAM полностью очищена",
        "vram_cleaned": "✓ VRAM очищена",
        "vram_already_empty": "✓ VRAM уже пуста",
        "vram_exit": "Очистка VRAM перед выходом...",
        "unloading": "Выгрузка",
        "loading_vram": "Загрузка в VRAM",
        "translating": "ИИ переводит",
        "thinking": "ИИ размышляет",
        "typing": "Печатает",
        "polishing": "Отполировка текста",
        "done": "● Готово",
        "conn_err": "✕ Ошибка связи",
        "api_err": "Ошибка API",
        "dict_variants": "варианты перевода и идиомы:",
        "custom_lang_hint": "Нажмите Enter для своего языка",
        "no_matches": "Нет совпадений",
        "ctx_paste_cur": "Вставить в курсор (Ctrl+V)",
        "ctx_paste_rep": "Вставить с заменой",
        "ctx_copy": "Копировать (Ctrl+C)",
        "ctx_cut": "Вырезать (Ctrl+X)",
        "ctx_sel_all": "Выделить всё (Ctrl+A)",
        "ctx_bold": "Сделать **Жирным**",
        "ctx_italic": "Сделать *Курсивом*",
        "ctx_code": "Сделать `Монолитом`",
        "ctx_strike": "Сделать ~~Зачёркнутым~~",
        "ctx_clear": "Очистить всё",
        "ctx_copy_sel": "Копировать выделенное (Ctrl+C)",
        "ctx_copy_all": "Копировать весь перевод",
        "warn_prefix": "⚠ Неверный язык:",
        "mismatch_warn": "⚠ Неверный язык: выбран «{src}», но это «{det}»! (Вот перевод с «{det}»):",
        "mismatch_status": "⚠ Это {det}, а не {src}!"
    },
    "en": {
        "tip_swap": "Swap languages",
        "tip_tts": "Listen to translation",
        "tip_go": "Translate (Ctrl+Enter)",
        "tip_stop": "Stop translation",
        "tip_auto_chk": "Auto-translate while typing",
        "tip_refresh": "Refresh LM Studio models",
        "tip_server": "Start LM Studio server",
        "tip_load_model": "Load model",
        "tip_vram": "Clear VRAM",
        "tip_settings": "Settings",
        "splash_sub": "Local Neural Machine Translator",
        "splash_init": "Initializing...",
        "splash_env": "Preparing graphics environment...",
        "splash_tex": "Building embedded UI assets...",
        "splash_ui": "Assembling main window...",
        "splash_cfg": "Reading config.json...",
        "splash_start": "Launching application...",
        "auto_detect": "Auto Detect",
        "auto_short": "Auto Detect",
        "select_lang": "Select language...",
        "select_model": "Select model...",
        "no_models": "No models in LM Studio",
        "offline_model": "LM Studio Offline",
        "loading": "Loading...",
        "auto_trans_chk": "Auto-translate",
        "smart_search_sw": "Smart Search",
        "settings_title": "Application Settings",
        "settings_pin": "Always on top",
        "settings_lang": "App Language",
        "server_btn": "Server",
        "instant_btn": "⚡ Instant Answer",
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
        "server_started": "● Server started!",
        "server_failed": "✕ Enable Local Server (:1234)",
        "lms_online": "● LM Studio Online",
        "vram_check": "Checking & clearing VRAM",
        "vram_cleaned_all": "✓ VRAM completely cleared",
        "vram_cleaned": "✓ VRAM cleared",
        "vram_already_empty": "✓ VRAM already empty",
        "vram_exit": "Clearing VRAM before exit...",
        "unloading": "Unloading",
        "loading_vram": "Loading into VRAM",
        "translating": "AI translating",
        "thinking": "AI thinking",
        "typing": "Typing",
        "polishing": "Polishing translation",
        "done": "● Done",
        "conn_err": "✕ Connection error",
        "api_err": "API Error",
        "dict_variants": "translations & idioms:",
        "custom_lang_hint": "Press Enter for custom language",
        "no_matches": "No matches",
        "ctx_paste_cur": "Paste at cursor (Ctrl+V)",
        "ctx_paste_rep": "Paste & replace all",
        "ctx_copy": "Copy (Ctrl+C)",
        "ctx_cut": "Cut (Ctrl+X)",
        "ctx_sel_all": "Select All (Ctrl+A)",
        "ctx_bold": "Make **Bold**",
        "ctx_italic": "Make *Italic*",
        "ctx_code": "Make `Inline Code`",
        "ctx_strike": "Make ~~Strikethrough~~",
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
    UI_STRINGS["ru"]["loading"], UI_STRINGS["en"]["loading"]
}

LANG_ISO_MAP = {
    "Auto Detect": "globe", "Russian": "ru", "English": "gb", "German": "de",
    "French": "fr", "Spanish": "es", "Italian": "it", "Portuguese": "pt",
    "Chinese (Simplified)": "cn", "Chinese (Traditional)": "tw", "Japanese": "jp",
    "Korean": "kr", "Ukrainian": "ua", "Belarusian": "by", "Kazakh": "kz",
    "Uzbek": "uz", "Kyrgyz": "kg", "Tajik": "tj", "Turkmen": "tm",
    "Azerbaijani": "az", "Armenian": "am", "Georgian": "ge", "Turkish": "tr",
    "Arabic": "sa", "Hebrew": "il", "Persian": "ir", "Hindi": "in",
    "Bengali": "bd", "Urdu": "pk", "Punjabi": "in", "Tamil": "in",
    "Telugu": "in", "Marathi": "in", "Gujarati": "in", "Kannada": "in",
    "Malayalam": "in", "Sinhala": "lk", "Nepali": "np", "Thai": "th",
    "Vietnamese": "vn", "Indonesian": "id", "Malay": "my", "Tagalog": "ph",
    "Burmese": "mm", "Khmer": "kh", "Lao": "la", "Mongolian": "mn",
    "Polish": "pl", "Czech": "cz", "Slovak": "sk", "Hungarian": "hu",
    "Romanian": "ro", "Bulgarian": "bg", "Serbian": "rs", "Croatian": "hr",
    "Bosnian": "ba", "Slovenian": "si", "Macedonian": "mk", "Albanian": "al",
    "Greek": "gr", "Lithuanian": "lt", "Latvian": "lv", "Estonian": "ee",
    "Dutch": "nl", "Swedish": "se", "Norwegian": "no", "Danish": "dk",
    "Finnish": "fi", "Icelandic": "is", "Irish": "ie", "Welsh": "gb-wls",
    "Scottish Gaelic": "gb-sct", "Basque": "es", "Catalan": "es",
    "Galician": "es", "Maltese": "mt", "Luxembourgish": "lu", "Afrikaans": "za",
    "Swahili": "ke", "Amharic": "et", "Yoruba": "ng", "Igbo": "ng",
    "Hausa": "ng", "Zulu": "za", "Xhosa": "za", "Somali": "so",
    "Malagasy": "mg", "Kurdish": "iq", "Pashto": "af", "Tatar": "ru",
    "Bashkir": "ru", "Chuvash": "ru", "Chechen": "ru", "Ossetian": "ru",
    "Yakut": "ru", "Buryat": "ru", "Udmurt": "ru", "Komi": "ru",
    "Mari": "ru", "Mordvin": "ru", "Yiddish": "il", "Latin": "va",
    "Ancient Greek": "gr", "Old Church Slavonic": "ru", "Sanskrit": "in",
    "Esperanto": "globe", "Interlingua": "globe", "Toki Pona": "globe",
    "Maori": "nz", "Hawaiian": "us", "Samoan": "ws", "Cebuano": "ph",
    "Javanese": "id", "Sundanese": "id", "Haitian Creole": "ht",
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
    "Auto Detect": ("Автоопределение", "auto авто определить автоматически обнаружение"),
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
TARGET_LANGUAGES_EN = [l for l in WORLD_LANGUAGES_EN if l != "Auto Detect"]

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
RE_CYR_LAT_MIXED_WORD = re.compile(
    r"\b(?:[а-яА-ЯёЁ]+[a-zA-Z\u00C0-\u024F]+[а-яА-ЯёЁa-zA-Z\u00C0-\u024F]*|"
    r"[a-zA-Z\u00C0-\u024F]+[а-яА-ЯёЁ]+[а-яА-ЯёЁa-zA-Z\u00C0-\u024F]*)\b"
)
RE_LATIN_WORDS = re.compile(r"\b[a-zA-Z\u00C0-\u024F]{2,}\b")
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

ALLOWED_LATIN_ACRONYMS = {
    "ai", "agi", "llm", "llms", "rnn", "rnns", "lstm", "lstms", "gpu", "cpu",
    "vram", "ram", "api", "sdk", "ui", "ux", "id", "url", "http", "https", "json"
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

ICON_NAMES = ("swap", "tts_play", "tts_stop", "play", "stop", "refresh", "vram_clean", "model_load", "server", "settings")
CDN_ICON_URLS = {}
_FONT_CACHE = {}


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
    """Ищет ресурс внутри PyInstaller _MEIPASS, затем в папке скрипта, затем в конфиге/кэше."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand = os.path.join(meipass, relative_path)
        if os.path.exists(cand):
            return cand
    cand_script = os.path.join(SCRIPT_DIR, relative_path)
    if os.path.exists(cand_script):
        return cand_script
    return os.path.join(BASE_DIR, relative_path)


def _draw_procedural_flag(iso_code, w=40, h=28):
    """Генерирует иконку флага прямо в памяти (RAM) — не требует внешних файлов или сети."""
    if not HAS_PIL:
        return None
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if iso_code == "globe":
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=4, fill="#1e3a8a", outline="#3b82f6", width=1)
        cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 4
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#93c5fd", width=2)
        d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline="#93c5fd", width=1)
        d.line([(cx - r, cy), (cx + r, cy)], fill="#93c5fd", width=1)
        return img

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
    }
    vert_3 = {
        "fr": ("#002395", "#ffffff", "#ed2939"),
        "it": ("#009246", "#ffffff", "#ce2b37"),
        "ro": ("#002b7f", "#fcd116", "#ce1126"),
        "ie": ("#169b62", "#ffffff", "#ff883e"),
        "ng": ("#008751", "#ffffff", "#008751"),
    }
    horiz_2 = {
        "ua": ("#0057b7", "#ffd700"),
        "pl": ("#ffffff", "#dc143c"),
        "id": ("#ff0000", "#ffffff"),
    }

    if iso_code in horiz_3:
        c1, c2, c3 = horiz_3[iso_code]
        d.rectangle([0, 0, w, h // 3], fill=c1)
        d.rectangle([0, h // 3, w, (2 * h) // 3], fill=c2)
        d.rectangle([0, (2 * h) // 3, w, h], fill=c3)
    elif iso_code in vert_3:
        c1, c2, c3 = vert_3[iso_code]
        d.rectangle([0, 0, w // 3, h], fill=c1)
        d.rectangle([w // 3, 0, (2 * w) // 3, h], fill=c2)
        d.rectangle([(2 * w) // 3, 0, w, h], fill=c3)
    elif iso_code in horiz_2:
        c1, c2 = horiz_2[iso_code]
        d.rectangle([0, 0, w, h // 2], fill=c1)
        d.rectangle([0, h // 2, w, h], fill=c2)
    elif iso_code in ("gb", "gb-wls", "gb-sct"):
        d.rectangle([0, 0, w, h], fill="#012169")
        d.line([(0, 0), (w, h)], fill="#ffffff", width=5)
        d.line([(0, h), (w, 0)], fill="#ffffff", width=5)
        d.line([(0, 0), (w, h)], fill="#c8102e", width=2)
        d.line([(0, h), (w, 0)], fill="#c8102e", width=2)
        d.rectangle([0, h // 2 - 4, w, h // 2 + 4], fill="#ffffff")
        d.rectangle([w // 2 - 4, 0, w // 2 + 4, h], fill="#ffffff")
        d.rectangle([0, h // 2 - 2, w, h // 2 + 2], fill="#c8102e")
        d.rectangle([w // 2 - 2, 0, w // 2 + 2, h], fill="#c8102e")
    elif iso_code == "us":
        d.rectangle([0, 0, w, h], fill="#b22234")
        for y in range(2, h, 4):
            d.rectangle([0, y, w, y + 1], fill="#ffffff")
        d.rectangle([0, 0, w // 2, h // 2], fill="#3c3b6e")
    elif iso_code == "es":
        d.rectangle([0, 0, w, h], fill="#aa151b")
        d.rectangle([0, h // 4, w, (3 * h) // 4], fill="#f1bf00")
    elif iso_code == "pt":
        d.rectangle([0, 0, (2 * w) // 5, h], fill="#006600")
        d.rectangle([(2 * w) // 5, 0, w, h], fill="#ff0000")
        d.ellipse([(2 * w) // 5 - 4, h // 2 - 4, (2 * w) // 5 + 4, h // 2 + 4], fill="#ffcc00")
    elif iso_code == "jp":
        d.rectangle([0, 0, w, h], fill="#ffffff")
        r = h // 3
        d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill="#bc002d")
    elif iso_code in ("cn", "vn"):
        d.rectangle([0, 0, w, h], fill="#de2910")
        d.ellipse([6, 6, 16, 16], fill="#ffde00")
    elif iso_code == "kr":
        d.rectangle([0, 0, w, h], fill="#ffffff")
        r = h // 4
        d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill="#cd2e3a")
    elif iso_code == "by":
        d.rectangle([0, 0, w, (2 * h) // 3], fill="#c8313e")
        d.rectangle([0, (2 * h) // 3, w, h], fill="#4aa657")
        d.rectangle([0, 0, 5, h], fill="#ffffff")
    elif iso_code == "kz":
        d.rectangle([0, 0, w, h], fill="#00afca")
        r = h // 4
        d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill="#fec50c")
    elif iso_code == "tr":
        d.rectangle([0, 0, w, h], fill="#e30a17")
        d.ellipse([w // 3 - 5, h // 2 - 6, w // 3 + 7, h // 2 + 6], fill="#ffffff")
        d.ellipse([w // 3 - 2, h // 2 - 5, w // 3 + 8, h // 2 + 5], fill="#e30a17")
    elif iso_code in ("se", "fi", "no", "dk", "is"):
        colors = {
            "se": ("#006aa7", "#fecc02"),
            "fi": ("#ffffff", "#003580"),
            "no": ("#ba0c2f", "#00205b"),
            "dk": ("#c8102e", "#ffffff"),
            "is": ("#02529c", "#dc1e35"),
        }
        bg_c, cr_c = colors[iso_code]
        d.rectangle([0, 0, w, h], fill=bg_c)
        d.rectangle([w // 3 - 2, 0, w // 3 + 3, h], fill=cr_c)
        d.rectangle([0, h // 2 - 2, w, h // 2 + 3], fill=cr_c)
    else:
        palette = ["#1d4ed8", "#047857", "#b91c1c", "#7e22ce", "#0f766e", "#b45309", "#374151"]
        col = palette[sum(ord(c) for c in iso_code) % len(palette)]
        d.rectangle([0, 0, w, h], fill=col)
        d.rectangle([0, h - 5, w, h], fill="#ffffff")

    d.rectangle([0, 0, w - 1, h - 1], outline="#323846", width=1)
    return img


def _draw_fallback_icon(name, size=192):
    """Генерирует векторную иконку кнопки прямо в памяти (RAM), если нет сети и кэша."""
    if not HAS_PIL:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = (255, 255, 255, 255)
    w = max(int(size * 0.1), 12)

    if name == "swap":
        y1 = int(size * 0.34)
        d.line([(int(size * 0.18), y1), (int(size * 0.82), y1)], fill=c, width=w)
        d.polygon([(int(size * 0.85), y1), (int(size * 0.62), y1 - int(size * 0.18)), (int(size * 0.62), y1 + int(size * 0.18))], fill=c)
        y2 = int(size * 0.66)
        d.line([(int(size * 0.18), y2), (int(size * 0.82), y2)], fill=c, width=w)
        d.polygon([(int(size * 0.15), y2), (int(size * 0.38), y2 - int(size * 0.18)), (int(size * 0.38), y2 + int(size * 0.18))], fill=c)

    elif name in ("tts_play", "tts_stop"):
        spk = [
            (int(size * 0.18), int(size * 0.38)),
            (int(size * 0.34), int(size * 0.38)),
            (int(size * 0.54), int(size * 0.20)),
            (int(size * 0.54), int(size * 0.80)),
            (int(size * 0.34), int(size * 0.62)),
            (int(size * 0.18), int(size * 0.62)),
        ]
        d.polygon(spk, fill=c)
        if name == "tts_play":
            d.arc([int(size * 0.42), int(size * 0.28), int(size * 0.74), int(size * 0.72)], start=-55, end=55, fill=c, width=max(w - 4, 8))
            d.arc([int(size * 0.34), int(size * 0.16), int(size * 0.88), int(size * 0.84)], start=-55, end=55, fill=c, width=max(w - 4, 8))
        else:
            d.line([(int(size * 0.62), int(size * 0.34)), (int(size * 0.86), int(size * 0.66))], fill=c, width=max(w - 2, 10))
            d.line([(int(size * 0.86), int(size * 0.34)), (int(size * 0.62), int(size * 0.66))], fill=c, width=max(w - 2, 10))

    elif name == "play":
        pts = [(int(size * 0.40), int(size * 0.30)), (int(size * 0.70), int(size * 0.60)), (int(size * 0.40), int(size * 0.80))]
        d.line(pts, fill=c, width=int(w * 1.35), joint="curve")

    elif name == "stop":
        d.ellipse([int(size * 0.14), int(size * 0.14), int(size * 0.86), int(size * 0.86)], outline=c, width=w)
        d.rounded_rectangle([int(size * 0.35), int(size * 0.35), int(size * 0.65), int(size * 0.65)], radius=8, fill=c)

    elif name == "refresh":
        bbox = [int(size * 0.18), int(size * 0.18), int(size * 0.82), int(size * 0.82)]
        d.arc(bbox, start=35, end=315, fill=c, width=w)
        d.polygon([(int(size * 0.84), int(size * 0.18)), (int(size * 0.86), int(size * 0.46)), (int(size * 0.58), int(size * 0.38))], fill=c)

    elif name == "vram_clean":
        # Иконка веника / метлы для очистки VRAM
        d.line([(int(size * 0.78), int(size * 0.14)), (int(size * 0.46), int(size * 0.46))], fill=c, width=max(w - 2, 12))
        collar = [
            (int(size * 0.36), int(size * 0.42)),
            (int(size * 0.58), int(size * 0.64)),
            (int(size * 0.52), int(size * 0.70)),
            (int(size * 0.30), int(size * 0.48)),
        ]
        d.polygon(collar, fill=c)
        bristles = [
            (int(size * 0.30), int(size * 0.48)),
            (int(size * 0.52), int(size * 0.70)),
            (int(size * 0.34), int(size * 0.88)),
            (int(size * 0.12), int(size * 0.66)),
        ]
        d.polygon(bristles, fill=c)
        d.line([(int(size * 0.22), int(size * 0.76)), (int(size * 0.35), int(size * 0.63))], fill=(0, 0, 0, 0), width=6)
        d.line([(int(size * 0.28), int(size * 0.82)), (int(size * 0.41), int(size * 0.69))], fill=(0, 0, 0, 0), width=6)

    elif name == "model_load":
        # Стрелка загрузки вниз в лоток
        cx = size // 2
        d.line([(cx, int(size * 0.15)), (cx, int(size * 0.62))], fill=c, width=w)
        d.polygon([
            (cx, int(size * 0.72)),
            (int(size * 0.26), int(size * 0.46)),
            (int(size * 0.74), int(size * 0.46))
        ], fill=c)
        tray_y = int(size * 0.84)
        d.line([(int(size * 0.18), int(size * 0.66)), (int(size * 0.18), tray_y)], fill=c, width=max(w - 2, 10))
        d.line([(int(size * 0.18), tray_y), (int(size * 0.82), tray_y)], fill=c, width=max(w - 2, 10))
        d.line([(int(size * 0.82), tray_y), (int(size * 0.82), int(size * 0.66))], fill=c, width=max(w - 2, 10))

    elif name == "server":
        d.rounded_rectangle([int(size * 0.18), int(size * 0.20), int(size * 0.82), int(size * 0.46)], radius=10, outline=c, width=w)
        d.rounded_rectangle([int(size * 0.18), int(size * 0.54), int(size * 0.82), int(size * 0.80)], radius=10, outline=c, width=w)
        d.ellipse([int(size * 0.28), int(size * 0.29), int(size * 0.36), int(size * 0.37)], fill=c)
        d.ellipse([int(size * 0.28), int(size * 0.63), int(size * 0.36), int(size * 0.71)], fill=c)

    elif name == "settings":
        d.ellipse([int(size * 0.26), int(size * 0.26), int(size * 0.74), int(size * 0.74)], outline=c, width=w)
        d.ellipse([int(size * 0.42), int(size * 0.42), int(size * 0.58), int(size * 0.58)], fill=c)
        d.line([(int(size * 0.50), int(size * 0.12)), (int(size * 0.50), int(size * 0.26))], fill=c, width=w)
        d.line([(int(size * 0.50), int(size * 0.74)), (int(size * 0.50), int(size * 0.88))], fill=c, width=w)
        d.line([(int(size * 0.12), int(size * 0.50)), (int(size * 0.26), int(size * 0.50))], fill=c, width=w)
        d.line([(int(size * 0.74), int(size * 0.50)), (int(size * 0.88), int(size * 0.50))], fill=c, width=w)

    return img.resize((64, 64), Image.Resampling.LANCZOS)


def ensure_cached_icons(splash=None):
    """
    Загружает иконки из вшитых ресурсов (_MEIPASS/icons) или папки icons/.
    Для новых иконок (vram_clean, model_load) при отсутствии на диске пробует скачать PNG с CDN,
    сохраняя в кэш, либо мгновенно рисует векторный фоллбэк в RAM.
    """
    if not HAS_PIL:
        return {}
    loaded = {}
    total = len(ICON_NAMES)
    for idx, name in enumerate(ICON_NAMES, start=1):
        pct = 10 + int((idx / total) * 35)
        if splash:
            splash.set_progress(pct, f"Loading icon {name} ({idx}/{total})...")

        pil_img = None
        local_cache_file = os.path.join(ICONS_DIR, f"{name}.png")
        for cand_path in (resource_path(os.path.join("icons", f"{name}.png")), local_cache_file):
            if os.path.isfile(cand_path) and os.path.getsize(cand_path) > 100:
                try:
                    pil_img = Image.open(cand_path).convert("RGBA")
                    break
                except Exception:
                    pass

        if pil_img is None and name in CDN_ICON_URLS:
            try:
                os.makedirs(ICONS_DIR, exist_ok=True)
                req = urllib.request.Request(CDN_ICON_URLS[name], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=1.8) as resp:
                    raw_bytes = resp.read()
                if raw_bytes and len(raw_bytes) > 150:
                    with open(local_cache_file, "wb") as f:
                        f.write(raw_bytes)
                    pil_img = Image.open(local_cache_file).convert("RGBA")
            except Exception:
                pil_img = None

        if pil_img is None:
            pil_img = _draw_fallback_icon(name)

        loaded[name] = pil_img
    return loaded


def ensure_cached_flags(splash=None):
    """
    Загружает флаги стран из вшитых ресурсов .exe (_MEIPASS/icons/flags),
    либо из локальной папки icons/flags/, либо мгновенно рисует их в оперативной памяти.
    """
    if not HAS_PIL:
        return {}
    unique_codes = sorted(set(LANG_ISO_MAP.values()))
    loaded_pil = {}

    if splash:
        splash.set_progress(55, "Building embedded flag icons...")

    for code in unique_codes:
        pil_img = None
        if code != "globe":
            for cand_path in (
                resource_path(os.path.join("icons", "flags", f"{code}.png")),
                os.path.join(FLAGS_DIR, f"{code}.png")
            ):
                if os.path.isfile(cand_path) and os.path.getsize(cand_path) > 60:
                    try:
                        pil_img = Image.open(cand_path).convert("RGBA").resize((40, 28), Image.Resampling.LANCZOS)
                        break
                    except Exception:
                        pass
        if pil_img is None:
            pil_img = _draw_procedural_flag(code, 40, 28)
        if pil_img is not None:
            loaded_pil[code] = pil_img

    return loaded_pil


def get_tkfont_for_widget(tk_widget, fallback_family=UI_FONT, fallback_size=-13, fallback_weight="bold"):
    try:
        font_spec = tk_widget.cget("font")
        if font_spec:
            key = str(font_spec)
            f = _FONT_CACHE.get(key)
            if f is None:
                f = tkfont.Font(root=tk_widget, font=font_spec)
                _FONT_CACHE[key] = f
            return f
    except Exception:
        pass

    key = (fallback_family, fallback_size, fallback_weight)
    f = _FONT_CACHE.get(key)
    if f is None:
        try:
            f = tkfont.Font(family=fallback_family, size=fallback_size, weight=fallback_weight)
            _FONT_CACHE[key] = f
        except Exception:
            return None
    return f


def truncate_text_with_font(text, max_phys_px, tk_font_obj=None, fallback_char_px=8):
    if not text or max_phys_px <= 20:
        return text
    if tk_font_obj is not None:
        try:
            if tk_font_obj.measure(text) <= max_phys_px:
                return text
            ell = "..."
            ell_w = tk_font_obj.measure(ell)
            target_w = max_phys_px - ell_w
            if target_w <= 8:
                return ell
            lo, hi = 1, len(text)
            best = 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if tk_font_obj.measure(text[:mid]) <= target_w:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            return text[:best].rstrip() + ell
        except Exception:
            pass

    max_chars = max(4, int(max_phys_px // max(fallback_char_px, 5)))
    if len(text) <= max_chars:
        return text
    return text[: max(1, max_chars - 3)].rstrip() + "..."


class HoverTooltip:
    def __init__(self, widget, text_provider, delay_ms=500):
        self.widget = widget
        self.text_provider = text_provider
        self.delay_ms = delay_ms
        self.tip_win = None
        self._after_id = None

        # Привязываем события ко всем под-виджетам CustomTkinter (canvas, entry, label)
        targets = [widget]
        for attr in ("_canvas", "_label", "_entry"):
            sub = getattr(widget, attr, None)
            if sub is not None and sub not in targets:
                targets.append(sub)

        for t in targets:
            try:
                t.bind("<Enter>", self._on_enter, add="+")
                t.bind("<Leave>", self._on_leave, add="+")
                t.bind("<ButtonPress>", self._on_leave, add="+")
            except Exception:
                pass

    def _on_enter(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        try:
            full_text = self.text_provider() if callable(self.text_provider) else str(self.text_provider)
            if not full_text:
                return
            self._hide()
            self.tip_win = tk.Toplevel(self.widget)
            self.tip_win.withdraw()
            self.tip_win.overrideredirect(True)
            self.tip_win.attributes("-topmost", True)
            if IS_LINUX:
                try:
                    self.tip_win.wm_attributes("-type", "tooltip")
                except Exception:
                    pass
            self.tip_win.configure(bg=THEME["border_focus"], padx=1, pady=1)
            lbl = tk.Label(
                self.tip_win,
                text=full_text,
                font=(UI_FONT, 10),
                bg=THEME["bg_popup"],
                fg=THEME["text_main"],
                padx=8,
                pady=4
            )
            lbl.pack()
            self.tip_win.update_idletasks()

            tw = self.tip_win.winfo_reqwidth()
            th = self.tip_win.winfo_reqheight()
            wx = self.widget.winfo_rootx()
            wy = self.widget.winfo_rooty()
            wh = self.widget.winfo_height()
            sw = self.widget.winfo_screenwidth()

            x = min(max(6, wx), max(6, sw - tw - 8))
            y = wy - th - 6 if wy - th - 6 > 8 else wy + wh + 6
            self.tip_win.geometry(f"{tw}x{th}+{x}+{y}")
            self.tip_win.deiconify()
        except Exception:
            self._hide()

    def _hide(self):
        if self.tip_win is not None:
            try:
                self.tip_win.destroy()
            except Exception:
                pass
            self.tip_win = None

def strip_loaded_prefix(val):
    if not val:
        return ""
    return val[len(LOADED_PREFIX):].strip() if val.startswith(LOADED_PREFIX) else val.strip()


def resolve_lms_executable():
    path_bin = shutil.which("lms")
    if path_bin:
        return path_bin
    candidates = [
        os.path.expanduser("~/.lmstudio/bin/lms"),
        os.path.expanduser(r"~\.lmstudio\bin\lms.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\LM-Studio\app\bin\lms.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\LM Studio\resources\app\.webpack\lms.exe"),
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


class GUISplashScreen:
    def __init__(self, parent, subtitle_text="Локальный нейросетевой переводчик", init_text="Инициализация..."):
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        if IS_LINUX:
            try:
                self.win.wm_attributes("-type", "splash")
            except Exception:
                pass
        self.win.configure(bg=THEME["border_focus"], padx=1, pady=1)

        w, h = 450, 195
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        inner = tk.Frame(self.win, bg=THEME["bg_root"], bd=0, highlightthickness=0)
        inner.pack(fill="both", expand=True)

        header_frame = tk.Frame(inner, bg=THEME["bg_root"])
        header_frame.pack(fill="x", padx=24, pady=(26, 4))

        badge = tk.Canvas(header_frame, width=36, height=36, bg=THEME["bg_root"], highlightthickness=0)
        badge.pack(side="left", padx=(0, 12))
        badge.create_oval(2, 2, 34, 34, fill="#1d4ed8", outline="#3b82f6", width=2)
        badge.create_text(18, 18, text="AI", fill="#ffffff", font=(UI_FONT, 11, "bold"))

        title_box = tk.Frame(header_frame, bg=THEME["bg_root"])
        title_box.pack(side="left", fill="x")
        tk.Label(
            title_box, text="LLM TRANSLATE", font=(UI_FONT, 16, "bold"),
            fg="#ffffff", bg=THEME["bg_root"], anchor="w"
        ).pack(fill="x")
        tk.Label(
            title_box, text=subtitle_text, font=(UI_FONT, 9),
            fg=THEME["text_muted"], bg=THEME["bg_root"], anchor="w"
        ).pack(fill="x")

        info_frame = tk.Frame(inner, bg=THEME["bg_root"])
        info_frame.pack(fill="x", padx=24, pady=(24, 6))

        self.lbl_task = tk.Label(
            info_frame, text=init_text, font=(UI_FONT, 10),
            fg="#d4d4d8", bg=THEME["bg_root"], anchor="w"
        )
        self.lbl_task.pack(side="left", fill="x", expand=True)

        self.lbl_pct = tk.Label(
            info_frame, text="0%", font=(UI_FONT, 10, "bold"),
            fg="#3b82f6", bg=THEME["bg_root"], anchor="e"
        )
        self.lbl_pct.pack(side="right")

        self.bar_w = w - 50
        self.bar_canvas = tk.Canvas(
            inner, width=self.bar_w, height=8, bg="#222634",
            bd=0, highlightthickness=0
        )
        self.bar_canvas.pack(padx=24, pady=(2, 16))
        self.bar_fill_rect = self.bar_canvas.create_rectangle(0, 0, 0, 8, fill="#3b82f6", width=0)

        self.win.update()

    def set_progress(self, percent, status_text):
        try:
            pct = max(0, min(100, int(percent)))
            self.lbl_task.configure(text=status_text)
            self.lbl_pct.configure(text=f"{pct}%")
            fill_px = int((pct / 100.0) * self.bar_w)
            self.bar_canvas.coords(self.bar_fill_rect, 0, 0, fill_px, 8)
            self.win.update()
        except Exception:
            pass

    def close(self):
        try:
            self.win.destroy()
        except Exception:
            pass


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


class SearchableDropdown(ctk.CTkFrame):
    def __init__(
        self, master, root_window, values, default_value,
        command=None, aliases=None, prefer_upwards=False,
        height=34, allow_custom=True, font_size=13, flag_provider=None
    ):
        super().__init__(
            master,
            fg_color=THEME["bg_dd"],
            border_color=THEME["border_subtle"],
            border_width=1,
            corner_radius=8,
            height=height
        )
        self.root = root_window
        self.values = list(values)
        self.aliases = aliases or {}
        self.command = command
        self.current_val = default_value
        self.prefer_upwards = prefer_upwards
        self.allow_custom = allow_custom
        self.font_size = font_size
        self.flag_provider = flag_provider
        self._is_editing = False
        self._popup_open = False

        self.dropdown_win = None
        self.list_canvas = None
        self.scrollbar = None
        self._filtered_items = []
        self._selected_idx = 0
        self._row_h = 28

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_propagate(False)

        self.lbl_flag = tk.Label(
            self,
            bg=THEME["bg_dd"],
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        if self.flag_provider is not None:
            self.lbl_flag.grid(row=0, column=0, sticky="w", padx=(8, 2), pady=2)
            self.lbl_flag.bind("<Button-1>", self._on_toggle_btn_click)

        self.entry = ctk.CTkEntry(
            self,
            height=height - 4,
            font=(UI_FONT, self.font_size, "bold"),
            fg_color="transparent",
            border_width=0,
            text_color=THEME["text_main"]
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(4 if self.flag_provider is None else 2, 0), pady=2)

        self.btn_arrow = ctk.CTkButton(
            self,
            text="▾",
            width=22,
            height=height - 6,
            font=(UI_FONT, 13),
            fg_color="transparent",
            hover_color=THEME["bg_dd_hover"],
            text_color=THEME["text_muted"],
            corner_radius=6,
            command=self._on_toggle_btn_click
        )
        self.btn_arrow.grid(row=0, column=2, sticky="e", padx=(0, 3), pady=2)

        self.entry.insert(0, default_value)

        self.entry.bind("<Button-1>", self._on_entry_click)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Escape>", lambda e: self.close_dropdown())
        self.entry.bind("<MouseWheel>", self._on_entry_mousewheel)
        self.bind("<Configure>", self._on_entry_configure, add="+")
        self.entry.bind("<Configure>", self._on_entry_configure, add="+")

        HoverTooltip(self.entry._entry, self._get_tooltip_if_truncated)

    def _keep_entry_focus(self):
        if self._is_editing and self._popup_open:
            try:
                self.entry._entry.focus_set()
            except Exception:
                pass

    def _update_header_flag(self):
        if self.flag_provider is None:
            return
        try:
            if self._is_editing:
                self.lbl_flag.configure(image="")
                if self.lbl_flag.winfo_manager():
                    self.lbl_flag.grid_remove()
                self.entry.grid_configure(padx=(6, 0))
                return
            photo = self.flag_provider(self.current_val)
            if photo is not None:
                if not self.lbl_flag.winfo_manager():
                    self.lbl_flag.grid(row=0, column=0, sticky="w", padx=(8, 2), pady=2)
                self.entry.grid_configure(padx=(2, 0))
                self.lbl_flag.configure(image=photo)
                self.lbl_flag._image_ref = photo
            else:
                self.lbl_flag.configure(image="")
                if self.lbl_flag.winfo_manager():
                    self.lbl_flag.grid_remove()
                self.entry.grid_configure(padx=(6, 0))
        except Exception:
            pass

    def _get_tooltip_if_truncated(self):
        if self._is_editing:
            return ""
        shown = self.entry.get()
        if shown.endswith("...") and shown != self.current_val:
            return self.current_val
        return ""

    def _on_entry_configure(self, event=None):
        if not self._is_editing:
            self._refresh_display_text()

    def _refresh_display_text(self):
        if self._is_editing:
            return
        self._update_header_flag()
        try:
            tk_ent = self.entry._entry
            phys_w = tk_ent.winfo_width()
            if phys_w <= 24:
                frame_w = self.winfo_width()
                arrow_w = max(self.btn_arrow.winfo_width(), 26)
                flag_w = 28 if self.flag_provider is not None else 0
                phys_w = frame_w - arrow_w - flag_w - 14

            if phys_w <= 24:
                if self.entry.get() != self.current_val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, self.current_val)
                self.after(45, self._refresh_display_text)
                return

            avail_phys_px = max(32, phys_w - 6)
            f_obj = get_tkfont_for_widget(tk_ent, fallback_family=UI_FONT, fallback_size=-self.font_size, fallback_weight="bold")
            disp = truncate_text_with_font(self.current_val, avail_phys_px, tk_font_obj=f_obj)
            if self.entry.get() != disp:
                self.entry.delete(0, "end")
                self.entry.insert(0, disp)
            tk_ent.icursor(0)
            tk_ent.xview_moveto(0.0)
        except Exception:
            try:
                if self.entry.get() != self.current_val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, self.current_val)
            except Exception:
                pass

    def _start_editing_and_open(self):
        if hasattr(self.root, "_close_all_dropdowns"):
            self.root._close_all_dropdowns(except_dd=self)
        self._is_editing = True
        self._update_header_flag()
        self.configure(border_color=THEME["border_focus"])
        self.entry.delete(0, "end")
        self.open_dropdown(self.values)
        self.entry._entry.focus_set()

    def _on_toggle_btn_click(self, event=None):
        if self._popup_open and self.dropdown_win and self.dropdown_win.winfo_exists() and self.dropdown_win.winfo_ismapped():
            self.close_dropdown()
        else:
            self._start_editing_and_open()
        return "break"

    def _on_entry_click(self, event=None):
        if self._popup_open and self.dropdown_win and self.dropdown_win.winfo_exists() and self.dropdown_win.winfo_ismapped():
            self.entry._entry.focus_set()
            return
        self._start_editing_and_open()

    def trigger_filter_from_entry(self):
        self._is_editing = True
        self._update_header_flag()
        query = self.entry.get().strip().lower()
        if not query:
            matches = self.values
        elif getattr(self.root, "use_smart_search", False):
            matches = smart_filter_items(query, self.values, self.aliases)
        else:
            matches = [
                item for item in self.values
                if query in item.lower()
                or query in self.aliases.get(strip_flag_prefix(strip_loaded_prefix(item)), "")
                or query in self.aliases.get(strip_loaded_prefix(item), "")
            ]
        self.open_dropdown(matches)

    def _on_key_release(self, event):
        if event.keysym in (
            "Return", "Escape", "Up", "Down", "Left", "Right", "Home", "End",
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R",
            "Tab", "ISO_Left_Tab", "Caps_Lock", "Num_Lock"
        ):
            return
        if event.state & 0x4:
            return
        self.trigger_filter_from_entry()

    def _set_highlighted_row(self, new_idx, ensure_visible=True):
        if not self._filtered_items or not self.list_canvas:
            return
        new_idx = max(0, min(new_idx, len(self._filtered_items) - 1))
        old_idx = self._selected_idx
        self._selected_idx = new_idx
        try:
            self.list_canvas.itemconfig(f"bg_{old_idx}", fill=THEME["bg_popup"])
            self.list_canvas.itemconfig(f"bg_{new_idx}", fill=THEME["bg_accent"])
            if ensure_visible:
                total_h = max(1, len(self._filtered_items) * self._row_h)
                vis_h = max(1, self.list_canvas.winfo_height())
                top_frac, bot_frac = self.list_canvas.yview()
                row_top = (new_idx * self._row_h) / total_h
                row_bot = ((new_idx + 1) * self._row_h) / total_h
                if row_top < top_frac:
                    self.list_canvas.yview_moveto(row_top)
                elif row_bot > bot_frac:
                    self.list_canvas.yview_moveto(max(0.0, row_bot - (vis_h / total_h)))
        except Exception:
            pass

    def _on_arrow_down(self, event):
        if not (self._popup_open and self.dropdown_win and self.dropdown_win.winfo_ismapped()):
            self._start_editing_and_open()
            return "break"
        if self._filtered_items:
            self._set_highlighted_row(self._selected_idx + 1, ensure_visible=True)
        return "break"

    def _on_arrow_up(self, event):
        if self._popup_open and self.dropdown_win and self.dropdown_win.winfo_ismapped() and self._filtered_items:
            self._set_highlighted_row(self._selected_idx - 1, ensure_visible=True)
        return "break"

    def _on_enter(self, event=None):
        typed = self.entry.get().strip()
        if self._popup_open and self.dropdown_win and self.dropdown_win.winfo_ismapped() and self._filtered_items:
            idx = max(0, min(self._selected_idx, len(self._filtered_items) - 1))
            self.select(self._filtered_items[idx])
            return
        if self.allow_custom and typed and not typed.endswith("..."):
            self.select(typed, is_custom=True)
        else:
            self.select(self.current_val)

    def _create_popup_if_needed(self):
        if self.dropdown_win and self.dropdown_win.winfo_exists():
            return

        # Внутриоконный фрейм-оверлей: не создает отдельного окна ОС и не забирает фокус у приложения
        self.dropdown_win = tk.Frame(
            self.root,
            bg=THEME["border_focus"],
            padx=1,
            pady=1,
            bd=0,
            highlightthickness=0
        )

        container = tk.Frame(self.dropdown_win, bg=THEME["bg_popup"], bd=0, highlightthickness=0)
        container.pack(fill="both", expand=True)

        self.list_canvas = tk.Canvas(
            container,
            bg=THEME["bg_popup"],
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=0
        )
        self.list_canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ctk.CTkScrollbar(
            container,
            command=self.list_canvas.yview,
            width=12,
            fg_color=THEME["bg_popup"],
            button_color="#323846",
            button_hover_color="#454d5e"
        )
        self.scrollbar.pack(side="right", fill="y", padx=2, pady=2)
        self.list_canvas.configure(yscrollcommand=self.scrollbar.set)

        for sb_w in (self.scrollbar, getattr(self.scrollbar, "_canvas", None)):
            if sb_w is not None:
                sb_w.bind("<Button-1>", lambda e: self.after(1, self._keep_entry_focus), add="+")
                sb_w.bind("<B1-Motion>", lambda e: self.after(1, self._keep_entry_focus), add="+")
                sb_w.bind("<ButtonRelease-1>", lambda e: self.after(1, self._keep_entry_focus), add="+")
                sb_w.bind("<MouseWheel>", self._on_mousewheel)

        self.list_canvas.bind("<Motion>", self._on_canvas_hover)
        self.list_canvas.bind("<ButtonRelease-1>", self._on_canvas_click)
        self.list_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.list_canvas.bind("<Button-4>", lambda e: self.list_canvas.yview_scroll(-2, "units"))
        self.list_canvas.bind("<Button-5>", lambda e: self.list_canvas.yview_scroll(2, "units"))

    def _on_entry_mousewheel(self, event):
        if self._popup_open and self.list_canvas:
            return self._on_mousewheel(event)

    def _on_mousewheel(self, event):
        if not self.list_canvas:
            return "break"
        delta = event.delta
        step = int(-1 * (delta / 120) * 2) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
        self.list_canvas.yview_scroll(step, "units")
        return "break"

    def _on_canvas_hover(self, event):
        if not self._filtered_items:
            return
        cy = self.list_canvas.canvasy(event.y)
        idx = int(cy // self._row_h)
        if 0 <= idx < len(self._filtered_items) and idx != self._selected_idx:
            self._set_highlighted_row(idx, ensure_visible=False)

    def _on_canvas_click(self, event):
        if not self._filtered_items:
            return
        cy = self.list_canvas.canvasy(event.y)
        idx = int(cy // self._row_h)
        if 0 <= idx < len(self._filtered_items):
            self.select(self._filtered_items[idx])

    def _compute_popup_width_px(self):
        self.update_idletasks()
        frame_w = self.winfo_width()
        if not self.allow_custom and self.master is not None:
            return max(frame_w, self.master.winfo_width())
        return max(frame_w, 180)

    def sync_position(self):
        if not self._popup_open or not self.dropdown_win or not self.dropdown_win.winfo_exists():
            return
        if not self.root.winfo_viewable() or self.root.state() == "iconic":
            self.close_dropdown()
            return

        self.root.update_idletasks()
        try:
            scale = self._get_widget_scaling()
        except Exception:
            scale = 1.0

        rel_x = self.winfo_rootx() - self.root.winfo_rootx()
        rel_y = self.winfo_rooty() - self.root.winfo_rooty()
        box_w = self._compute_popup_width_px()
        box_h = self.winfo_height()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        if rel_x + box_w > root_w - 6:
            box_w = max(160, root_w - rel_x - 6)

        count = max(len(self._filtered_items), 1)
        self._row_h = max(26, int(26 * scale))
        max_phys_h = int(260 * scale)
        gap_phys = max(int(4 * scale), 4)

        space_below = root_h - (rel_y + box_h) - 8
        space_above = rel_y - 8

        if (self.prefer_upwards and space_above >= 120) or (space_below < 140 and space_above > space_below):
            avail_h = max(80, space_above - gap_phys)
            popup_phys_h = min(count * self._row_h + 6, max_phys_h, avail_h)
            pos_y = rel_y - popup_phys_h - gap_phys
        else:
            avail_h = max(80, space_below - gap_phys)
            popup_phys_h = min(count * self._row_h + 6, max_phys_h, avail_h)
            pos_y = rel_y + box_h + gap_phys

        self.dropdown_win.place(x=rel_x, y=pos_y, width=box_w, height=popup_phys_h)
        self.dropdown_win.lift()

    def open_dropdown(self, items):
        self._create_popup_if_needed()
        self._filtered_items = list(items)
        self._popup_open = True
        try:
            scale = self._get_widget_scaling()
        except Exception:
            scale = 1.0
        self._row_h = max(26, int(26 * scale))

        popup_phys_w = self._compute_popup_width_px()
        sb_reserve = max(int(18 * scale), 18)
        text_x = int(34 * scale) if self.flag_provider is not None else 12
        avail_list_phys_px = max(120, popup_phys_w - text_x - sb_reserve - 8)
        row_font = (UI_FONT, 11)

        self.list_canvas.delete("all")
        self.list_canvas._img_refs = []

        if not self._filtered_items:
            msg = self.root._tr("custom_lang_hint") if self.allow_custom else self.root._tr("no_matches")
            self.list_canvas.create_text(
                12, self._row_h // 2,
                text=msg, fill="gray", font=row_font, anchor="w"
            )
            self.list_canvas.configure(scrollregion=(0, 0, popup_phys_w - sb_reserve, self._row_h))
        else:
            cur_clean = strip_flag_prefix(strip_loaded_prefix(self.current_val))
            self._selected_idx = 0
            for idx, item in enumerate(self._filtered_items):
                if strip_flag_prefix(strip_loaded_prefix(item)) == cur_clean:
                    self._selected_idx = idx
                    break

            f_obj = get_tkfont_for_widget(self.list_canvas, fallback_family=UI_FONT, fallback_size=-11, fallback_weight="normal")
            for idx, item in enumerate(self._filtered_items):
                y0 = idx * self._row_h
                y1 = y0 + self._row_h
                yc = y0 + self._row_h // 2
                bg_col = THEME["bg_accent"] if idx == self._selected_idx else THEME["bg_popup"]

                self.list_canvas.create_rectangle(
                    2, y0 + 1, popup_phys_w - sb_reserve, y1 - 1,
                    fill=bg_col, outline="", tags=(f"bg_{idx}",)
                )
                if self.flag_provider is not None:
                    photo = self.flag_provider(item)
                    if photo is not None:
                        self.list_canvas._img_refs.append(photo)
                        self.list_canvas.create_image(int(17 * scale), yc, image=photo, anchor="center")

                disp_item = truncate_text_with_font(item, avail_list_phys_px, tk_font_obj=f_obj)
                self.list_canvas.create_text(
                    text_x, yc,
                    text=disp_item, fill="#ffffff", font=row_font, anchor="w"
                )

            total_h = len(self._filtered_items) * self._row_h
            self.list_canvas.configure(scrollregion=(0, 0, popup_phys_w - sb_reserve, total_h))

        self.list_canvas.yview_moveto(0.0)
        self.sync_position()
        if self._filtered_items and self._selected_idx > 4:
            self._set_highlighted_row(self._selected_idx, ensure_visible=True)
        self._keep_entry_focus()

    def select(self, val, is_custom=False):
        if val in self.values or is_custom:
            self.current_val = val
            if is_custom and val not in self.values:
                self.values.append(val)
        self._is_editing = False
        self._popup_open = False
        self.configure(border_color=THEME["border_subtle"])
        if self.dropdown_win and self.dropdown_win.winfo_exists():
            self.dropdown_win.place_forget()
        self._refresh_display_text()
        self.root.focus_set()
        if self.command:
            self.command(self.current_val)

    def close_dropdown(self):
        self._is_editing = False
        self._popup_open = False
        self.configure(border_color=THEME["border_subtle"])
        if self.dropdown_win and self.dropdown_win.winfo_exists():
            self.dropdown_win.place_forget()
        self._refresh_display_text()

    def configure_values(self, new_values):
        self.values = list(new_values)

    def get(self):
        return self.current_val

    def set(self, val):
        self.current_val = val
        self._is_editing = False
        self._refresh_display_text()


class LLMTranslateApp(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=THEME["bg_root"])
        self.ui_lang = self._peek_ui_lang()

        self.withdraw()
        self.splash = GUISplashScreen(self, subtitle_text=self._tr("splash_sub"), init_text=self._tr("splash_init"))
        self.splash.set_progress(5, self._tr("splash_env"))

        self.title("LLM TRANSLATE")
        w, h = 1060, 600
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(860, 470)
        self._apply_app_icon()

        self.raw_icons = ensure_cached_icons(splash=self.splash)
        self.raw_flags = ensure_cached_flags(splash=self.splash)
        self.splash.set_progress(72, self._tr("splash_tex"))

        self.ctk_icons = {}
        icon_sizes = {
            "swap": (18, 18), "tts_play": (18, 18), "tts_stop": (18, 18), "play": (20, 20), "stop": (18, 18),
            "refresh": (16, 16), "vram_clean": (16, 16), "model_load": (16, 16), "server": (15, 15), "settings": (16, 16)
        }
        for k, sz in icon_sizes.items():
            if k in self.raw_icons and self.raw_icons[k] is not None:
                self.ctk_icons[k] = ctk.CTkImage(light_image=self.raw_icons[k], dark_image=self.raw_icons[k], size=sz)
            else:
                self.ctk_icons[k] = None

        self.flag_tk_photos = {}
        self.flag_ctk_icons = {}
        if HAS_PIL:
            for code, pil_img in self.raw_flags.items():
                try:
                    resized = pil_img.resize((20, 14), Image.Resampling.LANCZOS)
                    self.flag_tk_photos[code] = ImageTk.PhotoImage(resized)
                    self.flag_ctk_icons[code] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(18, 13))
                except Exception:
                    pass

        self.client = OpenAI(base_url=f"http://{LM_HOST}:{LM_PORT}/v1", api_key="lm-studio", timeout=15.0)
        self.model_id = self._tr("select_model")
        self._saved_config_model = self._tr("select_model")
        self._available_models = []
        self._loaded_vram_models = set()
        self._is_online = False
        self._server_booting = False
        self._is_loading_model = False
        self.use_smart_search = False
        self.pin_window = False
        self.settings_win = None

        self._tts_proc = None
        self._tts_lock = threading.Lock()
        self._tts_stop_event = threading.Event()
        self._is_speaking = False

        self.is_auto_detect = True
        self.detected_src_lang = None

        self._task_id = 0
        self._model_switch_id = 0
        self._active_stream = None
        self._stream_lock = threading.Lock()
        self._last_edit_time = 0.0
        self._last_translated_state = ("", "", "", "")
        self._last_win_rect = (0, 0, 0, 0)

        self._anim_running = False
        self._anim_phase_text = ""
        self._anim_color = "#eab308"
        self._anim_start_ts = 0.0
        self._anim_step = 0
        self._full_status_text = self._tr("connecting")
        self._full_status_color = THEME["text_muted"]

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
        self._last_selected_out_text = ""

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.splash.set_progress(82, self._tr("splash_ui"))
        self._build_ui()

        self.splash.set_progress(92, self._tr("splash_cfg"))
        self._setup_bindings()
        self._load_config()
        self._update_swap_button_state()
        self._sync_vram_button_visibility()

        self.splash.set_progress(100, self._tr("splash_start"))
        time.sleep(0.05)
        self.splash.close()

        self._withdraw_called_before_window_exists = False
        self._iconify_called_before_window_exists = False
        self.deiconify()
        self.update_idletasks()
        self.after(50, self._ensure_window_visible)

        self.fetch_models(auto_start_server=True)
        self.after(120, self._realtime_watcher)
        self.after(5000, self._auto_reconnect_loop)

    def _get_flag_photo_for_label(self, label_text):
        if not label_text or label_text in ALL_LANG_PLACEHOLDERS:
            return None
        clean = strip_flag_prefix(label_text)
        if clean.startswith("Авто (") or clean.startswith("Auto Detect ("):
            inner = clean.split("(", 1)[1].rstrip(")")
            canon = self._lang_to_canonical(inner)
        else:
            canon = self._lang_to_canonical(clean)
        iso = LANG_ISO_MAP.get(canon, "globe")
        return self.flag_tk_photos.get(iso) or self.flag_tk_photos.get("globe")

    def _ensure_window_visible(self):
        try:
            self._withdraw_called_before_window_exists = False
            if self.state() != "normal":
                self.deiconify()
            self._apply_app_icon()
            self.lift()
            self.focus_force()
            for dd in (self.dd_src, self.dd_tgt, self.dd_model):
                dd._refresh_display_text()
            self._refresh_status_label_ellipsis()
        except Exception:
            pass

    def _peek_ui_lang(self):
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                lang = cfg.get("ui_lang", "ru")
                if lang in ("ru", "en"):
                    return lang
            except Exception:
                pass
        return "ru"

    def _tr(self, key, **kwargs):
        text = UI_STRINGS.get(self.ui_lang, UI_STRINGS["ru"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _lang_to_canonical(self, val):
        if not val:
            return ""
        clean = strip_flag_prefix(val)
        if clean in ALL_LANG_PLACEHOLDERS:
            return ""
        if (
            clean in ("Auto Detect", "Автоопределение")
            or clean.startswith("Auto Detect (")
            or clean.startswith("Автоопределение (")
            or clean.startswith("Авто (")
        ):
            return "Auto Detect"
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
        if canon == "Auto Detect":
            return self._tr("auto_detect")
        if self.ui_lang == "ru":
            return LANG_EN_TO_RU.get(canon, canon)
        return canon

    def _format_auto_detect_display(self, detected_canon=None):
        if not detected_canon:
            return self._tr("auto_detect")
        det_disp = self._lang_to_display(detected_canon)
        prefix = self._tr("auto_short")
        return f"{prefix} ({det_disp})"

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
            if "/" in h:
                parts = [p.strip() for p in h.split("/")]
                trans_parts = [POS_RU_TO_EN.get(p, POS_TOKEN_RU_TO_EN.get(p, p)) for p in parts]
                return " / ".join(trans_parts)
            res = h
            for ru_k, en_v in POS_TOKEN_RU_TO_EN.items():
                res = res.replace(ru_k, en_v)
            return res
        else:
            if h in POS_EN_TO_RU:
                return POS_EN_TO_RU[h]
            if "/" in h:
                parts = [p.strip() for p in h.split("/")]
                trans_parts = [POS_EN_TO_RU.get(p, POS_TOKEN_EN_TO_RU.get(p, p)) for p in parts]
                return " / ".join(trans_parts)
            res = h
            for en_k, ru_v in POS_TOKEN_EN_TO_RU.items():
                res = res.replace(en_k, ru_v)
            return res

    def _build_mismatch_texts(self, src_canon, det_canon):
        src_disp = self._lang_to_display(src_canon)
        det_disp = self._lang_to_display(det_canon)
        banner = self._tr("mismatch_warn", src=src_disp, det=det_disp)
        status = self._tr("mismatch_status", det=det_disp, src=src_disp)
        return banner, status

    def _sync_server_button_visibility(self):
        try:
            if self._is_online:
                if self.btn_server.winfo_manager():
                    self.btn_server.grid_remove()
                    self.after(20, self.dd_model._refresh_display_text)
            else:
                if not self.btn_server.winfo_manager():
                    self.btn_server.grid(row=0, column=2, padx=2)
                    self.after(20, self.dd_model._refresh_display_text)
        except Exception:
            pass

    def _sync_vram_button_visibility(self):
        try:
            clean_cur = strip_loaded_prefix(self.model_id)
            valid_selected = self._is_valid_model_selected()
            cur_is_loaded = valid_selected and (clean_cur in self._loaded_vram_models)
            any_loaded = len(self._loaded_vram_models) > 0

            if not self._is_online:
                if hasattr(self, "btn_vram") and self.btn_vram.winfo_manager():
                    self.btn_vram.grid_remove()
                if hasattr(self, "btn_load_model") and self.btn_load_model.winfo_manager():
                    self.btn_load_model.grid_remove()
            elif cur_is_loaded or (not valid_selected and any_loaded):
                if hasattr(self, "btn_load_model") and self.btn_load_model.winfo_manager():
                    self.btn_load_model.grid_remove()
                if hasattr(self, "btn_vram") and not self.btn_vram.winfo_manager():
                    self.btn_vram.grid(row=0, column=3, padx=2)
            elif valid_selected and not cur_is_loaded:
                if hasattr(self, "btn_vram") and self.btn_vram.winfo_manager():
                    self.btn_vram.grid_remove()
                if hasattr(self, "btn_load_model") and not self.btn_load_model.winfo_manager():
                    self.btn_load_model.grid(row=0, column=3, padx=2)
            else:
                if hasattr(self, "btn_vram") and self.btn_vram.winfo_manager():
                    self.btn_vram.grid_remove()
                if hasattr(self, "btn_load_model") and self.btn_load_model.winfo_manager():
                    self.btn_load_model.grid_remove()

            self.after(20, self.dd_model._refresh_display_text)
        except Exception:
            pass

    def _toggle_settings_popup(self):
        if self.settings_win and self.settings_win.winfo_exists() and self.settings_win.winfo_ismapped():
            self._close_settings_popup()
        else:
            self._close_all_dropdowns(except_dd="settings")
            self._open_settings_popup()

    def _open_settings_popup(self):
        if self.settings_win and self.settings_win.winfo_exists():
            try:
                self.settings_win.destroy()
            except Exception:
                pass

        self.settings_win = tk.Frame(self, bg=THEME["border_focus"], padx=1, pady=1, bd=0, highlightthickness=0)

        card = tk.Frame(self.settings_win, bg=THEME["bg_popup"], bd=0, highlightthickness=0)
        card.pack(fill="both", expand=True)

        self.lbl_set_title = tk.Label(
            card, text=self._tr("settings_title"),
            font=(UI_FONT, 10, "bold"), fg=THEME["text_muted"], bg=THEME["bg_popup"], anchor="w"
        )
        self.lbl_set_title.pack(fill="x", padx=14, pady=(10, 6))

        sep = tk.Frame(card, bg=THEME["border_subtle"], height=1)
        sep.pack(fill="x", padx=12, pady=(0, 6))

        row_pin = tk.Frame(card, bg=THEME["bg_popup"])
        row_pin.pack(fill="x", padx=14, pady=5)
        self.lbl_set_pin = tk.Label(
            row_pin, text=self._tr("settings_pin"),
            font=(UI_FONT, 11), fg=THEME["text_main"], bg=THEME["bg_popup"], anchor="w"
        )
        self.lbl_set_pin.pack(side="left", fill="x", expand=True)

        self.sw_pin = ctk.CTkSwitch(
            row_pin, text="", width=40, switch_width=36, switch_height=19,
            command=self._toggle_pin
        )
        self.sw_pin.pack(side="right")
        if self.pin_window:
            self.sw_pin.select()
        else:
            self.sw_pin.deselect()

        row_smart = tk.Frame(card, bg=THEME["bg_popup"])
        row_smart.pack(fill="x", padx=14, pady=5)
        smart_title = "Умный поиск" if self.ui_lang == "ru" else "Smart Search"
        self.lbl_set_smart = tk.Label(
            row_smart, text=smart_title,
            font=(UI_FONT, 11), fg=THEME["text_main"], bg=THEME["bg_popup"], anchor="w"
        )
        self.lbl_set_smart.pack(side="left", fill="x", expand=True)

        self.sw_smart = ctk.CTkSwitch(
            row_smart, text="", width=40, switch_width=36, switch_height=19,
            command=self._toggle_smart_search
        )
        self.sw_smart.pack(side="right")
        if self.use_smart_search:
            self.sw_smart.select()
        else:
            self.sw_smart.deselect()

        row_lang = tk.Frame(card, bg=THEME["bg_popup"])
        row_lang.pack(fill="x", padx=14, pady=(6, 12))
        self.lbl_set_lang = tk.Label(
            row_lang, text=self._tr("settings_lang"),
            font=(UI_FONT, 11), fg=THEME["text_main"], bg=THEME["bg_popup"], anchor="w"
        )
        self.lbl_set_lang.pack(side="left", fill="x", expand=True, padx=(0, 8))

        lang_btns_frame = tk.Frame(row_lang, bg=THEME["bg_popup"])
        lang_btns_frame.pack(side="right")

        self.btn_lang_ru = ctk.CTkButton(
            lang_btns_frame,
            text="RU",
            image=self.flag_ctk_icons.get("ru"),
            compound="left",
            width=58,
            height=26,
            corner_radius=6,
            font=(UI_FONT, 11, "bold"),
            fg_color=THEME["bg_accent"] if self.ui_lang == "ru" else THEME["bg_btn"],
            hover_color=THEME["bg_accent_hover"] if self.ui_lang == "ru" else THEME["bg_btn_hover"],
            command=lambda: self.set_ui_language("ru")
        )
        self.btn_lang_ru.pack(side="left", padx=(0, 4))

        self.btn_lang_en = ctk.CTkButton(
            lang_btns_frame,
            text="EN",
            image=self.flag_ctk_icons.get("gb"),
            compound="left",
            width=58,
            height=26,
            corner_radius=6,
            font=(UI_FONT, 11, "bold"),
            fg_color=THEME["bg_accent"] if self.ui_lang == "en" else THEME["bg_btn"],
            hover_color=THEME["bg_accent_hover"] if self.ui_lang == "en" else THEME["bg_btn_hover"],
            command=lambda: self.set_ui_language("en")
        )
        self.btn_lang_en.pack(side="left")

        self.settings_win.update_idletasks()
        self._sync_settings_popup_position()

    def _sync_settings_popup_position(self):
        if not self.settings_win or not self.settings_win.winfo_exists():
            return
        try:
            self.update_idletasks()
            self.settings_win.update_idletasks()
            try:
                scale = self._get_widget_scaling()
            except Exception:
                scale = 1.0
            pw = max(self.settings_win.winfo_reqwidth(), int(275 * scale))
            ph = max(self.settings_win.winfo_reqheight(), int(150 * scale))
            bx = self.btn_settings.winfo_rootx() - self.winfo_rootx()
            by = self.btn_settings.winfo_rooty() - self.winfo_rooty()
            bw = self.btn_settings.winfo_width()
            root_w = self.winfo_width()

            x = min(max(8, bx + bw - pw), max(8, root_w - pw - 8))
            y = max(8, by - ph - max(int(6 * scale), 6))
            self.settings_win.place(x=x, y=y, width=pw, height=ph)
            self.settings_win.lift()
        except Exception:
            pass

    def _close_settings_popup(self):
        if self.settings_win and self.settings_win.winfo_exists():
            try:
                self.settings_win.place_forget()
            except Exception:
                pass

    def set_ui_language(self, new_lang):
        if new_lang not in ("ru", "en") or new_lang == self.ui_lang:
            return
        self.toggle_ui_language()

    def toggle_ui_language(self):
        src_canon = "Auto Detect" if self.is_auto_detect else self._lang_to_canonical(self.dd_src.get())
        tgt_raw = self.dd_tgt.get()
        tgt_is_placeholder = tgt_raw in ALL_LANG_PLACEHOLDERS
        tgt_canon = "" if tgt_is_placeholder else self._lang_to_canonical(tgt_raw)

        self.ui_lang = "en" if self.ui_lang == "ru" else "ru"
        self.chk_auto.configure(text=self._tr("auto_trans_chk"))
        self.btn_server.configure(text=self._tr("server_btn"))
        self.btn_instant.configure(text=self._tr("instant_btn"))

        if self.settings_win and self.settings_win.winfo_exists():
            try:
                self.lbl_set_title.configure(text=self._tr("settings_title"))
                self.lbl_set_pin.configure(text=self._tr("settings_pin"))
                self.lbl_set_smart.configure(text="Умный поиск" if self.ui_lang == "ru" else "Smart Search")
                self.lbl_set_lang.configure(text=self._tr("settings_lang"))
                self.btn_lang_ru.configure(
                    fg_color=THEME["bg_accent"] if self.ui_lang == "ru" else THEME["bg_btn"],
                    hover_color=THEME["bg_accent_hover"] if self.ui_lang == "ru" else THEME["bg_btn_hover"]
                )
                self.btn_lang_en.configure(
                    fg_color=THEME["bg_accent"] if self.ui_lang == "en" else THEME["bg_btn"],
                    hover_color=THEME["bg_accent_hover"] if self.ui_lang == "en" else THEME["bg_btn_hover"]
                )
                self._sync_settings_popup_position()
            except Exception:
                pass

        self.dd_src.configure_values(self._get_localized_world_languages())
        self.dd_tgt.configure_values(self._get_localized_target_languages())

        if self.is_auto_detect:
            self.dd_src.set(self._format_auto_detect_display(self.detected_src_lang))
        else:
            self.dd_src.set(self._lang_to_display(src_canon))

        if tgt_is_placeholder or not tgt_canon:
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
        self._refresh_model_dropdown_labels()
        self._rebuild_context_menus()

        if self._tw_mismatch_langs:
            s_c, d_c = self._tw_mismatch_langs
            new_banner, new_status = self._build_mismatch_texts(s_c, d_c)
            self._tw_mismatch_warning = new_banner
            self._tw_final_status_msg = new_status
            if not self._anim_running:
                self._stop_status_anim(new_status, "#f59e0b", 1.0)
        elif not self._anim_running:
            if self._is_online:
                if self._is_valid_model_selected():
                    self._stop_status_anim(self._tr("lms_online"), "#22c55e", 0.0)
                else:
                    self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
            else:
                self._stop_status_anim(self._tr("server_failed"), "#ef4444", 0.0)

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

    def _load_config(self):
        if not os.path.isfile(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            lang = cfg.get("ui_lang", "ru")
            if lang in ("ru", "en") and lang != self.ui_lang:
                self.ui_lang = lang
                self.chk_auto.configure(text=self._tr("auto_trans_chk"))
                self.use_smart_search = bool(cfg.get("smart_search", False))
                self.btn_server.configure(text=self._tr("server_btn"))
                self.btn_instant.configure(text=self._tr("instant_btn"))
                self._set_status_label(self._tr("connecting"), THEME["text_muted"])
                self._rebuild_context_menus()

            self.dd_src.configure_values(self._get_localized_world_languages())
            self.dd_tgt.configure_values(self._get_localized_target_languages())

            src_lang_raw = cfg.get("src_lang", "Auto Detect")
            src_canon = self._lang_to_canonical(src_lang_raw)
            if not src_canon or src_canon == "Auto Detect":
                self.is_auto_detect = True
                self.dd_src.set(self._format_auto_detect_display(None))
            else:
                self.is_auto_detect = False
                self.dd_src.set(self._lang_to_display(src_canon))

            tgt_lang_raw = cfg.get("tgt_lang", "")
            if not tgt_lang_raw or tgt_lang_raw in ALL_LANG_PLACEHOLDERS:
                self.dd_tgt.set(self._tr("select_lang"))
            else:
                tgt_canon = self._lang_to_canonical(tgt_lang_raw)
                self.dd_tgt.set(self._lang_to_display(tgt_canon))

            saved_model = strip_loaded_prefix(cfg.get("model_id", self._tr("select_model")))
            if saved_model and saved_model not in ALL_MODEL_PLACEHOLDERS:
                self._saved_config_model = saved_model

            if cfg.get("auto_translate", True):
                self.chk_auto.select()
            else:
                self.chk_auto.deselect()

            if cfg.get("smart_search", False):
                self.sw_smart.select()
                self.use_smart_search = True
            else:
                self.sw_smart.deselect()
                self.use_smart_search = False

            self.pin_window = bool(cfg.get("pin_window", False))
            self.attributes("-topmost", self.pin_window)
        except Exception:
            pass

    def _save_config(self):
        try:
            src_val = "Auto Detect" if self.is_auto_detect else self._lang_to_canonical(self.dd_src.get())
            tgt_raw = self.dd_tgt.get()
            tgt_val = "" if tgt_raw in ALL_LANG_PLACEHOLDERS else self._lang_to_canonical(tgt_raw)
            clean_m = strip_loaded_prefix(self.model_id)
            model_val = clean_m if clean_m not in ALL_MODEL_PLACEHOLDERS else self._saved_config_model
            cfg = {
                "ui_lang": self.ui_lang,
                "src_lang": src_val,
                "tgt_lang": tgt_val,
                "model_id": model_val,
                "auto_translate": bool(self.chk_auto.get()),
                "smart_search": bool(self.use_smart_search),
                "pin_window": bool(self.pin_window)
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _apply_app_icon(self):
        ico_path = resource_path("logo.ico")
        png_path = resource_path("logo.png")

        def _force_set_icon():
            if IS_WIN and os.path.isfile(ico_path):
                try:
                    self.iconbitmap(default=ico_path)
                    self.iconbitmap(ico_path)
                except Exception:
                    pass

            if os.path.isfile(png_path):
                try:
                    if HAS_PIL:
                        pil_ico = Image.open(png_path).convert("RGBA")
                        self._icon_img_64 = ImageTk.PhotoImage(pil_ico.resize((64, 64), Image.Resampling.LANCZOS))
                        self._icon_img_32 = ImageTk.PhotoImage(pil_ico.resize((32, 32), Image.Resampling.LANCZOS))
                        self.iconphoto(True, self._icon_img_64, self._icon_img_32)
                    else:
                        self._icon_img = tk.PhotoImage(file=png_path)
                        self.iconphoto(True, self._icon_img)
                    return
                except Exception:
                    pass

        _force_set_icon()
        # Перебиваем встроенный таймер CustomTkinter (200мс), который сбрасывает иконку на синий квадрат
        self.after(250, _force_set_icon)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1, uniform="panel")
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1, uniform="panel")
        self.grid_rowconfigure(1, weight=1)

        self.dd_src = SearchableDropdown(
            self, self, self._get_localized_world_languages(), self._tr("auto_detect"),
            command=self._on_src_lang_selected, aliases=LANG_MAP, prefer_upwards=False,
            height=34, allow_custom=True, flag_provider=self._get_flag_photo_for_label
        )
        self.dd_src.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=(12, 6))

        self.dd_tgt = SearchableDropdown(
            self, self, self._get_localized_target_languages(), self._tr("select_lang"),
            command=self._on_tgt_lang_selected, aliases=LANG_MAP, prefer_upwards=False,
            height=34, allow_custom=True, flag_provider=self._get_flag_photo_for_label
        )
        self.dd_tgt.grid(row=0, column=2, sticky="ew", padx=(6, 12), pady=(12, 6))

        self.t_in = ctk.CTkTextbox(
            self,
            font=(UI_FONT, 15),
            fg_color=THEME["bg_card_in"],
            text_color=THEME["text_main"],
            border_width=1,
            border_color=THEME["border_subtle"],
            corner_radius=10,
            undo=True,
            wrap="word"
        )
        self.t_in.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=4)
        self._configure_rich_text_tags(self.t_in._textbox, is_input=True)

        self.mid_bar = ctk.CTkFrame(self, fg_color="transparent", width=44)
        self.mid_bar.grid(row=1, column=1, sticky="ns", pady=4)

        self.btn_swap = ctk.CTkButton(
            self.mid_bar, text="⇄" if not self.ctk_icons["swap"] else "", image=self.ctk_icons["swap"],
            width=38, height=34, corner_radius=8,
            fg_color=THEME["bg_btn"], hover_color=THEME["bg_btn_hover"],
            state="disabled", command=self.swap_languages
        )
        self.btn_swap.pack(pady=(0, 6))

        self.btn_tts = ctk.CTkButton(
            self.mid_bar, text="🔊" if not self.ctk_icons["tts_play"] else "", image=self.ctk_icons["tts_play"],
            width=38, height=34, corner_radius=8,
            fg_color=THEME["bg_btn"], hover_color=THEME["bg_btn_hover"],
            command=self.toggle_tts
        )
        self.btn_tts.pack(pady=6)

        self.btn_go = ctk.CTkButton(
            self.mid_bar, text="❯" if not self.ctk_icons["play"] else "", image=self.ctk_icons["play"],
            width=38, height=88, corner_radius=10,
            fg_color=THEME["bg_accent"], hover_color=THEME["bg_accent_hover"],
            command=self._force_trigger
        )
        self.btn_go.pack(pady=6, expand=True)

        self.btn_stop = ctk.CTkButton(
            self.mid_bar, text="⊘" if not self.ctk_icons["stop"] else "", image=self.ctk_icons["stop"],
            width=38, height=34, corner_radius=8,
            fg_color=THEME["bg_btn"], hover_color=THEME["bg_danger_hover"],
            state="disabled", command=self.stop_translation
        )
        self.btn_stop.pack(pady=(6, 0))

        self.out_container = ctk.CTkFrame(self, fg_color="transparent")
        self.out_container.grid(row=1, column=2, sticky="nsew", padx=(6, 12), pady=4)
        self.out_container.grid_rowconfigure(0, weight=1)
        self.out_container.grid_columnconfigure(0, weight=1)

        self.t_out = ctk.CTkTextbox(
            self.out_container,
            font=(UI_FONT, 15),
            fg_color=THEME["bg_card_out"],
            text_color=THEME["text_main"],
            border_width=1,
            border_color=THEME["border_subtle"],
            corner_radius=10,
            wrap="word"
        )
        self.t_out.grid(row=0, column=0, sticky="nsew")
        self.t_out._textbox.configure(
            insertwidth=0,
            selectbackground=THEME["bg_accent"],
            selectforeground="#ffffff",
            inactiveselectbackground="#1e3a8a",
            exportselection=True
        )
        self._configure_rich_text_tags(self.t_out._textbox, is_input=False)

        self.btn_instant = ctk.CTkButton(
            self.out_container, text=self._tr("instant_btn"), height=30, width=148,
            font=(UI_FONT, 12, "bold"), fg_color=THEME["bg_accent"], hover_color=THEME["bg_accent_hover"],
            corner_radius=7, command=self.skip_typewriter_animation
        )
        self.btn_instant.place_forget()

        self.progress_bar = ctk.CTkProgressBar(
            self, height=4, corner_radius=2,
            progress_color="#3b82f6", fg_color="#181c26"
        )
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(4, 2))
        self.progress_bar.set(0.0)

        self.bot_left = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.bot_left.grid(row=3, column=0, sticky="ew", padx=(12, 6), pady=(4, 12))
        self.bot_left.grid_columnconfigure(1, weight=1)

        self.chk_auto = ctk.CTkCheckBox(
            self.bot_left, text=self._tr("auto_trans_chk"), font=(UI_FONT, 12),
            checkbox_width=18, checkbox_height=18, corner_radius=5,
            command=self._save_config
        )
        self.chk_auto.grid(row=0, column=0, padx=(2, 10))
        self.chk_auto.select()

        self.lbl_status = ctk.CTkLabel(
            self.bot_left, text=self._tr("connecting"), font=(UI_FONT, 12, "bold"),
            text_color=THEME["text_muted"], anchor="e", height=30
        )
        self.lbl_status.grid(row=0, column=1, sticky="ew", padx=(4, 2))
        self.bot_left.bind("<Configure>", lambda e: self._refresh_status_label_ellipsis(), add="+")
        if hasattr(self.lbl_status, "_label"):
            HoverTooltip(self.lbl_status._label, self._get_status_tooltip_if_truncated, delay_ms=400)

        self.bot_right = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.bot_right.grid(row=3, column=2, sticky="ew", padx=(6, 12), pady=(4, 12))
        self.bot_right.grid_columnconfigure(0, weight=1)

        self.dd_model = SearchableDropdown(
            self.bot_right, self, [self._tr("select_model")], self._tr("select_model"),
            command=self.set_model, prefer_upwards=True, height=30, allow_custom=False, font_size=12, flag_provider=None
        )
        self.dd_model.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_refresh = ctk.CTkButton(
            self.bot_right, text="🔄" if not self.ctk_icons["refresh"] else "", image=self.ctk_icons["refresh"],
            width=30, height=30, corner_radius=7,
            fg_color=THEME["bg_btn"], hover_color=THEME["bg_btn_hover"],
            command=lambda: self.fetch_models(auto_start_server=False)
        )
        self.btn_refresh.grid(row=0, column=1, padx=2)

        self.btn_server = ctk.CTkButton(
            self.bot_right, text=self._tr("server_btn"), image=self.ctk_icons["server"], compound="left",
            width=64, height=30, corner_radius=7, font=(UI_FONT, 12, "bold"),
            fg_color=THEME["bg_server"], hover_color=THEME["bg_server_hover"],
            border_width=1, border_color=THEME["border_subtle"],
            command=self.start_lm_studio_server_manual
        )
        self.btn_server.grid(row=0, column=2, padx=2)

        self.btn_load_model = ctk.CTkButton(
            self.bot_right, text="⬇" if not self.ctk_icons.get("model_load") else "", image=self.ctk_icons.get("model_load"),
            width=30, height=30, corner_radius=7,
            fg_color=THEME["bg_btn"], hover_color=THEME["bg_accent"],
            command=self.load_selected_model_to_vram
        )
        self.btn_load_model.grid(row=0, column=3, padx=2)

        self.btn_vram = ctk.CTkButton(
            self.bot_right, text="VRAM", image=self.ctk_icons.get("vram_clean"), compound="left",
            width=62, height=30, corner_radius=7, font=(UI_FONT, 12, "bold"),
            fg_color=THEME["bg_danger"], hover_color=THEME["bg_danger_hover"],
            command=self.unload_vram
        )
        self.btn_vram.grid(row=0, column=3, padx=2)

        self.btn_settings = ctk.CTkButton(
            self.bot_right, text="⚙" if not self.ctk_icons["settings"] else "", image=self.ctk_icons["settings"],
            width=30, height=30, corner_radius=7,
            fg_color=THEME["bg_btn"], hover_color=THEME["bg_btn_hover"],
            command=self._toggle_settings_popup
        )
        self.btn_settings.grid(row=0, column=4, padx=(2, 0))
        # Всплывающие подсказки при долгом наведении
        HoverTooltip(self.btn_swap, lambda: self._tr("tip_swap"), delay_ms=500)
        HoverTooltip(self.btn_tts, lambda: self._tr("tip_tts"), delay_ms=500)
        HoverTooltip(self.btn_go, lambda: self._tr("tip_go"), delay_ms=500)
        HoverTooltip(self.btn_stop, lambda: self._tr("tip_stop"), delay_ms=500)
        HoverTooltip(self.chk_auto, lambda: self._tr("tip_auto_chk"), delay_ms=500)
        HoverTooltip(self.btn_refresh, lambda: self._tr("tip_refresh"), delay_ms=500)
        HoverTooltip(self.btn_server, lambda: self._tr("tip_server"), delay_ms=500)
        HoverTooltip(self.btn_load_model, lambda: self._tr("tip_load_model"), delay_ms=500)
        HoverTooltip(self.btn_vram, lambda: self._tr("tip_vram"), delay_ms=500)
        HoverTooltip(self.btn_settings, lambda: self._tr("tip_settings"), delay_ms=500)

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

    def _mci_send_main_thread(self, cmd):
        """Выполняет команду MCI в главном потоке Tkinter (где есть Windows Message Loop)."""
        if not IS_WIN:
            return ""
        res_holder = [""]
        done_ev = threading.Event()

        def _run():
            try:
                buf = ctypes.create_unicode_buffer(256)
                rc = ctypes.windll.winmm.mciSendStringW(cmd, buf, 256, 0)
                res_holder[0] = f"ERR:{rc}" if rc != 0 else buf.value
            except Exception as e:
                res_holder[0] = f"ERR:{e}"
            finally:
                done_ev.set()

        self.after(0, _run)
        done_ev.wait(timeout=1.5)
        return res_holder[0]

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
        self.btn_tts.configure(
            text="⏹" if not self.ctk_icons["tts_stop"] else "",
            image=self.ctk_icons["tts_stop"],
            fg_color=THEME["bg_accent"],
            hover_color=THEME["bg_accent_hover"]
        )
        self._stop_status_anim(self._tr("tts_speaking"), "#3b82f6", 1.0)

        def tts_worker():
            played_online = False
            tmp_mp3 = os.path.join(tempfile.gettempdir(), f"llm_tts_{os.getpid()}.mp3")
            try:
                sentences = self._split_tts_sentences(clean_speech, max_len=180)
                audio_buffers = [None] * len(sentences)
                ready_events = [threading.Event() for _ in sentences]

                # Параллельная предзагрузка всех фраз в RAM, чтобы не было пауз между предложениями
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
                        self._mci_send_main_thread("close llm_tts")
                        short_p = get_win_short_path(tmp_mp3)
                        open_res = self._mci_send_main_thread(f'open "{short_p}" type mpegvideo alias llm_tts')
                        if open_res.startswith("ERR:"):
                            break

                        self._mci_send_main_thread("setaudio llm_tts volume to 1000")
                        len_str = self._mci_send_main_thread("status llm_tts length")
                        total_ms = int(len_str) if len_str.isdigit() else 0

                        play_res = self._mci_send_main_thread("play llm_tts from 0")
                        if play_res.startswith("ERR:"):
                            self._mci_send_main_thread("close llm_tts")
                            break

                        played_online = True
                        start_t = time.monotonic()
                        max_wait = (total_ms / 1000.0 + 0.4) if total_ms > 0 else 15.0

                        while not self._tts_stop_event.is_set():
                            if time.monotonic() - start_t > max_wait:
                                break
                            pos_str = self._mci_send_main_thread("status llm_tts position")
                            if total_ms > 0 and pos_str.isdigit() and int(pos_str) >= total_ms - 35:
                                break
                            mode_str = self._mci_send_main_thread("status llm_tts mode").lower()
                            if mode_str in ("stopped", "not ready", "") and (time.monotonic() - start_t) > 0.2:
                                break
                            time.sleep(0.03)

                        self._mci_send_main_thread("close llm_tts")
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
                    self._mci_send_main_thread("close llm_tts")
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
                        for cmd in (
                            ["spd-say", "-w", "-l", lang_short, clean_speech],
                            ["espeak-ng", "-v", lang_short, clean_speech],
                            ["espeak", "-v", lang_short, clean_speech],
                        ):
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

            self.after(0, self._reset_tts_ui_after_finish)

        threading.Thread(target=tts_worker, daemon=True).start()

    def _reset_tts_ui_after_finish(self):
        if not self._is_speaking:
            return
        self._is_speaking = False
        self.btn_tts.configure(
            text="🔊" if not self.ctk_icons["tts_play"] else "",
            image=self.ctk_icons["tts_play"],
            fg_color=THEME["bg_btn"],
            hover_color=THEME["bg_btn_hover"]
        )
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
        tmp_mp3 = os.path.join(tempfile.gettempdir(), f"llm_tts_{os.getpid()}.mp3")
        if os.path.exists(tmp_mp3):
            try:
                os.remove(tmp_mp3)
            except Exception:
                pass
        if self._is_speaking:
            self._is_speaking = False
            self.btn_tts.configure(
                text="🔊" if not self.ctk_icons["tts_play"] else "",
                image=self.ctk_icons["tts_play"],
                fg_color=THEME["bg_btn"],
                hover_color=THEME["bg_btn_hover"]
            )
            if show_status and not self._anim_running:
                self._stop_status_anim(self._tr("tts_stopped"), "#eab308", 0.0)

    def _get_status_tooltip_if_truncated(self):
        try:
            shown = self.lbl_status.cget("text")
            if shown and shown.endswith("...") and shown != self._full_status_text:
                return self._full_status_text
        except Exception:
            pass
        return ""

    def _refresh_status_label_ellipsis(self):
        try:
            tk_lbl = getattr(self.lbl_status, "_label", self.lbl_status)
            phys_w = self.lbl_status.winfo_width()
            if phys_w <= 36:
                bot_w = self.bot_left.winfo_width()
                lbl_x = self.lbl_status.winfo_x()
                if bot_w > 120 and lbl_x > 0:
                    phys_w = bot_w - lbl_x - 6

            if phys_w <= 36:
                self.lbl_status.configure(text=self._full_status_text, text_color=self._full_status_color)
                return

            avail_phys_px = max(50, phys_w - 8)
            f_obj = get_tkfont_for_widget(tk_lbl, fallback_family=UI_FONT, fallback_size=-12, fallback_weight="bold")
            short_txt = truncate_text_with_font(self._full_status_text, avail_phys_px, tk_font_obj=f_obj)
            self.lbl_status.configure(text=short_txt, text_color=self._full_status_color)
        except Exception:
            try:
                self.lbl_status.configure(text=self._full_status_text, text_color=self._full_status_color)
            except Exception:
                pass

    def _set_status_label(self, full_text, color):
        self._full_status_text = full_text
        self._full_status_color = color
        self._refresh_status_label_ellipsis()

    def _configure_rich_text_tags(self, tb, is_input=False):
        tb.tag_config("warn_banner", font=(UI_FONT, 13, "bold"), foreground="#f59e0b")
        tb.tag_config("main_trans", font=(UI_FONT, 15), foreground="#ffffff")
        tb.tag_config("dict_title", font=(UI_FONT, 13, "italic"), foreground="#8a8a8a")
        tb.tag_config("pos_header", font=(UI_FONT, 14, "bold"), foreground="#3b82f6")
        tb.tag_config("idiom_header", font=(UI_FONT, 14, "bold"), foreground="#a855f7")
        tb.tag_config("native_header", font=(UI_FONT, 14, "bold"), foreground="#10b981")
        tb.tag_config("dict_pending_dots", font=(UI_FONT, 16, "bold"), foreground="#3b82f6")
        tb.tag_config("dict_body", font=(UI_FONT, 13), foreground="#d4d4d4")

        tb.tag_config("md_bold", font=(UI_FONT, 15, "bold"), foreground="#ffffff")
        tb.tag_config("md_italic", font=(UI_FONT, 15, "italic"), foreground="#f3f4f6")
        tb.tag_config("md_bold_italic", font=(UI_FONT, 15, "bold italic"), foreground="#ffffff")
        tb.tag_config("md_code", font=(MONO_FONT, 14, "bold"), background="#242936", foreground="#93c5fd")
        tb.tag_config("md_codeblock", font=(MONO_FONT, 14), background="#1c212c", foreground="#60a5fa")
        tb.tag_config("md_strike", font=(UI_FONT, 15, "overstrike"), foreground="#9ca3af")
        tb.tag_config("md_underline", font=(UI_FONT, 15, "underline"), foreground="#ffffff")
        tb.tag_config("md_header", font=(UI_FONT, 17, "bold"), foreground="#60a5fa")
        tb.tag_config("md_quote", font=(UI_FONT, 15, "italic"), foreground="#9ca3af")

        if is_input:
            tb.tag_config("md_syntax_hidden", elide=True)
            tb.tag_config("md_syntax_active", foreground="#52525b")

    def _apply_live_input_markdown(self):
        tb = self.t_in._textbox
        raw = tb.get("1.0", "end-1c")

        for tag in (
            "md_bold", "md_italic", "md_bold_italic", "md_code", "md_codeblock",
            "md_strike", "md_underline", "md_header", "md_quote",
            "md_syntax_hidden", "md_syntax_active"
        ):
            tb.tag_remove(tag, "1.0", "end")

        if not raw:
            return

        try:
            ins_line, ins_col = map(int, tb.index("insert").split("."))
            lines_before = raw.split("\n")[:ins_line - 1]
            cursor_offset = sum(len(l) + 1 for l in lines_before) + ins_col
        except Exception:
            cursor_offset = -1

        offset = 0
        for line in raw.split("\n"):
            line_len = len(line)
            h_m = re.match(r"^(#{1,3}\s+)(.+)$", line)
            if h_m:
                p_len = len(h_m.group(1))
                s_idx = f"1.0+{offset}c"
                m_idx = f"1.0+{offset + p_len}c"
                e_idx = f"1.0+{offset + line_len}c"
                tb.tag_add("md_header", m_idx, e_idx)
                syn_tag = "md_syntax_active" if (offset <= cursor_offset <= offset + line_len) else "md_syntax_hidden"
                tb.tag_add(syn_tag, s_idx, m_idx)
            else:
                q_m = re.match(r"^(>\s+)(.+)$", line)
                if q_m:
                    p_len = len(q_m.group(1))
                    s_idx = f"1.0+{offset}c"
                    m_idx = f"1.0+{offset + p_len}c"
                    e_idx = f"1.0+{offset + line_len}c"
                    tb.tag_add("md_quote", m_idx, e_idx)
                    syn_tag = "md_syntax_active" if (offset <= cursor_offset <= offset + line_len) else "md_syntax_hidden"
                    tb.tag_add(syn_tag, s_idx, m_idx)
            offset += line_len + 1

        for m in RE_MD_TOKEN.finditer(raw):
            st, en = m.span()
            token = m.group(0)
            cursor_inside = (st <= cursor_offset <= en)
            syn_tag = "md_syntax_active" if cursor_inside else "md_syntax_hidden"

            if token.startswith("```") and token.endswith("```") and len(token) > 6:
                d_len, style_tag = 3, "md_codeblock"
            elif token.startswith("`") and token.endswith("`") and len(token) > 2:
                d_len, style_tag = 1, "md_code"
            elif token.startswith("***") and token.endswith("***") and len(token) > 6:
                d_len, style_tag = 3, "md_bold_italic"
            elif (token.startswith("**") and token.endswith("**")) or (token.startswith("__") and token.endswith("__")):
                d_len, style_tag = 2, "md_bold"
            elif (token.startswith("*") and token.endswith("*")) or (token.startswith("_") and token.endswith("_")):
                d_len, style_tag = 1, "md_italic"
            elif token.startswith("~~") and token.endswith("~~") and len(token) > 4:
                d_len, style_tag = 2, "md_strike"
            elif token.startswith("++") and token.endswith("++") and len(token) > 4:
                d_len, style_tag = 2, "md_underline"
            else:
                continue

            tb.tag_add(syn_tag, f"1.0+{st}c", f"1.0+{st + d_len}c")
            tb.tag_add(style_tag, f"1.0+{st + d_len}c", f"1.0+{en - d_len}c")
            tb.tag_add(syn_tag, f"1.0+{en - d_len}c", f"1.0+{en}c")

    def _insert_markdown_styled_text(self, tb, text, default_tag="main_trans"):
        lines = text.split("\n")
        for l_idx, line in enumerate(lines):
            if l_idx > 0:
                tb.insert("end", "\n", default_tag)

            base_tag = default_tag
            work_line = line
            h_m = re.match(r"^#{1,3}\s+(.+)$", work_line)
            if h_m:
                base_tag = "md_header"
                work_line = h_m.group(1)
            else:
                q_m = re.match(r"^>\s+(.+)$", work_line)
                if q_m:
                    base_tag = "md_quote"
                    work_line = "▎ " + q_m.group(1)

            last_idx = 0
            for m in RE_MD_TOKEN.finditer(work_line):
                st, en = m.span()
                if st > last_idx:
                    tb.insert("end", work_line[last_idx:st], base_tag)

                token = m.group(0)
                if token.startswith("```") and token.endswith("```") and len(token) > 6:
                    tb.insert("end", token[3:-3], "md_codeblock")
                elif token.startswith("`") and token.endswith("`") and len(token) > 2:
                    tb.insert("end", token[1:-1], "md_code")
                elif token.startswith("***") and token.endswith("***") and len(token) > 6:
                    tb.insert("end", token[3:-3], "md_bold_italic")
                elif (token.startswith("**") and token.endswith("**")) or (token.startswith("__") and token.endswith("__")):
                    tb.insert("end", token[2:-2], "md_bold")
                elif (token.startswith("*") and token.endswith("*")) or (token.startswith("_") and token.endswith("_")):
                    tb.insert("end", token[1:-1], "md_italic")
                elif token.startswith("~~") and token.endswith("~~") and len(token) > 4:
                    tb.insert("end", token[2:-2], "md_strike")
                elif token.startswith("++") and token.endswith("++") and len(token) > 4:
                    tb.insert("end", token[2:-2], "md_underline")
                else:
                    tb.insert("end", token, base_tag)

                last_idx = en

            if last_idx < len(work_line):
                tb.insert("end", work_line[last_idx:], base_tag)

    def _format_model_display(self, model_name):
        clean = strip_loaded_prefix(model_name)
        if clean in ALL_MODEL_PLACEHOLDERS or not clean:
            return clean
        return f"{LOADED_PREFIX}{clean}" if clean in self._loaded_vram_models else clean

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

    def _query_lms_ps_loaded_models(self):
        loaded = set()
        try:
            res = subprocess.run(
                [LMS_BIN, "ps"],
                shell=False,
                timeout=5,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WIN else 0
            )
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
        if not clean_target or clean_target in ALL_MODEL_PLACEHOLDERS:
            return
        if clean_target not in self._loaded_vram_models:
            return
        for _ in range(2):
            self._run_lms_cmd(["unload", clean_target], timeout=10)
            currently_loaded = self._query_lms_ps_loaded_models()
            if clean_target not in currently_loaded:
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

    def _toggle_pin(self):
        if hasattr(self, "sw_pin") and self.sw_pin.winfo_exists():
            self.pin_window = bool(self.sw_pin.get())
        else:
            self.pin_window = not self.pin_window
        self.attributes("-topmost", self.pin_window)
        self._save_config()

    def _on_src_lang_selected(self, val):
        canon = self._lang_to_canonical(val)
        if canon == "Auto Detect":
            self.is_auto_detect = True
            self.detected_src_lang = None
            self.dd_src.set(self._format_auto_detect_display(None))
        else:
            self.is_auto_detect = False
            self.detected_src_lang = None
            self.dd_src.set(self._lang_to_display(canon))
        self._update_swap_button_state()
        self._save_config()
        if self.chk_auto.get():
            self._force_trigger()

    def _on_tgt_lang_selected(self, val):
        if val not in ALL_LANG_PLACEHOLDERS:
            canon = self._lang_to_canonical(val)
            if canon == "Auto Detect":
                self.dd_tgt.set(self._tr("select_lang"))
            else:
                self.dd_tgt.set(self._lang_to_display(canon))
        self._update_swap_button_state()
        self._save_config()
        if self.chk_auto.get():
            self._force_trigger()

    def _get_effective_src_mode(self):
        return "Auto Detect" if self.is_auto_detect else self._lang_to_canonical(self.dd_src.get())

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
        if not tgt_canon or tgt_canon == "Auto Detect":
            self.btn_swap.configure(state="disabled")
            return

        if self.is_auto_detect:
            can_swap = bool(self.detected_src_lang) and (self.detected_src_lang != tgt_canon)
        else:
            src_canon = self._get_effective_src_mode()
            can_swap = bool(src_canon) and (src_canon != "Auto Detect") and (src_canon != tgt_canon)

        self.btn_swap.configure(state="normal" if can_swap else "disabled")

    def _toggle_smart_search(self):
        if hasattr(self, "sw_smart") and self.sw_smart.winfo_exists():
            self.use_smart_search = bool(self.sw_smart.get())
        else:
            self.use_smart_search = not self.use_smart_search
        self._save_config()

    def _start_status_anim(self, phase_text, color="#eab308", bar_color="#eab308"):
        self._anim_phase_text = phase_text
        self._anim_color = color
        self._anim_start_ts = time.monotonic()
        self.progress_bar.configure(progress_color=bar_color)
        if not self._anim_running:
            self._anim_running = True
            self._tick_status_anim()

    def _update_status_anim_phase(self, phase_text, color="#3b82f6", bar_color="#3b82f6"):
        self._anim_phase_text = phase_text
        self._anim_color = color
        self.progress_bar.configure(progress_color=bar_color)

    def _stop_status_anim(self, final_text, color="#22c55e", bar_fill=1.0):
        self._anim_running = False
        self._set_status_label(final_text, color)
        self.progress_bar.configure(progress_color=color if bar_fill > 0 else "#181c26")
        self.progress_bar.set(bar_fill)

    def _tick_status_anim(self):
        if not self._anim_running:
            return
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner = frames[self._anim_step % len(frames)]
        elapsed = time.monotonic() - self._anim_start_ts

        pos = (self._anim_step % 40) / 40.0
        wave = pos * 2 if pos <= 0.5 else (1.0 - pos) * 2
        self.progress_bar.set(0.15 + wave * 0.75)

        unit = "s" if self.ui_lang == "en" else "с"
        self._set_status_label(
            f"{spinner} {self._anim_phase_text} ({elapsed:.1f}{unit})",
            self._anim_color
        )
        self._anim_step += 1
        self.after(80, self._tick_status_anim)

    def _rebuild_context_menus(self):
        inner_in = self.t_in._textbox
        inner_out = self.t_out._textbox

        if not hasattr(self, "ctx_menu_in") or self.ctx_menu_in is None:
            self.ctx_menu_in = tk.Menu(self, tearoff=0, bg="#181b24", fg="white", activebackground=THEME["bg_accent"], font=(UI_FONT, 10))
        else:
            self.ctx_menu_in.delete(0, "end")

        self.ctx_menu_in.add_command(label=self._tr("ctx_paste_cur"), command=lambda: self._paste_into_textbox(replace_all=False))
        self.ctx_menu_in.add_command(label=self._tr("ctx_paste_rep"), command=self.paste_to_input)
        self.ctx_menu_in.add_separator()
        self.ctx_menu_in.add_command(label=self._tr("ctx_copy"), command=lambda: self._copy_from_widget(inner_in))
        self.ctx_menu_in.add_command(label=self._tr("ctx_cut"), command=self._cut_from_input)
        self.ctx_menu_in.add_command(label=self._tr("ctx_sel_all"), command=lambda: self._select_all_widget(inner_in))
        self.ctx_menu_in.add_separator()
        self.ctx_menu_in.add_command(label=self._tr("ctx_bold"), command=lambda: self._wrap_input_selection("**", "**"))
        self.ctx_menu_in.add_command(label=self._tr("ctx_italic"), command=lambda: self._wrap_input_selection("*", "*"))
        self.ctx_menu_in.add_command(label=self._tr("ctx_code"), command=lambda: self._wrap_input_selection("`", "`"))
        self.ctx_menu_in.add_command(label=self._tr("ctx_strike"), command=lambda: self._wrap_input_selection("~~", "~~"))
        self.ctx_menu_in.add_separator()
        self.ctx_menu_in.add_command(label=self._tr("ctx_clear"), command=self.clear_all)

        if not hasattr(self, "ctx_menu_out") or self.ctx_menu_out is None:
            self.ctx_menu_out = tk.Menu(self, tearoff=0, bg="#181b24", fg="white", activebackground=THEME["bg_accent"], font=(UI_FONT, 10))
        else:
            self.ctx_menu_out.delete(0, "end")

        self.ctx_menu_out.add_command(label=self._tr("ctx_copy_sel"), command=lambda: self._copy_from_widget(inner_out, fallback_all=True))
        self.ctx_menu_out.add_command(label=self._tr("ctx_copy_all"), command=self.copy_output)
        self.ctx_menu_out.add_separator()
        self.ctx_menu_out.add_command(label=self._tr("ctx_sel_all"), command=lambda: self._select_all_widget(inner_out))

        if not hasattr(self, "ctx_menu_entry") or self.ctx_menu_entry is None:
            self.ctx_menu_entry = tk.Menu(self, tearoff=0, bg="#181b24", fg="white", activebackground=THEME["bg_accent"], font=(UI_FONT, 10))
        else:
            self.ctx_menu_entry.delete(0, "end")

        self.ctx_menu_entry.add_command(label=self._tr("ctx_paste_cur"), command=lambda: self._entry_paste(self._active_entry_for_menu))
        self.ctx_menu_entry.add_command(label=self._tr("ctx_copy"), command=lambda: self._entry_copy(self._active_entry_for_menu))
        self.ctx_menu_entry.add_command(label=self._tr("ctx_cut"), command=lambda: self._entry_cut(self._active_entry_for_menu))
        self.ctx_menu_entry.add_separator()
        self.ctx_menu_entry.add_command(label=self._tr("ctx_sel_all"), command=lambda: self._entry_select_all(self._active_entry_for_menu))

    def _setup_bindings(self):
        self.bind("<Button-1>", self._check_outside_click, add="+")
        self.bind("<Configure>", self._on_window_configure, add="+")
        self.bind("<Unmap>", self._on_window_unmap, add="+")
        self.bind("<FocusOut>", self._on_app_focus_out, add="+")

        self.bind_all("<Control-KeyPress>", self._global_ctrl_key_router)

        inner_in = self.t_in._textbox
        inner_in.bind("<FocusIn>", lambda e: self.t_in.configure(border_color=THEME["border_focus"]), add="+")
        inner_in.bind("<FocusOut>", lambda e: self.t_in.configure(border_color=THEME["border_subtle"]), add="+")
        inner_in.bind("<KeyPress>", self._mark_edited)
        inner_in.bind("<KeyRelease>", self._on_input_key_release)
        inner_in.bind("<ButtonRelease-1>", lambda e: self.after(10, self._apply_live_input_markdown))
        inner_in.bind("<Control-Return>", lambda e: self._force_trigger())
        inner_in.bind("<<Paste>>", self._on_native_paste_in)
        inner_in.bind("<<Cut>>", self._on_native_cut_in)
        inner_in.bind("<<Copy>>", lambda e: self._on_native_copy(inner_in, fallback_all=False))

        inner_out = self.t_out._textbox
        inner_out.bind("<Button-1>", lambda e: inner_out.focus_set(), add="+")
        inner_out.bind("<ButtonRelease-1>", self._remember_output_selection, add="+")
        inner_out.bind("<B1-Motion>", self._remember_output_selection, add="+")
        inner_out.bind("<KeyPress>", self._guard_output_keypress)
        inner_out.bind("<<Copy>>", lambda e: self._on_native_copy(inner_out, fallback_all=True))
        inner_out.bind("<<Paste>>", lambda e: "break")
        inner_out.bind("<<Cut>>", lambda e: "break")

        self._active_entry_for_menu = None
        self._rebuild_context_menus()

        for w_in in (self.t_in, inner_in):
            w_in.bind("<Button-3>", self._show_in_context_menu)
            if IS_MAC:
                w_in.bind("<Button-2>", self._show_in_context_menu)

        for w_out in (self.t_out, inner_out):
            w_out.bind("<Button-3>", self._show_out_context_menu)
            if IS_MAC:
                w_out.bind("<Button-2>", self._show_out_context_menu)

        for dd in (self.dd_src, self.dd_tgt, self.dd_model):
            tk_ent = dd.entry._entry
            tk_ent.bind("<<Paste>>", lambda e, ent=tk_ent, d=dd: self._entry_paste(ent, d))
            tk_ent.bind("<<Cut>>", lambda e, ent=tk_ent, d=dd: self._entry_cut(ent, d))
            tk_ent.bind("<<Copy>>", lambda e, ent=tk_ent: self._entry_copy(ent))
            tk_ent.bind("<Button-3>", lambda e, ent=tk_ent: self._popup_entry_menu(ent, e))

    def _remember_output_selection(self, event=None):
        tb = self.t_out._textbox
        try:
            sel = tb.get("sel.first", "sel.last")
            self._last_selected_out_text = sel if sel else ""
        except tk.TclError:
            self._last_selected_out_text = ""

    def _on_native_copy(self, tb, fallback_all=False):
        self._copy_from_widget(tb, fallback_all=fallback_all)
        return "break"

    def _show_in_context_menu(self, event):
        self._close_all_dropdowns()
        self.t_in._textbox.focus_set()
        try:
            self.ctx_menu_in.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx_menu_in.grab_release()
        return "break"

    def _show_out_context_menu(self, event):
        self._close_all_dropdowns()
        try:
            sel = self.t_out._textbox.get("sel.first", "sel.last")
            if sel:
                self._last_selected_out_text = sel
        except tk.TclError:
            pass
        self.t_out._textbox.focus_set()
        try:
            self.ctx_menu_out.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx_menu_out.grab_release()
        return "break"

    def _popup_entry_menu(self, tk_ent, event):
        self._active_entry_for_menu = tk_ent
        tk_ent.focus_set()
        try:
            self.ctx_menu_entry.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx_menu_entry.grab_release()
        return "break"

    @staticmethod
    def _match_hotkey_action(event):
        kc = event.keycode
        ks = (event.keysym or "").lower()
        if IS_WIN:
            is_copy = (kc == 67)
            is_paste = (kc == 86)
            is_cut = (kc == 88)
            is_sel_all = (kc == 65)
            is_undo = (kc == 90)
            is_redo = (kc == 89)
        else:
            is_copy = (kc == 54)
            is_paste = (kc == 55)
            is_cut = (kc == 53)
            is_sel_all = (kc == 38)
            is_undo = (kc == 52)
            is_redo = (kc == 29)

        is_copy = is_copy or ks in ("c", "с", "cyrillic_es")
        is_paste = is_paste or ks in ("v", "м", "cyrillic_em")
        is_cut = is_cut or ks in ("x", "ч", "cyrillic_che")
        is_sel_all = is_sel_all or ks in ("a", "ф", "cyrillic_ef")
        is_undo = is_undo or ks in ("z", "я", "cyrillic_ya")
        is_redo = is_redo or ks in ("y", "н", "cyrillic_en")
        return is_copy, is_paste, is_cut, is_sel_all, is_undo, is_redo

    def _guard_output_keypress(self, event):
        if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return None
        if event.state & 0x4:
            is_copy, _, _, is_sel_all, _, _ = self._match_hotkey_action(event)
            if is_copy:
                self._copy_from_widget(self.t_out._textbox, fallback_all=True)
                return "break"
            if is_sel_all:
                self._select_all_widget(self.t_out._textbox)
                return "break"
        return "break"

    def _global_ctrl_key_router(self, event):
        is_copy, is_paste, is_cut, is_sel_all, is_undo, is_redo = self._match_hotkey_action(event)
        if not (is_copy or is_paste or is_cut or is_sel_all or is_undo or is_redo):
            return None

        focused = self.focus_get()
        if focused is None:
            return None

        inner_in = self.t_in._textbox
        inner_out = self.t_out._textbox

        if focused is inner_in or focused is self.t_in:
            if is_paste:
                self._paste_into_textbox(replace_all=False)
                return "break"
            elif is_copy:
                self._copy_from_widget(inner_in)
                return "break"
            elif is_cut:
                self._cut_from_input()
                return "break"
            elif is_sel_all:
                self._select_all_widget(inner_in)
                return "break"
            elif is_undo:
                try:
                    inner_in.edit_undo()
                    self._mark_edited()
                    self.after(10, self._apply_live_input_markdown)
                except Exception:
                    pass
                return "break"
            elif is_redo:
                try:
                    inner_in.edit_redo()
                    self._mark_edited()
                    self.after(10, self._apply_live_input_markdown)
                except Exception:
                    pass
                return "break"

        if focused is inner_out or focused is self.t_out:
            if is_copy:
                self._copy_from_widget(inner_out, fallback_all=True)
                return "break"
            elif is_sel_all:
                self._select_all_widget(inner_out)
                return "break"
            elif is_paste or is_cut or is_undo or is_redo:
                return "break"

        for dd in (self.dd_src, self.dd_tgt, self.dd_model):
            if focused is dd.entry._entry or focused is dd.entry:
                ent = dd.entry._entry
                if is_paste:
                    self._entry_paste(ent, dd)
                    return "break"
                elif is_copy:
                    self._entry_copy(ent)
                    return "break"
                elif is_cut:
                    self._entry_cut(ent, dd)
                    return "break"
                elif is_sel_all:
                    self._entry_select_all(ent)
                    return "break"

        return None

    def _get_clipboard_safe(self):
        try:
            val = self.clipboard_get()
            if val:
                return val
        except Exception:
            pass
        if IS_LINUX:
            for cmd in (["wl-paste", "-n"], ["xclip", "-selection", "clipboard", "-o"], ["xsel", "-ob"]):
                if shutil.which(cmd[0]):
                    try:
                        res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
                        if res.returncode == 0 and res.stdout:
                            return res.stdout
                    except Exception:
                        pass
        if pyperclip is not None:
            try:
                return pyperclip.paste()
            except Exception:
                pass
        return ""

    def _set_clipboard(self, text):
        if not text:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update_idletasks()
        except Exception:
            pass
        if IS_LINUX:
            for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-ib"]):
                if shutil.which(cmd[0]):
                    try:
                        subprocess.run(cmd, input=text, text=True, timeout=1.5)
                        break
                    except Exception:
                        pass
        if pyperclip is not None:
            try:
                pyperclip.copy(text)
            except Exception:
                pass

    def _entry_copy(self, tk_ent):
        if not tk_ent:
            return "break"
        try:
            if tk_ent.selection_present():
                sel = tk_ent.selection_get()
            else:
                sel = tk_ent.get()
            self._set_clipboard(sel)
        except Exception:
            pass
        return "break"

    def _entry_paste(self, tk_ent, dd=None):
        if not tk_ent:
            return "break"
        clip = self._get_clipboard_safe()
        if not clip:
            return "break"
        clip_single = clip.replace("\r", " ").replace("\n", " ").strip()
        if dd is None:
            for cand in (self.dd_src, self.dd_tgt, self.dd_model):
                if tk_ent is cand.entry._entry:
                    dd = cand
                    break
        if dd is not None and not dd._is_editing:
            dd._is_editing = True
            tk_ent.delete(0, "end")
        try:
            if tk_ent.selection_present():
                tk_ent.delete("sel.first", "sel.last")
        except Exception:
            pass
        tk_ent.insert("insert", clip_single)
        if dd is not None:
            dd.trigger_filter_from_entry()
        return "break"

    def _entry_cut(self, tk_ent, dd=None):
        if not tk_ent:
            return "break"
        try:
            if tk_ent.selection_present():
                sel = tk_ent.selection_get()
                self._set_clipboard(sel)
                tk_ent.delete("sel.first", "sel.last")
                if dd is not None:
                    dd.trigger_filter_from_entry()
        except Exception:
            pass
        return "break"

    def _entry_select_all(self, tk_ent):
        if not tk_ent:
            return "break"
        try:
            tk_ent.select_range(0, "end")
            tk_ent.icursor("end")
        except Exception:
            pass
        return "break"

    def _wrap_input_selection(self, prefix, suffix):
        tb = self.t_in._textbox
        try:
            sel = tb.get("sel.first", "sel.last")
            tb.delete("sel.first", "sel.last")
            tb.insert("insert", f"{prefix}{sel}{suffix}")
        except tk.TclError:
            tb.insert("insert", f"{prefix}{suffix}")
            tb.mark_set("insert", f"insert-{len(suffix)}c")
        self._mark_edited()
        self._apply_live_input_markdown()

    def _on_input_key_release(self, event=None):
        self._mark_edited(event)
        self._apply_live_input_markdown()

    def _on_native_paste_in(self, event=None):
        self._paste_into_textbox(replace_all=False)
        return "break"

    def _on_native_cut_in(self, event=None):
        self._cut_from_input()
        return "break"

    def _on_window_unmap(self, event=None):
        if event is not None and event.widget is self:
            self._close_all_dropdowns()

    @staticmethod
    def _is_event_inside_widget(event, target_widget):
        if target_widget is None or not target_widget.winfo_exists():
            return False
        try:
            curr = event.widget
            while curr is not None:
                if curr is target_widget:
                    return True
                curr = getattr(curr, "master", None)
            if str(event.widget).startswith(str(target_widget)):
                return True
            if target_widget.winfo_ismapped():
                wx = target_widget.winfo_rootx()
                wy = target_widget.winfo_rooty()
                ww = target_widget.winfo_width()
                wh = target_widget.winfo_height()
                if wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh:
                    return True
        except Exception:
            pass
        return False

    def _on_window_unmap(self, event=None):
        if event is not None and event.widget is self:
            self._close_all_dropdowns()

    def _on_app_focus_out(self, event=None):
        def check_focus():
            try:
                if self.focus_displayof() is None or self.state() == "iconic" or not self.winfo_viewable():
                    self._close_all_dropdowns()
            except Exception:
                self._close_all_dropdowns()
        self.after(40, check_focus)

    def _on_window_configure(self, event=None):
        if event is not None and event.widget is not self:
            return
        if self.state() == "iconic" or not self.winfo_viewable():
            self._close_all_dropdowns()
            return
        rect = (self.winfo_x(), self.winfo_y(), self.winfo_width(), self.winfo_height())
        if rect == self._last_win_rect:
            return
        self._last_win_rect = rect
        for dd in (self.dd_src, self.dd_tgt, self.dd_model):
            dd._refresh_display_text()
            if dd._popup_open and dd.dropdown_win and dd.dropdown_win.winfo_exists():
                dd.sync_position()
        if self.settings_win and self.settings_win.winfo_exists() and self.settings_win.winfo_ismapped():
            self._sync_settings_popup_position()
        self._refresh_status_label_ellipsis()

    def _close_all_dropdowns(self, except_dd=None):
        for dd in (self.dd_src, self.dd_tgt, self.dd_model):
            if dd is not except_dd:
                dd.close_dropdown()
        if except_dd != "settings":
            self._close_settings_popup()

    def _mark_edited(self, event=None):
        if event and event.keysym in ("Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R", "Left", "Right", "Up", "Down"):
            return
        self._last_edit_time = time.monotonic()

    def _realtime_watcher(self):
        try:
            if self.state() == "iconic" or not self.winfo_viewable():
                self._close_all_dropdowns()

            current_text = self.t_in.get("0.0", "end-1c").strip()
            elapsed = time.monotonic() - self._last_edit_time

            if not current_text:
                if self._last_translated_state[0] != "" or self.detected_src_lang is not None:
                    self._abort_active_stream()
                    self.stop_tts()
                    self._last_translated_state = ("", "", "", "")
                    self._last_clean_translation = ""
                    self._last_selected_out_text = ""
                    self._tw_mismatch_langs = None
                    if self.is_auto_detect:
                        self.detected_src_lang = None
                        self.dd_src.set(self._format_auto_detect_display(None))
                    self._update_swap_button_state()
                    self.t_out._textbox.delete("1.0", "end")
                    self.btn_instant.place_forget()
                    self._stop_status_anim(self._tr("ready"), "#22c55e", 0.0)
            elif self.chk_auto.get() and self._is_online:
                tgt_canon = self._get_effective_tgt_lang()
                if not tgt_canon:
                    self._stop_status_anim(self._tr("choose_lang_right"), "#eab308", 0.0)
                elif not self._is_valid_model_selected():
                    self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
                else:
                    src_mode = self._get_effective_src_mode()
                    current_state = (current_text, src_mode, tgt_canon, strip_loaded_prefix(self.model_id))
                    if current_state != self._last_translated_state and elapsed >= 0.35:
                        self._last_translated_state = current_state
                        self.start_translation()
        except Exception:
            pass
        finally:
            self.after(120, self._realtime_watcher)

    def _auto_reconnect_loop(self):
        if not self._is_online and not self._server_booting:
            self.fetch_models(silent=True, auto_start_server=False)
        self.after(5000, self._auto_reconnect_loop)

    def _force_trigger(self):
        text = self.t_in.get("0.0", "end-1c").strip()
        if not text:
            return
        tgt_canon = self._get_effective_tgt_lang()
        if not tgt_canon:
            self._stop_status_anim(self._tr("choose_lang_right"), "#eab308", 0.0)
            return
        if not self._is_valid_model_selected():
            self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
            return
        src_mode = self._get_effective_src_mode()
        self._last_translated_state = (text, src_mode, tgt_canon, strip_loaded_prefix(self.model_id))
        self.start_translation()

    def _check_outside_click(self, event):
        if self.settings_win and self.settings_win.winfo_exists() and self.settings_win.winfo_ismapped():
            if not (
                self._is_event_inside_widget(event, self.settings_win)
                or self._is_event_inside_widget(event, self.btn_settings)
            ):
                self._close_settings_popup()

        for dd in (self.dd_src, self.dd_tgt, self.dd_model):
            if dd._popup_open and dd.dropdown_win and dd.dropdown_win.winfo_exists():
                if (
                    self._is_event_inside_widget(event, dd.dropdown_win)
                    or self._is_event_inside_widget(event, dd)
                ):
                    return
                dd.close_dropdown()

    def _select_all_widget(self, tb):
        try:
            tb.focus_set()
            tb.tag_add("sel", "1.0", "end-1c")
            tb.mark_set("insert", "end-1c")
            if tb is self.t_out._textbox:
                self._remember_output_selection()
        except Exception:
            pass

    def _copy_from_widget(self, tb, fallback_all=False):
        sel = ""
        try:
            if tb.tag_ranges("sel"):
                sel = tb.get("sel.first", "sel.last")
        except tk.TclError:
            sel = ""

        if not sel and tb is self.t_out._textbox and self._last_selected_out_text:
            sel = self._last_selected_out_text

        if sel:
            self._set_clipboard(sel)
            self._stop_status_anim(self._tr("copied_sel"), "#3b82f6", 1.0)
            return

        if fallback_all:
            self.copy_output()

    def _cut_from_input(self):
        tb = self.t_in._textbox
        try:
            sel = tb.get("sel.first", "sel.last")
            self._set_clipboard(sel)
            tb.delete("sel.first", "sel.last")
            self._mark_edited()
            self._apply_live_input_markdown()
        except tk.TclError:
            pass

    def _paste_into_textbox(self, replace_all=False):
        clip = self._get_clipboard_safe()
        if not clip:
            return
        tb = self.t_in._textbox
        tb.focus_set()
        if replace_all:
            tb.delete("1.0", "end")
            tb.insert("1.0", clip)
        else:
            try:
                tb.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            tb.insert("insert", clip)
        self._mark_edited()
        self._apply_live_input_markdown()

    def paste_to_input(self):
        clip = self._get_clipboard_safe()
        if clip:
            self._paste_into_textbox(replace_all=True)
            if self.chk_auto.get():
                self._force_trigger()

    def _extract_clean_main_output(self):
        if self._last_clean_translation:
            return self._last_clean_translation
        text = self.t_out.get("0.0", "end-1c").strip()
        if not text:
            return ""
        for wp in (UI_STRINGS["ru"]["warn_prefix"], UI_STRINGS["en"]["warn_prefix"]):
            if text.startswith(wp) and "\n\n" in text:
                text = text.split("\n\n", 1)[1].strip()
        for dv in (UI_STRINGS["ru"]["dict_variants"], UI_STRINGS["en"]["dict_variants"]):
            if f" — {dv}\n" in text:
                return text.split("\n\n")[0].strip()
        return text

    def copy_output(self):
        try:
            if self.t_out._textbox.tag_ranges("sel"):
                sel = self.t_out._textbox.get("sel.first", "sel.last")
                if sel.strip():
                    self._set_clipboard(sel)
                    self._stop_status_anim(self._tr("copied_sel"), "#3b82f6", 1.0)
                    return
        except Exception:
            pass

        main_trans = self._extract_clean_main_output()
        if main_trans:
            self._set_clipboard(main_trans)
            self._stop_status_anim(self._tr("copied"), "#3b82f6", 1.0)

    def _abort_active_stream(self):
        self._task_id += 1
        self._tw_running = False
        self.btn_instant.place_forget()
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
        self._last_selected_out_text = ""
        self._tw_main_target = ""
        self._tw_dict_sections = []
        self._tw_mismatch_warning = ""
        self._tw_mismatch_langs = None
        self._tw_final_status_msg = ""
        if self.is_auto_detect:
            self.detected_src_lang = None
            self.dd_src.set(self._format_auto_detect_display(None))
        self._update_swap_button_state()
        self.t_in.delete("0.0", "end")
        self.t_out._textbox.delete("1.0", "end")
        self.btn_go.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._stop_status_anim(self._tr("ready"), "#22c55e" if self._is_online else THEME["text_muted"], 0.0)

    def swap_languages(self):
        tgt_canon = self._get_effective_tgt_lang()
        if not tgt_canon or tgt_canon == "Auto Detect":
            return

        src_canon = self.detected_src_lang if self.is_auto_detect else self._get_effective_src_mode()
        if not src_canon or src_canon == "Auto Detect":
            return

        self.skip_typewriter_animation()
        self.stop_tts()
        self.is_auto_detect = False
        self.detected_src_lang = None
        self.dd_src.set(self._lang_to_display(tgt_canon))
        self.dd_tgt.set(self._lang_to_display(src_canon))
        self._update_swap_button_state()
        self._save_config()

        main_part = self._extract_clean_main_output()
        if main_part:
            self.t_in.delete("0.0", "end")
            self.t_in.insert("0.0", main_part)
            self._apply_live_input_markdown()
        if self.chk_auto.get():
            self._force_trigger()

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
                        subprocess.Popen(
                            [LM_STUDIO_GUI_EXE, "--minimized"],
                            startupinfo=si,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    else:
                        subprocess.Popen(
                            [LM_STUDIO_GUI_EXE],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
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
        self._start_status_anim(self._tr("starting_server"), "#eab308", "#eab308")

        def worker():
            ok = self._boot_local_lm_studio_server()
            if ok:
                self.after(0, lambda: self.fetch_models(silent=False, auto_start_server=False))
            else:
                self.after(0, lambda: self._stop_status_anim(self._tr("server_failed"), "#ef4444", 0.0))

        threading.Thread(target=worker, daemon=True).start()

    def _query_lms_ls_downloaded_models(self):
        models = []
        res = self._run_lms_cmd(["ls", "--json"], timeout=6)
        if res and res.stdout:
            try:
                data = json.loads(res.stdout)
                if isinstance(data, list):
                    for item in data:
                        m_key = item.get("modelKey") or item.get("id") or item.get("path")
                        if m_key and "embed" not in m_key.lower():
                            models.append(m_key)
            except Exception:
                pass
        return models

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
                self.after(0, lambda: self._start_status_anim(f"{self._tr('unloading')} {old_model[:15]}", "#eab308"))
                self._verified_unload_single_model(old_model)
                if self._model_switch_id != switch_id:
                    return
                self.after(0, self._refresh_model_dropdown_labels)
                if new_model in ALL_MODEL_PLACEHOLDERS:
                    self.after(0, lambda: self._stop_status_anim(self._tr("model_reset"), THEME["text_muted"], 0.0))
                else:
                    self.after(0, lambda: self._stop_status_anim(self._tr("model_ready"), "#22c55e", 0.0))
                    if self.chk_auto.get():
                        self.after(0, self._force_trigger)
            threading.Thread(target=swap_vram, daemon=True).start()
        else:
            if new_model in ALL_MODEL_PLACEHOLDERS:
                self._stop_status_anim(self._tr("choose_model_bottom"), "#eab308", 0.0)
            else:
                self._stop_status_anim(self._tr("model_ready"), "#22c55e", 0.0)
                if self.chk_auto.get():
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
                    if not names:
                        names = self._query_lms_ls_downloaded_models()
                    self.client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=20.0)
                    if names:
                        self._available_models = names
                        self._loaded_vram_models = self._query_lms_ps_loaded_models()
                        self.after(0, lambda n=names: self._update_models_ui(n, True))
                    else:
                        self._available_models = []
                        self._loaded_vram_models = set()
                        self.after(0, lambda: self._update_models_ui([self._tr("no_models")], False))
                    return
                except Exception:
                    continue

            if auto_start_server and not silent:
                self.after(0, lambda: self._update_status_anim_phase(self._tr("starting_server"), "#eab308", "#eab308"))
                if self._boot_local_lm_studio_server():
                    for host in (LM_HOST, "localhost"):
                        try:
                            test_client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=3.0)
                            models = test_client.models.list()
                            names = [m.id for m in models.data if "embed" not in m.id.lower()]
                            if not names:
                                names = self._query_lms_ls_downloaded_models()
                            self.client = OpenAI(base_url=f"http://{host}:{LM_PORT}/v1", api_key="lm-studio", timeout=20.0)
                            if names:
                                self._available_models = names
                                self._loaded_vram_models = self._query_lms_ps_loaded_models()
                                self.after(0, lambda n=names: self._update_models_ui(n, True))
                                return
                        except Exception:
                            continue

            self._loaded_vram_models = set()
            self.after(0, lambda: self._update_models_ui([self._tr("offline_model")], False, silent=silent))

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
        self.btn_load_model.configure(state="disabled")
        self._start_status_anim(f"{self._tr('loading_vram')}: {target_model[:18]}", "#eab308", "#eab308")

        def task():
            try:
                if self._loaded_vram_models:
                    self._verified_unload_all_vram(timeout_per_step=8)
                self._run_lms_cmd(["load", target_model, "-y"], timeout=45)
                loaded_now = self._query_lms_ps_loaded_models()
                if target_model not in loaded_now:
                    try:
                        self.client.chat.completions.create(
                            model=target_model,
                            messages=[{"role": "user", "content": "ok"}],
                            max_tokens=1,
                            stream=False
                        )
                        loaded_now.add(target_model)
                    except Exception:
                        pass
                self._loaded_vram_models = loaded_now if loaded_now else {target_model}
                self.after(0, self._refresh_model_dropdown_labels)
                self.after(0, lambda: self._stop_status_anim(self._tr("model_ready"), "#22c55e", 1.0))
                if self.chk_auto.get() and self.t_in.get("0.0", "end-1c").strip():
                    self.after(0, self._force_trigger)
            finally:
                self._is_loading_model = False
                self.after(0, lambda: self.btn_load_model.configure(state="normal"))

        threading.Thread(target=task, daemon=True).start()    

    def unload_vram(self):
        if not self._loaded_vram_models:
            self._sync_vram_button_visibility()
            self._stop_status_anim(self._tr("vram_already_empty"), "#22c55e", 0.0)
            return

        def task():
            self._abort_active_stream()
            self.after(0, lambda: self._start_status_anim(self._tr("vram_check"), "#eab308"))
            all_clean = self._verified_unload_all_vram()
            self.after(0, self._refresh_model_dropdown_labels)
            if all_clean:
                self.after(0, lambda: self._stop_status_anim(self._tr("vram_cleaned_all"), "#22c55e", 0.0))
            else:
                self.after(0, lambda: self._stop_status_anim(self._tr("vram_cleaned"), "#eab308", 0.0))
        threading.Thread(target=task, daemon=True).start()

    def stop_translation(self):
        self._abort_active_stream()
        self.btn_go.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._stop_status_anim(self._tr("stopped"), "#eab308", 0.0)

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
            if k != "Auto Detect" and (clean in k.lower() or clean == ru_name.lower() or clean in aliases.lower().split()):
                return k
        return raw_lang.strip(" <>[].,:;\"'").title()

    def _apply_detected_language_ui(self, detected_lang):
        norm = self._normalize_lang_name(detected_lang)
        if not norm:
            return None
        self.detected_src_lang = norm
        if self.is_auto_detect:
            self.dd_src.set(self._format_auto_detect_display(norm))
        self._update_swap_button_state()
        return norm

    def _find_corrupted_words(self, translated_text, original_text, tgt_lang):
        corrupted = []
        if tgt_lang in CYRILLIC_LANGUAGES:
            hybrids = RE_CYR_LAT_MIXED_WORD.findall(translated_text)
            corrupted.extend(hybrids)

            orig_latin = {w.lower() for w in RE_LATIN_WORDS.findall(original_text)}
            for lw in RE_LATIN_WORDS.findall(translated_text):
                low = lw.lower()
                if low in ALLOWED_LATIN_ACRONYMS or low in ("lang", "main", "dict"):
                    continue
                if low not in orig_latin:
                    corrupted.append(lw)
                elif len(original_text.split()) > 4 and low in orig_latin and not lw[0].isupper():
                    corrupted.append(lw)
        return list(dict.fromkeys(corrupted))

    def _clean_output_text(self, text, tgt_lang, src_text=""):
        text = RE_THINK_BLOCKS.sub("", text)
        text = RE_UNCLOSED_THINK.sub("", text)
        text = re.sub(r"<lang>.*?</lang>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<lang>[^\n]*$", "", text, flags=re.IGNORECASE)

        text = RE_SPECIAL_TOKENS.sub("", text)

        if tgt_lang not in CJK_LANGUAGES:
            text = RE_CJK_GARBAGE.sub("", text)
            text = re.sub(r"\n\s*[,.\s]+\s*$", "", text)

        if src_text and not RE_EMOJI_CHARS.search(src_text):
            text = RE_EMOJI_CHARS.sub("", text)

        return text.strip()

    def _parse_dict_response(self, raw_text, word):
        cleaned_raw = re.sub(r"</?[a-zA-Z]*$", "", raw_text).strip()
        if not cleaned_raw:
            return "", []

        input_word_low = re.sub(r"[*_`~+.,:;!?'\"()\[\]]", "", word).strip().lower()

        main_match = re.search(
            r"<main>\s*(.*?)\s*(?:</main>|<dict>|\n\s*\[|$)",
            cleaned_raw,
            flags=re.DOTALL | re.IGNORECASE
        )
        dict_match = re.search(
            r"<dict>\s*(.*?)\s*(?:</dict>|$)",
            cleaned_raw,
            flags=re.DOTALL | re.IGNORECASE
        )

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

            if sections and not sections[-1][1]:
                sections[-1][1].append(clean_line.rstrip(":"))
            elif sections:
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
                    for _, (ex_h, ex_list) in enumerate(valid_sections):
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

        if not self._tw_running:
            self._tw_running = True
            self._typewriter_tick()

    def skip_typewriter_animation(self):
        if not self._tw_main_target and not self._tw_target_text:
            self.btn_instant.place_forget()
            return
        self._tw_displayed_chars = float(len(self._tw_main_target))
        self.btn_instant.place_forget()
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
            self.btn_instant.place_forget()
            return

        total_main_len = len(self._tw_main_target)
        cur_len = int(self._tw_displayed_chars)

        if cur_len < total_main_len:
            if total_main_len <= 35:
                chars_per_sec = 36.0
            elif total_main_len <= 140:
                chars_per_sec = 65.0
            else:
                chars_per_sec = max(85.0, min(self._tw_tok_speed * 2.5, 220.0))

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
                self.btn_instant.place(relx=1.0, rely=1.0, x=-18, y=-12, anchor="se")
                self.btn_instant.lift()
            else:
                self.btn_instant.place_forget()

            self.after(25, self._typewriter_tick)
        else:
            self.btn_instant.place_forget()
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
                self.after(95, self._typewriter_tick)

    def _render_phased_output(self, main_text_part, dict_sections_to_show, is_dict_mode, word="", mismatch_warning="", dict_pending=False):
        tb = self.t_out._textbox

        saved_sel = None
        try:
            if tb.tag_ranges("sel"):
                saved_sel = (tb.index("sel.first"), tb.index("sel.last"))
        except Exception:
            saved_sel = None
        yview_pos = tb.yview()

        tb.delete("1.0", "end")

        if mismatch_warning:
            tb.insert("end", mismatch_warning + "\n\n", "warn_banner")

        if main_text_part:
            self._last_clean_translation = main_text_part
            self._insert_markdown_styled_text(tb, main_text_part, default_tag="main_trans")

        if is_dict_mode:
            if dict_sections_to_show:
                tb.insert("end", "\n\n", "main_trans")
                tb.insert("end", f"{word} — {self._tr('dict_variants')}\n", "dict_title")
                for pos_h, syns_list in dict_sections_to_show:
                    if pos_h:
                        loc_h = self._translate_pos_header(pos_h)
                        h_low = loc_h.lower()
                        if any(k in h_low for k in ("исконн", "native", "значени", "meaning", "аналог")):
                            tag_to_use = "native_header"
                        elif any(k in h_low for k in ("фразеологизм", "идиом", "idiom", "phras")):
                            tag_to_use = "idiom_header"
                        else:
                            tag_to_use = "pos_header"
                        tb.insert("end", f"\n{loc_h}\n", tag_to_use)
                    else:
                        tb.insert("end", "\n", "dict_body")
                    for s_line in syns_list:
                        tb.insert("end", f"    {s_line}\n", "dict_body")
            elif dict_pending and main_text_part:
                wave_frames = [
                    "•  ·  ·",
                    "·  •  ·",
                    "·  ·  •",
                    "·  •  ·",
                ]
                dots_str = wave_frames[self._dict_dots_step % len(wave_frames)]
                tb.insert("end", "\n\n", "main_trans")
                tb.insert("end", f"{word} — {self._tr('dict_variants')}\n", "dict_title")
                tb.insert("end", f"\n{dots_str}\n", "dict_pending_dots")

        if saved_sel:
            try:
                tb.tag_add("sel", saved_sel[0], saved_sel[1])
            except Exception:
                pass

        if self._tw_running:
            tb.see("end")
        elif yview_pos:
            try:
                tb.yview_moveto(yview_pos[0])
            except Exception:
                pass

    def _build_prompts(self, text, src_mode, tgt_lang, is_dict_mode):
        has_emojis = bool(RE_EMOJI_CHARS.search(text))
        emoji_rule = (
            "Preserve any emojis/emoticons from the input in their exact contextual places."
            if has_emojis else
            "STRICT EMOJI BAN: The input contains NO emojis. NEVER add or invent emojis/emoticons."
        )
        src_hint = f"from {src_mode} " if src_mode and src_mode != "Auto Detect" else ""
        cat_lang = "Russian" if self.ui_lang == "ru" else "English"
        idiom_header = "[фразеологизмы и идиомы]" if self.ui_lang == "ru" else "[idioms & phrases]"
        native_header = "[исконные аналоги / значение]" if self.ui_lang == "ru" else "[native equivalents / meaning]"

        if is_dict_mode:
            sys_prompt = (
                f"You are an authoritative bilingual translator, lexicographer, and etymology/slang expert translating {src_hint}into {tgt_lang}.\n"
                f"Analyze the exact grammatical form, tense, slang meaning, loanword status, and idiomatic usage of the input.\n\n"
                f"STRICT RULES:\n"
                f"1. Line 1: Output the source language in English inside <lang>...</lang> (e.g., <lang>English</lang>).\n"
                f"2. Line 2: Inside <main>...</main>, output ONLY the single best, most natural translation in {tgt_lang} matching the exact form/idiom of the input (e.g., for 'wasted' -> <main>потрачено</main>; for 'break a leg' -> <main>ни пуха ни пера</main>). NEVER repeat the untranslated source word inside <main>!\n"
                f"3. AI JUDGMENT ON ALTERNATIVES, NATIVE EQUIVALENTS & IDIOMS (<dict>...</dict>):\n"
                f"   - YOU DECIDE whether dictionary alternatives, native equivalents, or idioms are useful for this input.\n"
                f"   - Put EVERY category on its OWN NEW LINE starting with `[Category Name]`.\n"
                f"   - PARTS OF SPEECH: If the word has synonyms/variants, group them under headers in {cat_lang} (e.g., [причастие / предикатив], [прилагательное], [глагол], [существительное], [сленг]).\n"
                f"   - ANGLICISMS, LOANWORDS & SLANG ({native_header}): If the input is slang, an anglicism, a modern buzzword, or a word often transliterated/borrowed (e.g. cringe/кринж, vibe/вайб, deadline/дедлайн, rofl, flex, wasted, chill, toxic), include {native_header} on a new line with pure, native {tgt_lang} equivalents and clear meaning (for example, for 'cringe': испанский стыд, неловкость, коробит; for 'vibe': атмосфера, настрой, энергетика).\n"
                f"   - IDIOMS ({idiom_header}): Include {idiom_header} on a new line ONLY if natural idioms, phraseologisms, or set expressions genuinely exist for this word/concept. Otherwise omit it.\n"
                f"   - If the input is unambiguous and needs NO variants at all, leave <dict></dict> empty!\n"
                f"4. NEVER output paronym errors (never write 'бесценный' for 'wasted'; write 'бесцельный, напрасный, потраченный впустую, убитый, в хлам').\n"
                f"5. {emoji_rule}"
            )
            user_instruction = (
                f"Translate \"{text}\" {src_hint}into {tgt_lang} using this exact multi-line structure (each [Category] MUST start on a new line):\n"
                f"<lang>SourceLanguageInEnglish</lang>\n"
                f"<main>Best translation in {tgt_lang}</main>\n"
                f"<dict>\n"
                f"[Part of speech in {cat_lang}] synonym 1, synonym 2, synonym 3\n"
                f"{native_header} pure native {tgt_lang} equivalents / slang meaning (include if slang or loanword)\n"
                f"{idiom_header} idiom 1, set phrase 2 (include ONLY if genuine idioms exist)\n"
                f"</dict>"
            )
            return sys_prompt, [user_instruction]

        raw_chunks = self._split_into_chunks(text, max_chars=1800)
        chunks = [
            f"Translate the following text {src_hint}into pure {tgt_lang} (start with <lang>SourceLanguage</lang> on line 1, preserve any Markdown formatting like **bold**, *italic*, `code`):\n"
            f"<source_text>\n{c}\n</source_text>"
            for c in raw_chunks
        ]

        sys_prompt = (
            f"You are an elite literary, technical, and localization translator (like DeepL Pro) into {tgt_lang}.\n"
            f"CRITICAL RULES:\n"
            f"1. LANGUAGE DETECTION: On the very first line, output the source language name in English inside <lang>...</lang> tags (for example, <lang>Latin</lang> or <lang>English</lang>). Always translate from the text's TRUE language.\n"
            f"2. 100% PURE {tgt_lang.upper()} VOCABULARY & IDIOMS: Translate every single sentence idiomatically and accurately into pure {tgt_lang}. Adapt idioms and cultural expressions naturally. Never mix Latin and Cyrillic letters inside words. Translate technical terms properly (e.g. 'Silicon' in computing is 'кремниевый', 'Transformers' in AI is 'трансформеры', 'High-Dimensional' is 'многомерные/высокоразмерные', 'Alignment' is 'согласование/выравнивание', 'Sycophancy' is 'подхалимство/лесть').\n"
            f"3. MARKDOWN & SPECIAL FORMATTING: If the source text uses special formatting markers such as **bold**, *italic*, ***bold italic***, `inline monolith/code`, ```code blocks```, ~~strikethrough~~, ++underline++, # headers, or > quotes, you MUST preserve those exact markers around the corresponding translated words/phrases.\n"
            f"4. EMOJI POLICY: {emoji_rule}\n"
            f"5. COMPLETENESS: Do not skip any paragraphs, headers, or numbered items. Output ONLY <lang>...</lang> followed by the translation."
        )
        return sys_prompt, chunks

    def _create_chat_completion_universal(self, model_name, sys_prompt, user_payload, stream=True, temperature=0.0):
        messages_std = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_payload}
        ]
        stop_tokens = ["</source_text>", "<|im_end|>", "<|eot_id|>", "<|END_OF_TURN_TOKEN|>"]

        try:
            return self.client.chat.completions.create(
                model=model_name,
                messages=messages_std,
                stream=stream,
                temperature=temperature,
                top_p=0.85,
                frequency_penalty=0.05,
                presence_penalty=0.0,
                stop=stop_tokens
            )
        except Exception as e1:
            err_str = str(e1).lower()
            if "model" in err_str and ("not loaded" in err_str or "not found" in err_str or "no model" in err_str):
                self._run_lms_cmd(["load", model_name, "-y"], timeout=25)
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

            merged_messages = [{"role": "user", "content": f"{sys_prompt}\n\n{user_payload}"}]
            return self.client.chat.completions.create(
                model=model_name,
                messages=merged_messages,
                stream=stream,
                temperature=temperature
            )

    def start_translation(self):
        text = self.t_in.get("0.0", "end-1c").strip()
        tgt_lang = self._get_effective_tgt_lang()
        if not text or not tgt_lang or not self._is_valid_model_selected():
            return

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
        self._last_selected_out_text = ""
        self.t_out._textbox.delete("1.0", "end")

        self.btn_go.configure(state="disabled")
        self.btn_stop.configure(state="normal")

        src_mode = self._get_effective_src_mode()
        active_model = strip_loaded_prefix(self.model_id)

        if active_model not in self._loaded_vram_models:
            self._start_status_anim(self._tr("loading_vram"), "#eab308", "#eab308")
        else:
            self._start_status_anim(self._tr("translating"), "#3b82f6", "#3b82f6")

        plain_probe = re.sub(r"[*_`~+]", "", text).strip()
        words = plain_probe.split()
        is_dict_mode = (
            1 <= len(words) <= 6
            and len(plain_probe) <= 65
            and "\n" not in plain_probe
            and not any(plain_probe.endswith(p) for p in (".", "!", "?", ";", ":"))
        )
        self._tw_is_dict_mode = is_dict_mode
        self._tw_word = plain_probe
        sys_prompt, chunks = self._build_prompts(text, src_mode, tgt_lang, is_dict_mode)

        def ai_worker():
            local_stream = None
            try:
                completed_chunks_text = ""
                total_tokens = 0
                gen_start_ts = None
                detected_lang_final = None
                mismatch_banner = ""

                for idx, payload in enumerate(chunks):
                    if self._task_id != current_task:
                        return

                    local_stream = self._create_chat_completion_universal(
                        active_model, sys_prompt, payload, stream=True, temperature=0.0
                    )
                    with self._stream_lock:
                        self._active_stream = local_stream

                    chunk_accumulated = ""
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
                                    self.after(0, self._refresh_model_dropdown_labels)

                            total_tokens += 1
                            chunk_accumulated += content_piece

                            elapsed_so_far = max(now_ts - gen_start_ts, 0.05)
                            live_speed = total_tokens / elapsed_so_far

                            in_think = bool(reasoning_piece and not content_piece) or (
                                ("<think>" in chunk_accumulated or "<thought>" in chunk_accumulated)
                                and not ("</think>" in chunk_accumulated or "</thought>" in chunk_accumulated)
                            )
                            if in_think:
                                phase_lbl = f"{self._tr('thinking')} ({live_speed:.0f} tok/s)"
                                self.after(0, lambda p=phase_lbl: self._update_status_anim_phase(p, "#a855f7", "#a855f7"))
                            else:
                                phase_lbl = f"{self._tr('typing')} ({live_speed:.0f} tok/s)"
                                self.after(0, lambda p=phase_lbl: self._update_status_anim_phase(p, "#3b82f6", "#3b82f6"))

                            if detected_lang_final is None and idx == 0:
                                lang_m = re.search(r"<lang>(.*?)</lang>", chunk_accumulated, flags=re.IGNORECASE | re.DOTALL)
                                if lang_m:
                                    raw_det = lang_m.group(1).strip()
                                    detected_lang_final = self._normalize_lang_name(raw_det)
                                    if detected_lang_final:
                                        self.after(0, lambda d=detected_lang_final: self._apply_detected_language_ui(d))
                                        if not self.is_auto_detect and src_mode.lower() != detected_lang_final.lower():
                                            self._tw_mismatch_langs = (src_mode, detected_lang_final)
                                            mismatch_banner, _ = self._build_mismatch_texts(src_mode, detected_lang_final)
                                            self.after(0, lambda w=mismatch_banner: self._show_instant_mismatch_banner(current_task, w))

                            live_clean = self._clean_output_text(chunk_accumulated, tgt_lang, src_text=text)
                            if live_clean:
                                full_preview = (completed_chunks_text + "\n\n" + live_clean).strip() if completed_chunks_text else live_clean
                                self.after(
                                    0,
                                    lambda fp=full_preview, spd=live_speed, w=mismatch_banner: self._start_or_update_typewriter(
                                        current_task, fp, is_dict_mode, plain_probe, w, spd, stream_finished=False
                                    )
                                )

                    cleaned_final = self._clean_output_text(chunk_accumulated, tgt_lang, src_text=text)

                    if is_dict_mode and self._task_id == current_task and self._is_dict_output_broken(cleaned_final, plain_probe, tgt_lang):
                        self.after(0, lambda: self._update_status_anim_phase(self._tr("polishing"), "#a855f7", "#a855f7"))
                        idiom_h = "[фразеологизмы и идиомы]" if self.ui_lang == "ru" else "[idioms & phrases]"
                        native_h = "[исконные аналоги / значение]" if self.ui_lang == "ru" else "[native equivalents / meaning]"
                        retry_prompt = (
                            f"Translate the word/phrase \"{plain_probe}\" into {tgt_lang}. "
                            f"STRICTLY FORBIDDEN to leave \"{plain_probe}\" untranslated!\n"
                            f"Output in this exact multi-line format:\n"
                            f"<main>best translation in {tgt_lang}</main>\n"
                            f"<dict>\n"
                            f"[причастие / прилагательное] синонимы на {tgt_lang} (если есть)\n"
                            f"{native_h} исконные аналоги на {tgt_lang} (если сленг/англицизм)\n"
                            f"{idiom_h} фразеологизмы или идиомы на {tgt_lang} (если есть)\n"
                            f"</dict>"
                        )
                        retry_res = self._create_chat_completion_universal(
                            active_model, "You are a strict bilingual dictionary.", retry_prompt, stream=False, temperature=0.1
                        )
                        if retry_res and retry_res.choices and retry_res.choices[0].message.content:
                            cand_retry = self._clean_output_text(retry_res.choices[0].message.content, tgt_lang, src_text=text)
                            if not self._is_dict_output_broken(cand_retry, plain_probe, tgt_lang):
                                cleaned_final = cand_retry

                    if not is_dict_mode and self._task_id == current_task:
                        raw_chunk_src = re.sub(r"^.*?<source_text>\s*", "", payload, flags=re.DOTALL).replace("</source_text>", "").strip()
                        corrupted = self._find_corrupted_words(cleaned_final, raw_chunk_src, tgt_lang)
                        if 1 <= len(corrupted) <= 12:
                            self.after(0, lambda: self._update_status_anim_phase(self._tr("polishing"), "#a855f7", "#a855f7"))
                            fix_sys = (
                                f"В переводе обнаружены непереведенные слова или склейки: {', '.join(corrupted)}.\n"
                                f"Замени их в тексте перевода на чистый, литературный язык ({tgt_lang}) в точном соответствии с оригиналом, "
                                f"сохранив все спецсимволы форматирования (**жирный**, *курсив*, `монолит`). ЗАПРЕЩЕНО писать транслит в скобках.\n"
                                f"Выдай ТОЛЬКО готовый исправленный текст перевода."
                            )
                            fix_user = f"Оригинал:\n{raw_chunk_src}\n\nПеревод для отполировки:\n{cleaned_final}"
                            fix_res = self._create_chat_completion_universal(
                                active_model, fix_sys, fix_user, stream=False, temperature=0.0
                            )
                            if fix_res and fix_res.choices and fix_res.choices[0].message.content:
                                candidate = self._clean_output_text(fix_res.choices[0].message.content, tgt_lang, src_text=text)
                                if len(self._find_corrupted_words(candidate, raw_chunk_src, tgt_lang)) < len(corrupted):
                                    cleaned_final = candidate

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

                    self.after(
                        0,
                        lambda c=completed_chunks_text, spd=speed, w=mismatch_banner, fm=final_msg, fc=final_col: self._start_or_update_typewriter(
                            current_task, c, is_dict_mode, plain_probe, w, spd, stream_finished=True, final_msg=fm, final_color=fc
                        )
                    )

            except Exception as e:
                if self._task_id != current_task:
                    return
                err_msg = str(e)
                err_low = err_msg.lower()
                if any(k in err_low for k in ("connection", "refused", "connecterror", "timed out", "unreachable")):
                    self._is_online = False
                    self.after(0, self._sync_server_button_visibility)
                    self.after(0, self._sync_vram_button_visibility)
                self.after(0, lambda: self._render_phased_output(f"{self._tr('api_err')}:\n{err_msg}", [], False))
                self.after(0, lambda: self._stop_status_anim(self._tr("conn_err"), "#ef4444", 0.0))
            finally:
                if local_stream is not None:
                    try:
                        local_stream.close()
                    except Exception:
                        pass
                if self._task_id == current_task:
                    with self._stream_lock:
                        self._active_stream = None
                    self.after(0, lambda: self.btn_go.configure(state="normal"))
                    self.after(0, lambda: self.btn_stop.configure(state="disabled"))

        threading.Thread(target=ai_worker, daemon=True).start()

    def on_closing(self):
        self._save_config()
        self._close_all_dropdowns()
        self._abort_active_stream()
        self.stop_tts()
        if self._loaded_vram_models:
            try:
                self._set_status_label(self._tr("vram_exit"), "#eab308")
                self.update_idletasks()
            except Exception:
                pass
            self._verified_unload_all_vram(timeout_per_step=5)
        self.destroy()
        os._exit(0)


if __name__ == "__main__":
    app = LLMTranslateApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.on_closing()