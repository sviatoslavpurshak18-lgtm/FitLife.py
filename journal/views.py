import html
import logging
import os
import re
from urllib.parse import quote_plus

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from accounts.views import FitnessLoginRequiredMixin, get_current_fitness_user
from catalog.models import MealPlan, Workout
from .models import AiLog
from .services import AiUnavailable, FitnessRecommendationEngine, WARMUP_MIN, ask_ai_coach

logger = logging.getLogger(__name__)


DAY_RE = re.compile(r'^\((\d+) тренування, ~(\d+) хв\)$')
EXERCISE_RE = re.compile(r'^—\s*(.+), (\d+) (\S+) (.+)$')
PAREN_RE = re.compile(r'\s*\([^)]*\)')

# Хочеш конкретне відео для вправи? Додай сюди пару: назва вправи (малими літерами) -> посилання.
# Приклад: 'жим лежачи': 'https://www.youtube.com/watch?v=XXXXXXXXXXX'
EXERCISE_VIDEOS = {}


def exercise_video_url(name):
    """Посилання на відео вправи: своє з EXERCISE_VIDEOS або пошук на YouTube."""
    key = name.strip().lower()
    if key in EXERCISE_VIDEOS:
        return EXERCISE_VIDEOS[key]
    clean = PAREN_RE.sub('', name).strip()
    return 'https://www.youtube.com/results?search_query=' + quote_plus(f'{clean} техніка виконання')


def parse_program(text):
    """Розбирає program_text на дні та вправи для красивого показу.
    Якщо формат не розпізнано, повертає порожній список (шаблон покаже простий текст)."""
    days = []
    for line in (text or '').splitlines():
        line = line.strip()
        day = DAY_RE.match(line)
        if day:
            days.append({'num': int(day.group(1)), 'minutes': int(day.group(2)), 'warmup': WARMUP_MIN, 'exercises': []})
            continue
        # рядок вправи: "— назва, 3 підходи 10 повторів | відпочинок 3 хв | 11 хв"
        parts = [part.strip() for part in line.split(' | ')]
        ex = EXERCISE_RE.match(parts[0])
        if ex and days:
            days[-1]['exercises'].append({
                'name': ex.group(1),
                'sets': ex.group(2),
                'sets_word': ex.group(3),
                'reps': ex.group(4),
                'rest': parts[1].removeprefix('відпочинок ') if len(parts) > 1 else '',
                'time': parts[2] if len(parts) > 2 else '',
                'video_url': exercise_video_url(ex.group(1)),
            })
    return [d for d in days if d['exercises']]


class HomeView(TemplateView):
    template_name = 'home.html'


