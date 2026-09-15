import json
import os
import tempfile
import threading

from django.conf import settings

_lock = threading.Lock()

USER_FIELDS = [
    'id', 'username', 'email', 'password', 'date_of_birth', 'weight',
    'height', 'fitness_goal', 'gender', 'focus_muscle_group', 'session_hours',
]


def _path():
    return settings.BASE_DIR / 'data' / 'users.json'


def _load():
    path = _path()
    if not path.exists():
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _dump(data):
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def save_user(user):
    """Записує/оновлює користувача у data/users.json (пароль — лише хеш)."""
    record = {name: getattr(user, name) for name in USER_FIELDS}
    with _lock:
        data = _load()
        data[str(user.id)] = record
        _dump(data)


def delete_user(user_id):
    with _lock:
        data = _load()
        if data.pop(str(user_id), None) is not None:
            _dump(data)
