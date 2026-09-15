# Як перейти зі старої версії на нову

## 1. Видаліть зі свого проєкту (старе, більше не потрібне)
- `db.sqlite3`
- `accounts/json_store.py`, `accounts/context_processors.py`
- **усі** старі файли міграцій: `accounts/migrations/0*.py`, `catalog/migrations/0*.py`, `journal/migrations/0*.py`
  (залиште тільки `__init__.py` — нові `0001_initial.py` прийдуть з архіву)
- `templates/workout_detail.html`, `templates/nutrition_detail.html`, `templates/progress.html`
- `data/users.json` — спершу імпортуйте з нього користувачів (крок 5), потім видаліть із репозиторію
  (там email-и й хеші паролів, `data/` тепер у `.gitignore`)

## 2. Скопіюйте файли з архіву поверх проєкту
Папки `.git` і `venv` не чіпайте.

## 3. Секрети
Ключ OpenRouter, який був у `config/settings.py`, вважайте скомпрометованим: відкличте його на openrouter.ai
і створіть новий. Нове значення — тільки в `.env` (`OPENROUTER_API_KEY=...`).
Якщо старий ключ уже потрапляв у git-історію — відкликання обов'язкове.

## 4. Середовище і база
```bash
pip install -r requirements.txt
cp .env.example .env        # заповнити
# створити БД у PostgreSQL: CREATE DATABASE fitlife ENCODING 'UTF8';
python manage.py migrate
python manage.py check
python manage.py makemigrations --check    # має сказати "No changes detected"
```

## 5. Дані
```bash
python manage.py import_legacy_json data/users.json   # старі акаунти (логін email + старий пароль)
python manage.py seed_demo                            # демо-дані
python manage.py createsuperuser
python manage.py runserver
```

## 6. Git
```bash
git add -A
git commit -m "Перехід на User+Profile, PostgreSQL, CRUD на Generic Views, ролі"
git push
```
Рекомендовано розбити на кілька комітів (середовище → моделі → в'юхи → ролі → шаблони), щоб історія була не одним комітом.