class DashboardView(FitnessLoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = get_current_fitness_user(self.request)
        ctx['fitness_user'] = user
        ctx['meal_plan'] = MealPlan.objects.filter(users=user).first()
        ctx['workout'] = Workout.objects.filter(users=user).first()
        return ctx


class WorkoutDetailView(FitnessLoginRequiredMixin, TemplateView):
    template_name = 'workout_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = get_current_fitness_user(self.request)
        ctx['fitness_user'] = user
        workout = Workout.objects.filter(users=user).first()
        ctx['workout'] = workout
        ctx['days'] = parse_program(workout.program_text) if workout else []
        return ctx


class GeneratePlanView(FitnessLoginRequiredMixin, View):
    def post(self, request):
        user = get_current_fitness_user(request)
        engine = FitnessRecommendationEngine(user)
        _, workout, _ = engine.generate_recommendations()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            days = parse_program(workout.program_text)
            return JsonResponse({
                'title': workout.title,
                'duration_min': workout.duration_min,
                'html': render_to_string('partials/workout_days.html', {'days': days}, request=request),
            })

        messages.success(request, "AI згенерувало програму під ваші дані.")
        return redirect('workout_detail')



CHAT_HISTORY_KEY = 'ai_chat'
CHAT_MAX_MESSAGES = 20       # скільки останніх повідомлень пам'ятаємо (10 пар питання-відповідь)
CHAT_MAX_QUESTION = 500      # максимальна довжина питання


class AssistantView(FitnessLoginRequiredMixin, TemplateView):
    template_name = 'ai_assistant.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['fitness_user'] = get_current_fitness_user(self.request)
        ctx['history'] = self.request.session.get(CHAT_HISTORY_KEY, [])
        ctx['ai_enabled'] = bool(settings.OPENROUTER_API_KEY)
        ctx['max_len'] = CHAT_MAX_QUESTION
        return ctx


class AssistantAskView(FitnessLoginRequiredMixin, View):
    def post(self, request):
        user = get_current_fitness_user(request)
        question = (request.POST.get('question') or '').strip()
        if not question:
            return JsonResponse({'error': 'Введіть питання.'}, status=400)
        if len(question) > CHAT_MAX_QUESTION:
            return JsonResponse({'error': f'Питання задовге (максимум {CHAT_MAX_QUESTION} символів).'}, status=400)

        history = request.session.get(CHAT_HISTORY_KEY, [])
        try:
            answer = ask_ai_coach(user, history, question)
        except AiUnavailable as exc:
            return JsonResponse({'error': str(exc)}, status=503)
        except Exception:
            logger.exception("AI-чат: помилка запиту")
            return JsonResponse({'error': 'AI зараз недоступний. Спробуйте ще раз за хвилину.'}, status=502)

        history = history + [
            {'role': 'user', 'content': question},
            {'role': 'assistant', 'content': answer},
        ]
        request.session[CHAT_HISTORY_KEY] = history[-CHAT_MAX_MESSAGES:]
        AiLog.objects.create(
            users=user,
            recommendation_summary=f"Питання: {question} | Відповідь: {answer}"[:1000],
        )
        return JsonResponse({'answer': answer})


class AssistantClearView(FitnessLoginRequiredMixin, View):
    def post(self, request):
        request.session.pop(CHAT_HISTORY_KEY, None)
        return redirect('ai_assistant')


# ---------------------------------------------------------------------------
# Практика: HttpRequest / HttpResponse (django.http)
# ---------------------------------------------------------------------------

HIDDEN_COOKIES = {'sessionid', 'csrftoken'}      # значення цих cookie не показуємо
ALLOWED_UPLOAD_EXT = {'.jpg', '.jpeg', '.png', '.pdf', '.txt'}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


def rows_html(mapping, hidden=()):
    """Перетворює словник (request.GET / POST / COOKIES) на рядки таблиці."""
    if not mapping:
        return '<tr><td colspan="2"><i>порожньо</i></td></tr>'
    rows = []
    for key, value in mapping.items():
        shown = '***' if key in hidden else value
        rows.append('<tr><td>{}</td><td>{}</td></tr>'.format(html.escape(str(key)), html.escape(str(shown))))
    return ''.join(rows)


def save_uploaded_file(uploaded):
    """request.FILES -> зберігаємо файл у папку media/uploads. Повертає текст-результат."""
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        return 'Файл не збережено: дозволені лише ' + ', '.join(sorted(ALLOWED_UPLOAD_EXT))
    if uploaded.size > MAX_UPLOAD_BYTES:
        return 'Файл не збережено: розмір більший за 2 МБ'
    storage = FileSystemStorage(location=settings.MEDIA_ROOT / 'uploads')
    saved_name = storage.save(uploaded.name, uploaded)   # Django сам чистить назву й уникає збігів
    return 'Файл збережено як {} ({} байт, {})'.format(saved_name, uploaded.size, uploaded.content_type)


def request_info(request):
    """Показує атрибути HttpRequest і будує відповідь через HttpResponse."""
    if not get_current_fitness_user(request):
        return redirect('login')

    # request.method: різна логіка для різних HTTP-методів
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])      # статус 405

    upload_result = ''
    if request.method == 'POST':
        uploaded = request.FILES.get('document')
        if uploaded:
            upload_result = save_uploaded_file(uploaded)
        else:
            upload_result = 'Файл не обрано'

    post_data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
    user = get_current_fitness_user(request)
    previous_visit = request.COOKIES.get('last_visit', 'це перший візит')

    content = '''
<center><h2>Request / Response у Django</h2>
<p>Шлях (request.path): {path}</p>
<p>Метод (request.method): {method}</p>
<p>Користувач (сесія): {user}</p>
<p>Параметр GET "q": {q}</p>
<p>Попередній візит (cookie last_visit): {last_visit}</p>
<p>{upload}</p>

<h3>request.GET</h3><table border="1" cellpadding="4">{get_rows}</table>
<h3>request.POST</h3><table border="1" cellpadding="4">{post_rows}</table>
<h3>request.COOKIES</h3><table border="1" cellpadding="4">{cookie_rows}</table>

<h3>Надіслати GET-запит</h3>
<form method="get"><input name="q" placeholder="пошук"> <button>GET</button></form>

<h3>Надіслати POST-запит і файл (request.FILES)</h3>
<form method="post" enctype="multipart/form-data">
  <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
  <input name="note" placeholder="нотатка"> <input type="file" name="document"> <button>POST</button>
</form>
<p><a href="{back}">Назад на панель</a></p>
</center>
'''.format(
        path=html.escape(request.path),
        method=html.escape(request.method),
        user=html.escape(user.username),
        q=html.escape(request.GET.get('q', '—')),      # у сучасному Django замість has_key(): key in request.GET
        last_visit=html.escape(previous_visit),
        upload=html.escape(upload_result),
        get_rows=rows_html(request.GET),
        post_rows=rows_html(post_data),
        cookie_rows=rows_html(request.COOKIES, hidden=HIDDEN_COOKIES),
        csrf=get_token(request),
        back='/dashboard/',
    )

    response = HttpResponse(content)                        # HttpResponse
    response['X-Practice'] = 'django-http'                  # __setitem__: додаємо заголовок
    response.set_cookie('last_visit', timezone.localtime().strftime('%Y-%m-%dT%H-%M-%S'))

    # write(): дописуємо до тіла відповіді; status_code, content і __getitem__ читаємо з response
    response.write(
        '<center><hr><p>status_code: {} | довжина content: {} байт | X-Practice: {}</p></center>'.format(
            response.status_code, len(response.content), response['X-Practice'])
    )
    return response