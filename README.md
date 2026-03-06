# YT Playlist Tracker

YT Playlist Tracker is a simple web application built with Flask that helps you keep track of your progress in YouTube playlists. 

YouTube playlists can contain dozens or even hundreds of videos, which makes it easy to lose track of what you have already watched. This application allows you to search for channels, save playlists to your personal collection, and mark videos as watched or not watched so you always know where you left off.

The application uses the YouTube Data API to fetch channels, playlists and videos details and stores them locally in an SQLite database.

## Features

- Create a personal user account
- Search for YouTube channels by name
- Browse and save playlists from channels
- Refresh playlists to update their content
- Sort saved playlists by title, progress, date saved, or last watched
- Track progress of watched videos within playlists
- Mark videos as watched or not watched
  
## Requirements

- `Flask v3.1.3`
- `python-dotenv v1.2.1`
- `Werkzeug v3.1.6`
- `requests v2.32.5`

## Database

The application uses a lightweight SQLite database to store user accounts, saved playlists, and video watching progress.

The _users_ database file is created automatically on first run. Each user has their own database which is created automatically upon registration.

## Installation

**Step 1:** Clone this repo.

```bash
git clone git@github.com:kpogodzinski/yt_playlist_tracker.git
```

**Step 2:** Go to the project's directory.

```bash
cd yt_playlist_tracker
```

**Step 3:** Create and activate a virtual environment for Python.

_Windows:_

```bash
python -m venv .venv
.venv\Scripts\activate
```

_Linux:_

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Step 4:** Install requirements.

_Windows:_

```bash
pip install -r requirements.txt
```

_Linux:_
```bash
python3 -m pip install -r requirements.txt
```

## Configuration

Create an `.env` file based on the `.env_example` and fill in required environmental variables:
- `SECRET_KEY` – used by Flask to sign and secure sessions.
- `YOUTUBE_API_KEY` – used in YouTube API requests.

> :warning: **IMPORTANT: Do not share any of your keys!**

### Generating Flask secret key
This simple Python script generates a random 32-byte hexadecimal token that you can use as your secret key.

```python
import secrets
secrets.token_hex(32)
```

### Generating YouTube API key

Follow the steps from Google’s official guide to obtain an API key for your app. You can find it [here](https://developers.google.com/youtube/v3/getting-started#before-you-start).

> :warning: **IMPORTANT: Do not share any of your keys!**

## Running

Note: Make sure you are in the project directory and your virtual environment is activated.

**Step 1:** Run the server.

_Windows:_

```bash
python app.py
```
_Linux:_

```bash
python3 app.py
```

**Step 2:** Type in the URL in a web browser.

_If the server is running on local machine:_

```
http://localhost:5000/
```

_If the server is running on another machine:_

```
http://<ip_address>:5000/
```