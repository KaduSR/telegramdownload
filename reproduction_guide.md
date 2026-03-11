# Telegram API Setup Guide

This guide will walk you through the process of obtaining the necessary credentials to use the Telegram Media Downloader.

## Prerequisites

1.  A valid Telegram account.
2.  A phone number associated with that account.

## Step 1: Create a Telegram Application

1.  Go to the [Telegram API Development Tools](https://my.telegram.org/auth) website.
2.  Log in with your phone number. You will receive a confirmation code via your Telegram app.
3.  Once logged in, click on **"API development tools"**.
4.  If it's your first time, you'll need to create a new application:
    *   **App title**: Give it a name (e.g., `MyDownloader`).
    *   **Short name**: A short version of the name (e.g., `mydl`).
    *   **URL**: You can use `https://localhost` or leave it blank.
    *   **Platform**: Select any (e.g., `Desktop` or `Other`).
    *   **Description**: Optional.
5.  Click **"Create application"**.

## Step 2: Get your API Credentials

After creating the app, you will see your credentials:

*   **App api_id**: (Example: `1234567`)
*   **App api_hash**: (Example: `abcdef1234567890abcdef1234567890`)

**Important**: NEVER share these credentials publicly.

## Step 3: Configure the Project

### For CLI usage:
1.  Create a `.env` file in the root of the project.
2.  Add your credentials to the file:
    ```env
    API_ID=your_api_id
    API_HASH=your_api_hash
    PHONE=+your_phone_number_with_country_code
    CHANNEL_LINK=https://t.me/your_channel
    DOWNLOAD_DIR=./downloads
    MAX_PARALLEL_DOWNLOADS=3
    ```

### For Web UI usage:
1.  Run the Streamlit app: `streamlit run app.py`.
2.  Enter your **API ID**, **API HASH**, and **Phone Number** in the sidebar.
3.  Click **"Save Settings"**.

## Step 4: Authentication

The first time you run the script, Telegram will send you a verification code. Enter this code in the terminal or Web UI prompt. A session file (`session_name.session`) will be created in your project folder, allowing you to run the script without re-authenticating in the future.
