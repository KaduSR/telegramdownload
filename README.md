# 🤖 Telegram Media Pro Manager

A high-performance, automated media downloader and uploader for Telegram. This professional tool offers both a sleek **Streamlit Web UI** and a modern **CLI Dashboard**, designed for efficient management of media files from Telegram channels and groups.

---

## 🚀 Key Features

-   **Dual Interface**:
    -   **Web UI (Streamlit)**: Modern, user-friendly interface for managing downloads/uploads with real-time analytics.
    -   **CLI Dashboard (Rich)**: High-performance terminal interface with live progress tracking and ETAs.
-   **Parallel Processing**: High-speed, simultaneous downloads and uploads for maximum throughput.
-   **Smart Resume**: Automatically skips already downloaded files, ensuring reliability on unstable connections.
-   **SQLite Integration**: Robust history tracking and configuration persistence using a local SQLite database.
-   **Bot Notifications**: Optional integration with Telegram bots for real-time status alerts.
-   **Security First**: Sensitive credentials are managed via environment variables and encrypted fields.

---

## 🛠️ Technologies Used

-   **[Telethon](https://github.com/LonamiWebs/Telethon)**: Powerful Python library for interacting with the Telegram API.
-   **[Streamlit](https://streamlit.io/)**: For the modern, reactive web interface.
-   **[SQLite](https://sqlite.org/)**: Reliable local storage for download history and settings.
-   **[Rich](https://github.com/Textualize/rich)**: For the professional terminal-based dashboard.
-   **[Python Dotenv](https://github.com/theskumar/python-dotenv)**: Secure management of configuration via `.env` files.

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/telegram-downloader.git
cd telegram-downloader
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

1.  **Obtain Telegram API Keys**:
    - Follow our [API Setup Guide](reproduction_guide.md) to get your `API_ID` and `API_HASH`.
2.  **Environment Setup**:
    - Create a `.env` file in the root directory (see `reproduction_guide.md` for details).

---

## 🖥️ How to Use

### Option 1: Web Interface (Streamlit)
Ideal for a visual and interactive experience.
```bash
streamlit run app.py
```

### Option 2: CLI Dashboard
Ideal for headless servers or terminal enthusiasts.
```bash
python main.py
```

---

## 📂 Project Structure

-   `app.py`: The entry point for the Streamlit Web UI.
-   `main.py`: The entry point for the CLI Dashboard.
-   `downloader.py`: Core logic for Telegram communication and file processing.
-   `database.py`: Database schema and persistence layer (SQLite).
-   `dashboard.py`: Rich-based UI components for the CLI.
-   `config.py`: Configuration management and validation.

---

## 📊 Dashboard Metrics

-   **Queue Status**: Total files found vs. remaining downloads.
-   **Real-time Speed**: Live calculation of MB/s for active tasks.
-   **Progress Tracking**: Visual bars for each active file and overall progress.
-   **ETA**: Estimated completion time based on current performance.

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---

## ⚠️ Disclaimer

-   Please respect Telegram's [Terms of Service](https://telegram.org/tos).
-   Large-scale automated downloads may trigger temporary API rate limiting (FloodWait). Use responsibly.
