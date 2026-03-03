# MusicSwitch

A desktop app that conducts playback between **YouTube Music** and **Spotify**, switching randomly between them as songs end. You manage the playlists; MusicSwitch decides what plays when.

## How it works

MusicSwitch is a conductor, not a player. It never touches audio directly.

- YouTube Music runs in a hidden browser view (PyQt6 WebEngine)
- Spotify is controlled via its Web API (remote control, requires Premium)
- A small floating window stays on top of everything, showing what's playing

The switching algorithm is a weighted coin flip with memory — the longer you've been on one platform, the more likely you are to switch to the other:

| Consecutive plays | Stay probability |
|---|---|
| 1 | 50% |
| 2 | 35% |
| 3 | 20% |
| 4+ | 10% |

## Requirements

- Python 3.11+ — [python.org/downloads](https://www.python.org/downloads/)
- Spotify Premium account
- A Spotify app registered at [developer.spotify.com](https://developer.spotify.com)

---

## Setup — Linux / macOS

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Create a Spotify app**

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. In the app settings, add `http://127.0.0.1:8888/callback` as a Redirect URI
4. Copy your Client ID

**3. Configure the environment**

```bash
cp .env.example .env
# Open .env in any text editor and paste your Client ID
```

**4. Prepare your playlists**

- Open YouTube Music and queue a playlist — leave it paused
- Open Spotify and queue a playlist — leave it paused

**5. Run**

```bash
python main.py
```

---

## Setup — Windows

**1. Install Python**

Download and run the installer from [python.org/downloads](https://www.python.org/downloads/).
On the first screen, check **"Add Python to PATH"** before clicking Install.

**2. Install dependencies**

Open the MusicSwitch folder in File Explorer.
Click the address bar at the top, type `cmd`, and press Enter — this opens a Command Prompt inside the folder.

In the Command Prompt, run:

```
pip install -r requirements.txt
```

**3. Create a Spotify app**

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. In the app settings, add `http://127.0.0.1:8888/callback` as a Redirect URI
4. Copy your Client ID

**4. Configure the environment**

In File Explorer, right-click `.env.example` → **Copy**, then right-click in an empty area → **Paste**.
Rename the copy from `.env.example - Copy` to `.env`.

> If File Explorer warns you about changing the extension, click Yes.
> If you don't see file extensions, go to **View → Show → File name extensions**.

Open `.env` with Notepad, replace `your_client_id_here` with your actual Client ID, and save.

**5. Prepare your playlists**

- Open YouTube Music (in your browser) and queue a playlist — leave it paused
- Open Spotify and queue a playlist — leave it paused

**6. Run**

Open the MusicSwitch folder in File Explorer, click the address bar, type `cmd`, press Enter, then run:

```
python main.py
```

---

## First run

1. Click **Open YouTube Music** and log in, then click **Done**
2. Click **Connect Spotify** and complete the OAuth flow in your browser
3. Once both sources show as ready, click **▶ Start**

After the first run, your sessions are saved — you won't need to log in again.

## Controls

The floating window shows the current track, a progress bar, and two buttons:

- **Pause / Resume** — pauses the active platform
- **Skip** — runs the weighted algorithm and either skips within the current platform or switches to the other one

The window can be dragged by its title bar and stays on top of other windows.

## Project structure

```
main.py                  Entry point, signal wiring
src/
  conductor.py           Shuffle state machine
  ytm_bridge.py          Hidden WebEngine view + JS bridge
  spotify_client.py      spotipy wrapper + polling thread
  state.py               Shared dataclasses (AppState, TrackInfo)
  store.py               Persistent config via platformdirs
  ytm_script.js          Injected into the YTM page
  ui/
    floating_window.py   Main always-on-top window
    setup_screen.py      First-run / auth setup screen
    now_playing.py       Track info widget
    progress_bar.py      Progress bar widget
    pause_button.py      Pause / resume toggle
    skip_button.py       Skip button
```

## Packaging

```bash
pyinstaller --windowed --name MusicSwitch main.py
```

Note: PyQt6-WebEngine requires explicit data file inclusion in the `.spec` file for a working binary.
