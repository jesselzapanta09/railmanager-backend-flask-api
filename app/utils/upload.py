import os
import time
from werkzeug.utils import secure_filename

def save_file(file, folder):
    if not file:
        return None

    path = os.path.join("uploads", folder)
    os.makedirs(path, exist_ok=True)

    original_name = secure_filename(file.filename)
    _, ext = os.path.splitext(original_name)

    prefix_map = {
        "avatars": "avatar",
        "trains": "train",
    }
    prefix = prefix_map.get(folder, folder.rstrip("s") or "file")
    filename = f"{prefix}-{int(time.time() * 1000)}{ext.lower()}"

    filepath = os.path.join(path, filename)
    file.save(filepath)

    return f"/uploads/{folder}/{filename}"
