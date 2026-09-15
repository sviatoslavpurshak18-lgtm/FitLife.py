# FitLife — підбір тренувань і харчування (Django)

Веб-застосунок: після реєстрації за анкетою (вага, зріст, ціль, акцент, обмеження по здоров'ю…)
генерується програма тренувань і раціон (правилами або через AI-модель OpenRouter), є журнал замірів,
історія раціонів, чат з AI-тренером, власні тренування (CRUD) і панель тренера.

## Технології

- Python 3.12+, Django 6.0
- **СУБД: MySQL 8.0** (перевірено на 8.0.46; вкажіть у звіті свою фактичну версію: `SELECT VERSION();` у MySQL Command Line Client)
- Bootstrap 5 + власний CSS (`static/css/styles.css`)
- AI: OpenRouter (необов'язково — без ключа працює генерація за правилами)

## Запуск

### 1. Код і віртуальне середовище
```bash
git clone <URL вашого репозиторію>
cd Practice_3.py
python -m venv venv
# Windows:   venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

### 2. База даних MySQL
У MySQL Command Line Client (або Workbench) виконайте:
```sql
CREATE DATABASE fitlife CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- за потреби окремий користувач:
-- CREATE USER 'fitlife_user'@'localhost' IDENTIFIED BY '...';
-- GRANT ALL PRIVILEGES ON fitlife.* TO 'fitlife_user'@'localhost';
```

### 3. Змінні оточення
```bash
cp .env.example .env     # Windows: copy .env.example .env
```
Заповніть `.env` (файл у `.gitignore`, у репозиторій не потрапляє):

| Змінна | Призначення |
|---|---|
| `SECRET_KEY` | секретний ключ Django (згенеруйте: `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`) |
| `DEBUG` | `True` для розробки, `False` для продакшену |
| `ALLOWED_HOSTS` | хости через кому, напр. `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | підключення до MySQL (`DB_USER=root`, `DB_PORT=3306`) |
| `OPENROUTER_API_KEY` | ключ OpenRouter (необов'язково) |
| `OPENROUTER_MODEL` | модель, за замовчуванням `openai/gpt-4o-mini` |

### 4. Міграції, тестові дані, запуск
```bash
python manage.py migrate
python manage.py seed_demo          # тренер, 3 спортсмени, заміри, тренування, плани
python manage.py createsuperuser    # для /admin/
python manage.py runserver
```
Відкрийте http://127.0.0.1:8000/

Демо-акаунти (після `seed_demo`), пароль для всіх `Demo12345`:
`trainer` (роль «Тренер»), `olena`, `andrii`, `maksym`.

### Перенесення користувачів зі старої версії
Якщо лишився файл `data/users.json` зі старої версії (власна авторизація):
```bash
python manage.py import_legacy_json data/users.json
```
Хеші паролів сумісні — старі email і паролі продовжують працювати.

## Ролі

| Роль | Як отримати | Можливості |
|---|---|---|
| Користувач | будь-який зареєстрований | власні тренування (CRUD), раціон, заміри, AI, статистика |
| Тренер | група **«Тренери»** (створюється міграцією `catalog/0002`) | усе вище + панель тренера `/trainer/` і перегляд тренувань усіх користувачів |
| Адмін | `createsuperuser` | усе + `/admin/` |

Додати користувача до ролі: `/admin/` → Користувачі → вибрати користувача → Групи → «Тренери».

## Корисне

- **SQL-скрипти для звіту (діалект MySQL):** `python manage.py sqlmigrate accounts 0001`, так само `catalog 0001`, `journal 0001`.
- **Скидання пароля** у режимі розробки: листи виводяться в консоль, де запущено `runserver`
  (налаштуйте `EMAIL_BACKEND` у `config/settings.py` для реальної пошти).
- **Django Debug Toolbar** вмикається автоматично при `DEBUG=True` (панель справа на сторінках).
- **Перевірка проєкту:** `python manage.py check` і `python manage.py makemigrations --check` (не має пропонувати змін).

## Структура

```
config/      налаштування, кореневі URL, власний middleware (RequestTimingMiddleware)
accounts/    Profile, UserMeasurement; реєстрація, вхід/вихід, профіль, пароль, заміри
catalog/     Workout (основна сутність, CRUD), MealPlan, UserWorkout; власні DTL-теги
journal/     AiLog; генерація плану, AI-чат, статистика, панель тренера, журнал
templates/   base.html, partials/, по папках застосунків
```
Детальний опис для звіту (маршрути, в'юхи, ролі, валідація): [docs/section_1_3_notes.md](docs/section_1_3_notes.md).