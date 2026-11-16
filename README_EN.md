<div align="center">

# 🌐 LLM Translate

### Local Neural Text & Image Translator Powered by LM Studio

[🇷🇺 Русский](README.md) | **🇺🇸 English**

<br/>

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Backend](https://img.shields.io/badge/Backend-LM%20Studio%20API-8B5CF6.svg)](https://lmstudio.ai)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS%20(Beta)-gray.svg)](#)

*100% data privacy, zero subscriptions, offline text & screenshot translation without cloud APIs.*

<br/>

<p align="center">
  <img src="preview.png" alt="LLM Translate Interface" width="900" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);"/>
</p>

</div>

---

## 💡 Overview

Cloud translation services send all your text and screenshots to third-party servers, which is unacceptable when working with confidential documents, proprietary source code, or private conversations. Moreover, some translation platforms (such as DeepL) are geo-restricted in certain regions.

**LLM Translate** combines open-weight local language and vision models with a fast dual-pane desktop UI built on **PySide6 (Qt6)**. It communicates directly with your local **[LM Studio](https://lmstudio.ai)** server via the OpenAI-compatible API (`[http://127.0.0.1:1234](http://127.0.0.1:1234)`), ensuring **not a single byte leaves your machine**.

---

## ⚙️ Important: Add Python & LM Studio CLI (`lms`) to `PATH`

For **full automation**—allowing LLM Translate to automatically boot the local server, unload the previous model from `VRAM` when switching models, and free GPU memory upon exit—make sure both tools are available in your system **`PATH`**:

1. **LM Studio CLI (`lms`)** — enables automatic server startup (`lms server start`), model loading (`lms load`), and VRAM cleanup (`lms unload`).
   * **How to add to `PATH`:** open **LM Studio** → press `Ctrl + Shift + P` (Command Palette) → run **`Install LM Studio CLI (lms)`**, or run in your terminal:
     ```bash
     # Windows (PowerShell)
     ~/.lmstudio/bin/lms.exe bootstrap

     # Linux / macOS
     ~/.lmstudio/bin/lms bootstrap
     ```
   * Restart your terminal and verify with `lms status`.
2. **Python 3.10+ & `pip`** *(required when running from source or building `.exe`)*:
   * During Python installation on Windows, make sure to check **`Add python.exe to PATH`** on the first setup screen.

---

## 🎯 Recommended Models by GPU Memory (VRAM)

For maximum token generation speed, the model and its context (`KV cache`) must **fit entirely inside your GPU's VRAM**. If a model exceeds available VRAM, LM Studio offloads layers to system RAM, slowing down translation by 5–10x.

> **Keep in mind:** on an 8 GB GPU, the OS and background apps (browser, Discord, etc.) already consume **~1–1.5 GB**, leaving **~6.5–7 GB** for the model (or **~3.5–4.5 GB** while a heavy game is running).

| GPU VRAM | Comfortable Headroom (browser / games open, ~50–60% VRAM) | Maxed Out (dedicated to translation, zero RAM offloading) | Vision Model (for image / screenshot OCR) |
| :--- | :--- | :--- | :--- |
| **4 GB VRAM** | **`gemma-2-2b-it` (`Q4_K_M`, ~1.7 GB)**<br>Fast, lightweight, keeps context clean without stray characters. | **`gemma-2-2b-it` (`Q8_0`, ~2.8 GB)** or **`gemma-3-4b-it` (`Q3_K_M`, ~2.2 GB)**<br>Best translation quality that stays strictly under the 4 GB cap. | **`moondream2`** or **`minicpm-v-2_6` (`Q3_K_M`, ~2.5 GB)** |
| **8 GB VRAM** | **`gemma-3-4b-it` (`Q4_K_M`, ~2.8 GB)** or **`gemma-2-9b-it` (`IQ3_XS`, ~4.1 GB)**<br>Ideal daily driver: leaves ~3–4 GB free for your browser and OS. | **`gemma-2-9b-it` (`Q4_K_M` / `Q5_K_M`, ~5.8–6.4 GB)**<br>The sweet spot for high-accuracy translation on 8 GB GPUs. | **`gemma-3-4b-it` (`Q4_K_M`, ~2.8 GB)** or **`qwen2.5-vl-3b-instruct` (`Q4_K_M`, ~2.4 GB)** |
| **12 GB VRAM** | **`gemma-2-9b-it` (`Q5_K_M`, ~6.4 GB)**<br>High-precision 9B model with plenty of VRAM headroom. | **`gemma-3-12b-it` (`Q4_K_M`, ~7.5–8.1 GB)** or **`mistral-nemo-instruct-2407` (`Q5_K_M`, ~8.7 GB)**<br>Strong grasp of nuance, idioms, and technical terminology. | **`gemma-3-12b-it` (`Q4_K_M`)** (handles both text and images in one model) |
| **16 GB+ VRAM** | **`gemma-3-12b-it` (`Q6_K`, ~9.8 GB)**<br>Near-lossless quality with generous room for long contexts. | **`gemma-2-27b-it` (`IQ3_M` / `Q3_K_M`, ~11.5–12.5 GB)**<br>Approaches top cloud translation quality completely offline. | **`qwen2.5-vl-7b-instruct` (`Q5_K_M`, ~6.2 GB)** or **`gemma-3-12b-it`** |

---

## ⚡ Quick Start (Windows `.exe`)

1. Download `LLMTranslate.exe` from **[Releases](../../releases)**.
2. Install **[LM Studio](https://lmstudio.ai)**, add `lms` to `PATH` (see above), and download a recommended model from the table (e.g., `gemma-2-9b-it` or `gpt-oss-20b` in `Q4_K_M` or `Q5_K_M`).
3. Launch `LLMTranslate.exe`. If the local LM Studio server isn't running yet, the app will boot it automatically or let you start it via the **Server** button.

---

## ✨ Key Features

### 🧠 Smart Translation & Reasoning Mode
* **Dual Auto-Detection Modes:**
  * **Auto Detect (AI)** — identifies the true source language via vocabulary and grammar (distinguishing Latin, French, English, etc. even when sharing the same script).
  * **Auto Detect (Fast)** — instant script and marker detection before token generation even starts.
* **Language Mismatch Guard:** if you manually select a source language (e.g., English) but paste text in another language (e.g., German), the app displays a warning banner and translates from the actual detected language.
* **Thinking Mode (`<think>`):** supports reasoning models with live phase indicators (`Thinking` vs. `Generating`) while keeping thoughts separate from the final output.
* **Markdown & Code Preservation:** preserves `**bold**`, `*italic*`, `~~strikethrough~~`, `# headers`, `> quotes`, and fenced code blocks intact.
* **Automatic Post-Processing:** filters hallucinations, mixed-script artifacts, and untranslated echoes.

### 🖼️ Image & Screenshot Translation (OCR + Vision)
* Paste screenshots directly from your clipboard (`Ctrl + V`) or pick an image file via the toolbar button.
* Automatically selects the lightest available Vision model in LM Studio, or lets you pin a preferred Vision model in Settings.

### 📚 Dictionary Mode
When entering single words or short phrases (up to 6 words), the app switches to a lexicographic layout:
1. **Primary translation** tailored to context.
2. **Part-of-speech grouping** (`noun`, `verb`, `adjective`, etc.).
3. **Native equivalents & definitions** for slang and loanwords.
4. **Idioms & set phrases.**

### 🔊 Text-to-Speech (TTS) & Ergonomics
* **Read Aloud (TTS):** speaks the translated output in the target language with offline OS speech synthesis fallback.
* **Smooth Typewriter Streaming:** live token speed counter (`tok/s`) and an **⚡ Show instantly** button to skip animation on long texts.
* **Full VRAM Control:** automatically unloads the previous model when switching, provides a one-click **VRAM** purge button, and marks loaded models with `✓`.
* **Themes & UI Scaling:** three built-in themes (**Dark**, **AMOLED**, **Light**), UI scaling (`75%`–`150%`), Always-on-Top toggle, and instant `RU` / `EN` interface switching.

---

## 🛠 Architecture

```text
┌────────────────────────────────────────────────────────┐
│              LLM Translate GUI (PySide6)               │
│     (Markdown Engine + Typewriter + OCR + TTS)         │
└──────────────────────────┬─────────────────────────────┘
                           │
             HTTP / REST (OpenAI Standard API)
                           │
┌──────────────────────────▼─────────────────────────────┐
│                    LM Studio Server                    │
│                 http://127.0.0.1:1234                  │
│       ┌────────────────────────────────────────┐       │
│       │     Gemma 2/3 / Mistral / Vision       │       │
│       └────────────────────────────────────────┘       │
└──────────────────────────▲─────────────────────────────┘
                           │
         VRAM Management via CLI (`lms ps / load / unload`)
```

---

## 💻 Running from Source (Windows / Linux / macOS)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/llm-translate.git
cd llm-translate
pip install PySide6 openai pyperclip
```

> **Linux Note:** for full clipboard and offline TTS support, install `xclip` (or `wl-clipboard`) along with `espeak-ng` and `ffmpeg`:
> ```bash
> sudo apt install xclip wl-clipboard espeak-ng ffmpeg   # Debian / Ubuntu
> sudo pacman -S xclip wl-clipboard espeak-ng ffmpeg     # Arch Linux
> ```

### 2. Run
```bash
python llm_trans_latest.py
```

---

## 🎨 Custom Icons & Single-File `.exe` Build

On first launch with internet access, the app caches vector UI icons (Lucide) and flags into the OS cache directory (`%LOCALAPPDATA%\LLMTranslate\cache` on Windows, `~/.cache/llm-translate` on Linux) without cluttering the executable folder.

If running from source and you want to use **custom button icons or flags**:
1. Create an `icons/` directory next to the script (and `icons/flags/` for country flags).
2. Place `.png` or `.svg` files matching the internal names (`swap.svg`, `play.png`, `settings.svg`, `vision.svg`, `flags/us.png`, etc.) — they will be loaded automatically.

### Building a Standalone Executable (PyInstaller)
```bash
# Windows (clean single .exe)
pyinstaller --noconfirm --onefile --windowed --name "LLMTranslate" --icon "logo.ico" --add-data "icons;icons" llm_trans_latest.py

# Linux / macOS
pyinstaller --noconfirm --onefile --windowed --name "LLMTranslate" --add-data "icons:icons" llm_trans_latest.py
```
*(To bundle custom `icons/` directly inside the executable, add `--add-data "icons;icons"` on Windows or `--add-data "icons:icons"` on Linux/macOS).*

---

## ⌨ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + Enter` | Force translate immediately |
| `Ctrl + V` | Paste text or screenshot from clipboard |
| `Ctrl + C` | Copy selected text |
| `Ctrl + X` / `Ctrl + A` | Cut / Select all text |
| `Esc` | Close open dropdown menu |

---

## ⚙ Configuration (`config.json`)

The configuration file is generated automatically (next to the executable on Windows, or at `~/.config/llm-translate/config.json` on Linux):
```json
{
  "ui_lang": "en",
  "theme_mode": "dark",
  "ui_scale": 100,
  "src_lang": "Auto AI",
  "tgt_lang": "English",
  "model_id": "gemma-2-9b-it-abliterated",
  "auto_translate": true,
  "enable_thinking": false,
  "vision_model_id": "",
  "smart_search": false,
  "pin_window": false
}
```

---

## 📄 License

Distributed under the **GNU General Public License v3.0 (GPLv3)**. See [LICENSE](LICENSE) for full details.
