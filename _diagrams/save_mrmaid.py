import io
import os
import requests
from PIL import Image

def mm_to_img(code: str, filename="flowchart.png", *, fmt=None, timeout=30):
    """
    Render Mermaid -> image using Kroki.
    - fmt defaults from filename extension (png/svg)
    - Writes PNG via PIL, SVG as bytes
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("code must be a non-empty Mermaid string")

    ext = (os.path.splitext(filename)[1] or "").lower().lstrip(".")
    if fmt is None:
        fmt = ext or "png"
    fmt = fmt.lower()

    if fmt not in {"png", "svg"}:
        raise ValueError("fmt must be 'png' or 'svg'")

    url = f"https://kroki.io/mermaid/{fmt}"
    resp = requests.post(url, data=code.encode("utf-8"), timeout=timeout)
    resp.raise_for_status()

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

    if fmt == "png":
        img = Image.open(io.BytesIO(resp.content))
        img.save(filename)
    else:
        with open(filename, "wb") as f:
            f.write(resp.content)

    print(f"Saved: {filename}")
