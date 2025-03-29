from io import BytesIO
import os
import json
import random
import requests
from base64 import b64encode
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv(find_dotenv())

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
SPOTIFY_TOKEN = ""

REFRESH_TOKEN_URL = "https://accounts.spotify.com/api/token"
NOW_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENTLY_PLAYING_URL = "https://api.spotify.com/v1/me/player/recently-played?limit=1"

allowedOrigins = [
    "http://localhost:5503",
    "https://hydrovolter.pages.dev/",
    "http://hydrovolter.pages.dev",
    "https://hydrovolter.vercel.app/",
    "http://hydrovolter.vercel.app",
    "https://hydrovolter.com/",
    "http://hydrovolter.com",
    "https://hydrovolter.github.io",
    "http://hydrovolter.github.io",
    "https://hydrovolter.netlify.app",
    "http://hydrovolter.netlify.app",
]

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": allowedOrigins}})


def get_auth():
    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode("ascii")

def refresh_token():
    global SPOTIFY_TOKEN
    data = {"grant_type": "refresh_token", "refresh_token": SPOTIFY_REFRESH_TOKEN}
    headers = {"Authorization": f"Basic {get_auth()}"}
    response = requests.post(REFRESH_TOKEN_URL, data=data, headers=headers).json()
    SPOTIFY_TOKEN = response.get("access_token", "")
    return SPOTIFY_TOKEN

def get(url):
    global SPOTIFY_TOKEN
    if not SPOTIFY_TOKEN:
        SPOTIFY_TOKEN = refresh_token()
    response = requests.get(url, headers={"Authorization": f"Bearer {SPOTIFY_TOKEN}"})
    if response.status_code == 401:
        SPOTIFY_TOKEN = refresh_token()
        response = requests.get(url, headers={"Authorization": f"Bearer {SPOTIFY_TOKEN}"})
    return response.json() if response.status_code == 200 else {}

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
@app.route('/with_parameters')
def spotify_status(path):
    data = get(NOW_PLAYING_URL)
    
    item = data.get("item")
    if not data.get("is_playing") or item is None:
        return jsonify({"artist": "", "song": "", "song_url": "", "album_art": ""})
    
    artists = "; ".join(artist["name"] for artist in item.get("artists", []))

    return jsonify({
        "artist": artists,
        "song": item["name"],
        "song_url": item["external_urls"]["spotify"],
        "album_art": item["album"]["images"][1]["url"] if item.get("album", {}).get("images") else ""
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000), debug=True)
