# Матеріали для підрозділу 1.3 (описують фактичну реалізацію)

## Моделі
| Модель | Застосунок | Власник | Ключове |
|---|---|---|---|
| `Profile` | accounts | `user` OneToOne→User (CASCADE) | анкета; choices (стать, акцент, ціль, год. сесії, тренувань/тиждень); `age`, `bmi`; `save()` пише замір; `Meta.permissions: view_trainer_panel` |
| `UserMeasurement` | accounts | `user` FK→User (CASCADE) | вага/зріст/дата; `ordering = ['-recorded_at','-id']` |
| `Workout` | catalog | `user` FK→User (CASCADE) | основна сутність; `is_ai_generated` (bool), `created_at`; M2M `assigned_users` (through `UserWorkout`, related_name `assigned_workouts`); `UniqueConstraint` «одне згенероване тренування на користувача»; `Meta.permissions: view_all_workouts` |
| `UserWorkout` | catalog | `user` FK, `workout` FK (CASCADE) | проміжна таблиця M2M; `UniqueConstraint(user, workout)` |
| `MealPlan` | catalog | `user` FK→User (CASCADE) | історія раціонів: новий запис, коли змінились калорії/БЖВ |
| `AiLog` | journal | `user` FK→User (CASCADE) | `kind` (план/чат); M2M `workouts`, `meal_plans` (through) |
| `AiLogWorkout`, `AiLogMealPlan` | journal | FK на `AiLog` і на Workout/MealPlan (CASCADE) | `UniqueConstraint`; `__str__` |

**Обґрунтування `on_delete`:** усі зв'язки `CASCADE` — це особисті дані користувача або рядки проміжних таблиць,
які не мають сенсу без батьківського запису.

## Форми і валідація
| Правило | Рівень | Де |
|---|---|---|
| рік народження реальний, вік ≥ 12 | валідатор поля | `accounts/validators.py::validate_birth_year` |
| назва тренування ≥ 3 символи, не лише цифри | валідатор поля | `catalog/validators.py::validate_workout_title` |
| унікальність email/username, вага 30–300, зріст 100–250 | `clean_<field>()` | `accounts/forms.py` |
| пароль: ≥ 8 символів, велика літера, цифра, не лише цифри | `clean_password1()` + вбудовані валідатори | `RegisterForm` |
| назва тренування унікальна для користувача | `clean_title()` | `catalog/forms.py::WorkoutForm` |
| «Складне» тренування не коротше 30 хв | `clean()` (форма) | `WorkoutForm` |
| мін. тривалість ≤ макс. | `clean()` (форма) | `WorkoutSearchForm` (forms.Form без моделі) |
| діапазони `MinValue/MaxValue` | рівень моделі | `Profile`, `Workout` |

## Представлення
| Клас/функція | Маршрут | Що перевизначено і навіщо |
|---|---|---|
| `WorkoutListView` | `catalog:workout_list` | `get_queryset` (Q-пошук, фільтри, `select_related`, `annotate`, область «усі» лише з правом), `get_context_data` (форма пошуку) |
| `WorkoutDetailView` | `catalog:workout_detail` (`<int:pk>`) | `get_object` (перевірка власника/права → 403), `get_context_data` (розбір програми) |
| `WorkoutCreateView` | `catalog:workout_create` | `form_valid` (власник = `request.user`), `get_form_kwargs` |
| `WorkoutUpdateView` / `WorkoutDeleteView` | `catalog:workout_update` / `workout_delete` | `get_queryset` фільтрує за власником → чужі записи 404; `form_valid` (повідомлення) |
| `current_workout` (FBV) | `catalog:current` | проста дія «перейти до моєї програми»; клас тут зайвий |
| `MealPlanListView`, `MealPlanDetailView` | `catalog:mealplan_list`, `mealplan_detail` | `get_queryset` за власником |
| `MeasurementListView`, `MeasurementDetailView` | `accounts:measurement_list`, `measurement_detail` | `get_queryset`, `get_context_data` (aggregate) |
| `RegisterView` | `accounts:register` | `form_valid`: збереження, вхід, генерація першої програми |
| `ProfileEditView` | `accounts:profile_edit` | `get_object`, `form_valid` (перерахунок плану при зміні анкети) |
| `DashboardView`, `HomeView` | `journal:dashboard`, `journal:home` | `get_context_data` |
| `stats` (FBV) | `journal:stats` | статистика через `aggregate`/`annotate`; функція простіша за клас |
| `TrainerPanelView` | `journal:trainer_panel` | `PermissionRequiredMixin`; `annotate(Count)` |
| `GeneratePlanView`, `Assistant*View` | `journal:plan_generate`, `ai_*` | лише POST |
| `AiLogListView`, `AiLogDetailView` | `journal:ailog_list`, `ailog_detail` | `get_queryset` (`prefetch_related`) |
| `request_info` (FBV) | `journal:request_info` | демонстрація HttpRequest/HttpResponse; POST за схемою PRG |

## Ролі і доступ
| Роль | Може | Де перевіряється |
|---|---|---|
| Анонім | головна, вхід, реєстрація, скидання пароля | `LoginRequiredMixin` / `@login_required` на решті |
| Користувач | CRUD власних тренувань, раціон, заміри, AI, статистика | `catalog/views.py`: `get_queryset().filter(user=request.user)`; `form_valid` ставить власника |
| Тренер (група «Тренери») | панель тренера; перегляд чужих тренувань (лише читання) | `TrainerPanelView.permission_required`; `WorkoutDetailView.get_object` і `WorkoutListView.get_queryset` через `has_perm('catalog.view_all_workouts')` |

Права: `accounts.view_trainer_panel`, `catalog.view_all_workouts` (`Meta.permissions`); групу створює data-міграція `catalog/0002_trainer_group.py`.

## Шаблони
```
base.html
├─ partials/_navbar.html  → partials/_nav_link.html (inclusion-тег nav_link)
├─ partials/_messages.html
├─ home.html, dashboard.html, profile_edit.html, ai_assistant.html
├─ registration/login.html, register.html
├─ accounts/*  (usermeasurement_list/detail, form_page, done_page)
├─ catalog/*   (workout_list/detail/form/confirm_delete/empty, mealplan_list/detail)
├─ journal/*   (ailog_list/detail, stats, trainer_panel)
└─ partials/_pagination.html, _macro_bar.html, workout_days.html — через {% include %}
```
Власні теги (`catalog/templatetags/fitness_tags.py`): `nav_link`, `macro_bar` (inclusion), `bmi_badge`, `query_string` (simple_tag).

## Оптимізація запитів (Д5) — як зафіксувати для звіту
1. `python manage.py seed_demo`, увійти як `trainer`, відкрити `/workouts/?scope=all` — Debug Toolbar → SQL: кількість запитів.
2. «До»: тимчасово прибрати `select_related('user')` у `WorkoutListView.get_queryset` → на кожну картку додатковий запит за `w.user`.
3. «Після»: повернути `select_related('user')`. Те саме для `/logs/` (`prefetch_related('workouts','meal_plans')`) і `/trainer/` (`select_related('profile')` + `annotate`).
4. Зробіть скріншоти Debug Toolbar і запишіть кількість запитів та час у таблицю «до → після» (вказати обсяг даних).
