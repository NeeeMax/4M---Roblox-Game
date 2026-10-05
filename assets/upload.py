"""Upload one file to Max's Roblox account via Open Cloud and print its asset id.

    python assets/upload.py assets/ui/coin.png ["Display Name"]

One call = one upload job = one JSON line back: {"file", "assetType", "assetId", "content"}.
Images (.png/.jpg/.bmp/.tga) become Image assets (usable as ImageLabel.Image), .fbx/.glb/.gltf/.rbxm/.rbxmx
become Model assets (packages), .mp3/.ogg/.wav/.flac Audio.

API key (never commit it): env ROBLOX_API_KEY, or the git-ignored file .roblox-api-key in the repo root.
Create it on create.roblox.com → Open Cloud → API Keys with "assets" Read + Write.
Uploads go to Max's account unless env ROBLOX_USER_ID is set (your own key must belong to that user).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

USER_ID = os.environ.get("ROBLOX_USER_ID", "453953297")  # default: Crazymax0815 (Max)
API = "https://apis.roblox.com/assets/v1/"
TYPES = {
    ".png": ("Image", "image/png"), ".jpg": ("Image", "image/jpeg"), ".jpeg": ("Image", "image/jpeg"),
    ".bmp": ("Image", "image/bmp"), ".tga": ("Image", "image/tga"),
    ".fbx": ("Model", "model/fbx"), ".glb": ("Model", "model/gltf-binary"), ".gltf": ("Model", "model/gltf+json"),
    ".rbxm": ("Model", "model/x-rbxm"), ".rbxmx": ("Model", "model/x-rbxm"),
    ".mp3": ("Audio", "audio/mpeg"), ".ogg": ("Audio", "audio/ogg"), ".wav": ("Audio", "audio/wav"),
    ".flac": ("Audio", "audio/flac"),
}


def api_key() -> str:
    key = os.environ.get("ROBLOX_API_KEY")
    if not key:
        f = Path(__file__).resolve().parent.parent / ".roblox-api-key"
        key = f.read_text().strip() if f.exists() else ""
    if not key:
        sys.exit("No API key: set ROBLOX_API_KEY or create .roblox-api-key in the repo root")
    return key


def call(req: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='replace')}")


def upload(path: Path, name: str) -> dict:
    asset_type, mime = TYPES.get(path.suffix.lower(), (None, None))
    if not asset_type:
        sys.exit(f"Unsupported file type: {path.suffix}")
    meta = {
        "assetType": asset_type,
        "displayName": name[:50],
        "description": "Bonk it",
        "creationContext": {"creator": {"userId": USER_ID}},
    }
    b = uuid.uuid4().hex
    body = (
        f'--{b}\r\nContent-Disposition: form-data; name="request"\r\n\r\n{json.dumps(meta)}\r\n'
        f'--{b}\r\nContent-Disposition: form-data; name="fileContent"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    key = api_key()
    op = call(urllib.request.Request(API + "assets", data=body, method="POST", headers={
        "x-api-key": key, "Content-Type": f"multipart/form-data; boundary={b}"}))
    # Upload is async: poll the operation until Roblox has processed (and moderated) the asset.
    for _ in range(60):
        if op.get("done"):
            break
        time.sleep(2)
        op = call(urllib.request.Request(API + op["path"], headers={"x-api-key": key}))
    if not op.get("done"):
        sys.exit(f"Timed out waiting for {op.get('path')}")
    asset_id = op["response"]["assetId"]
    return {"file": str(path), "assetType": asset_type, "assetId": asset_id, "content": f"rbxassetid://{asset_id}"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    p = Path(sys.argv[1])
    print(json.dumps(upload(p, sys.argv[2] if len(sys.argv) > 2 else p.stem)))
