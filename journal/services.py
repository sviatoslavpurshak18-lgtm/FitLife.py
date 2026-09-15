import json
import logging
import random

import requests
from django.conf import settings
from django.utils import timezone

from accounts.models import FitnessUser
from catalog.models import MealPlan, Workout, UserWorkout
from .models import AiLog, AiLogMealPlan, AiLogWorkout

logger = logging.getLogger(__name__)


FOCUS_LABELS = {
    'груди': 'груди',
    'спина': 'спина',
    'ноги': 'ноги',
    'руки': 'руки (трицепс, біцепс, плечі)',
}

WARMUP_MIN = 8

# Час на одну вправу = підходи × (40 с виконання + відпочинок після підходу).
# Відпочинок залежить від групи м'язів (у секундах).
SET_WORK_SECONDS = 45
REST_SECONDS = {
    'груди': 180,   # 3 хв
    'спина': 180,   # 3 хв
    'ноги': 300,    # 5 хв
    'руки': 120,    # 2 хв
    'other': 90,    # прес, литки, шраги тощо
}

# Порядок груп у тренуванні (незалежно від акценту): груди, спина, ноги, руки, далі прес та інше.
GROUP_ORDER = ['груди', 'спина', 'ноги', 'руки', 'other']

# Якщо ліміт часу більший за програму, тренування добивається до ліміту:
# 1) додаємо нові вправи з банку (акцентна група частіше за інші),
# 2) потім підходи (до MAX_SETS),
# 3) і лише наприкінці трохи збільшуємо відпочинок (до MAX_REST_EXTRA понад мінімум).
MAX_SETS = 6
MAX_REST_EXTRA = 120   # секунд понад мінімальний відпочинок групи (більше для тривалих тренувань)
REST_STEP = 15         # крок збільшення відпочинку, секунд


def ex(name, sets, reps, minutes=None):
    """Вправа банку. Параметр minutes залишено для сумісності й не використовується:
    час тепер рахується з відпочинку (див. exercise_seconds)."""
    return {
        'name': name,
        'sets': sets,
        'reps': reps,
    }


def male_bank():
    return {
        'груди': [
            [
                ex('жим лежачи (90% від макс)', 3, '1-2 повтори', 12),
                ex('жим на похилій лаві', 3, '10-12 повторів'),
                ex('батерфляй', 3, '12 повторів'),
            ],
            [
                ex('жим лежачи (70% від макс)', 5, '8 повторів', 14),
                ex('жим на похилій лаві', 3, '8-10 повторів'),
                ex('батерфляй', 3, '12 повторів'),
            ],
            [
                ex('жим лежачи (80% від макс)', 4, '5 повторів', 13),
                ex('жим на похилій лаві', 3, '8-10 повторів'),
                ex('батерфляй', 3, '12 повторів'),
            ],
        ],
        'спина': [
            [
                ex('станова тяга (70% від макс)', 4, '5-6 повторів', 14),
                ex('тяга штанги у нахилі', 4, '8-10 повторів'),
                ex('тяга верхнього блоку', 3, '10-12 повторів'),
            ],
            [
                ex('підтягування / тяга верхнього блоку', 4, '8-10 повторів'),
                ex('тяга нижнього блоку', 3, '12 повторів'),
                ex('гіперекстензія', 3, '12-15 повторів'),
            ],
            [
                ex('тяга гантелі у нахилі', 3, '10-12 повторів'),
                ex('тяга нижнього блоку', 3, '12 повторів'),
                ex('шраги', 2, '12-15 повторів'),
            ],
        ],
        'ноги': [
            [
                ex('присідання (80% від макс)', 4, '5-6 повторів', 14),
                ex('жим ногами (велика вага)', 3, '12 повторів'),
                ex('випади з гантелями', 3, '10 повторів на ногу'),
            ],
            [
                ex('присідання (70% від макс)', 4, '8-10 повторів', 13),
                ex('румунська тяга', 3, '10-12 повторів'),
                ex('підйом на носки', 3, '15-20 повторів'),
            ],
            [
                ex('жим ногами', 4, '10-12 повторів'),
                ex('згинання ніг лежачи', 3, '12 повторів'),
                ex('розгинання ніг', 3, '12-15 повторів'),
            ],
        ],
        'руки': [
            [
                ex('жим гантелей сидячи (плечі)', 4, '8-10 повторів'),
                ex('розгинання рук у кросовері (канатна або пряма рукоятка)', 3, '10-15 повторів'),
                ex('згинання рук із гантелями на біцепс', 3, '10-12 повторів'),
            ],
            [
                ex('розведення гантелей у сторони', 3, '20 повторів'),
                ex('згинання хватом молоток', 3, '10-12 повторів'),
                ex('розгинання рук на трицепс у кросовері', 2, '12-15 повторів'),
            ],
            [
                ex('відведення рук у тренажері на задню дельту', 3, '20 повторів'),
                ex('згинання рук на біцепс у кросовері', 3, '10 повторів'),
                ex('французький жим', 3, '10-12 повторів'),
            ],
        ],
        'other': [
            ex('скручування на прес (на лаві)', 3, '20-25 повторів', 6),
            ex('підйом ніг у висі на турніку', 3, '15-20 повторів', 6),
            ex('шраги', 2, '12-15 повторів', 5),
            ex('гіперекстензія', 3, '12-15 повторів', 7),
            ex('підйом на носки', 3, '15-20 повторів', 6),
        ],
    }


def female_bank():
    return {
        'груди': [
            [
                ex('жим гантелей лежачи', 4, '10-12 повторів'),
                ex('жим гантелей на похилій лаві', 3, '10-12 повторів'),
                ex('розведення гантелей лежачи', 3, '12-15 повторів'),
            ],
            [
                ex('віджимання від підлоги або від лави', 3, '10-15 повторів'),
                ex('жим в тренажері на груди', 3, '12 повторів'),
                ex('зведення рук у кросовері', 3, '12-15 повторів'),
            ],
            [
                ex('жим гантелей лежачи', 3, '8-10 повторів'),
                ex('батерфляй', 3, '12-15 повторів'),
                ex('віджимання на брусах (гравітон / допомога)', 3, '8-12 повторів'),
            ],
        ],
        'спина': [
            [
                ex('тяга верхнього блоку широким хватом', 4, '10-12 повторів'),
                ex('тяга горизонтального блоку', 3, '12 повторів'),
                ex('тяга гантелі у нахилі', 3, '10-12 повторів'),
            ],
            [
                ex('підтягування в гравітоні', 3, '8-12 повторів'),
                ex('тяга верхнього блоку зворотним хватом', 3, '10-12 повторів'),
                ex('гіперекстензія', 3, '12-15 повторів'),
            ],
            [
                ex('тяга нижнього блоку', 3, '12 повторів'),
                ex('пуловер у кросовері', 3, '12-15 повторів'),
                ex('тяга до обличчя (face pull)', 3, '15-20 повторів'),
            ],
        ],
        'ноги': [
            [
                ex('сідничний місток (hip thrust)', 4, '10-12 повторів'),
                ex('присідання зі штангою або в Сміті', 4, '8-10 повторів', 12),
                ex('болгарські випади', 3, '10 повторів на ногу'),
            ],
            [
                ex('румунська тяга з гантелями', 4, '10-12 повторів'),
                ex('розгинання ніг', 3, '12-15 повторів'),
                ex('згинання ніг лежачи', 3, '12 повторів'),
            ],
            [
                ex('жим ногами', 4, '12-15 повторів'),
                ex('відведення ноги у кросовері на сідниці', 3, '12-15 повторів'),
                ex('підйом на носки', 3, '15-20 повторів'),
            ],
        ],
        'руки': [
            [
                ex('жим гантелей сидячи (плечі)', 4, '10-12 повторів'),
                ex('розведення гантелей у сторони', 3, '15-20 повторів'),
                ex('згинання рук на біцепс з гантелями', 3, '10-12 повторів'),
            ],
            [
                ex('розгинання рук на блоці з канатом', 3, '12-15 повторів'),
                ex('згинання хватом молоток', 3, '10-12 повторів'),
                ex('відведення рук у тренажері на задню дельту', 3, '15-20 повторів'),
            ],
            [
                ex('біцепс на блоці', 3, '10-12 повторів'),
                ex('французький жим з гантеллю', 3, '10-12 повторів'),
                ex('підйом гантелей перед собою', 3, '12-15 повторів'),
            ],
        ],
        'other': [
            ex('прес (скручування на лаві)', 3, '15-20 повторів', 6),
            ex('планка', 3, '30-45 секунд', 5),
            ex('гіперекстензія', 3, '12-15 повторів', 7),
            ex('підйом на носки', 3, '15-20 повторів', 6),
            ex('тяга до обличчя (face pull)', 3, '15-20 повторів', 6),
        ],
    }


def male_extra():
    """Додаткові варіанти днів для чоловічого банку (дописуються до основних)."""
    return {
        'груди': [
            [
                ex('жим гантелей лежачи', 4, '8-10 повторів'),
                ex('жим гантелей на похилій лаві', 3, '10 повторів'),
                ex('розведення гантелей лежачи', 3, '12 повторів'),
            ],
            [
                ex('віджимання на брусах (акцент на груди)', 4, '8-12 повторів'),
                ex('зведення рук у кросовері знизу вгору', 3, '12-15 повторів'),
                ex('пуловер із гантеллю', 3, '12 повторів'),
            ],
            [
                ex('жим лежачи (65% від макс)', 4, '10 повторів', 12),
                ex('жим у тренажері на груди', 3, '10-12 повторів'),
                ex('батерфляй', 3, '15 повторів'),
            ],
        ],
        'спина': [
            [
                ex('тяга штанги до поясу зворотним хватом', 4, '8-10 повторів'),
                ex('тяга Т-грифа', 3, '10 повторів'),
                ex('пуловер у кросовері', 3, '12-15 повторів'),
            ],
            [
                ex('підтягування широким хватом', 4, '6-10 повторів'),
                ex('тяга гантелі однією рукою', 3, '10 повторів на руку'),
                ex('тяга до обличчя (face pull)', 3, '15 повторів'),
            ],
            [
                ex('тяга в тренажері на спину', 4, '10 повторів'),
                ex('тяга верхнього блоку вузьким хватом', 3, '10-12 повторів'),
                ex('гіперекстензія', 3, '15 повторів'),
            ],
        ],
        'ноги': [
            [
                ex('присідання з паузою (70% від макс)', 4, '6-8 повторів', 13),
                ex('жим ногами', 3, '12 повторів'),
                ex('згинання ніг сидячи', 3, '12 повторів'),
            ],
            [
                ex('фронтальний присід', 4, '8 повторів', 12),
                ex('румунська тяга зі штангою', 3, '8-10 повторів'),
                ex('підйом на носки стоячи', 4, '15 повторів'),
            ],
            [
                ex('гакк-присідання', 4, '10 повторів'),
                ex('болгарські випади', 3, '10 повторів на ногу'),
                ex('розгинання ніг', 3, '15 повторів'),
            ],
        ],
        'руки': [
            [
                ex('жим штанги вузьким хватом', 4, '8-10 повторів'),
                ex('згинання рук зі штангою на біцепс', 3, '10 повторів'),
                ex('розведення гантелей у сторони', 3, '15 повторів'),
            ],
            [
                ex('віджимання на брусах (акцент на трицепс)', 3, '10 повторів'),
                ex('концентрований підйом на біцепс', 3, '12 повторів'),
                ex('тяга штанги до підборіддя', 3, '10 повторів'),
            ],
            [
                ex('жим Арнольда', 4, '10 повторів'),
                ex('розгинання рук через голову з гантеллю', 3, '12 повторів'),
                ex('згинання рук на біцепс на лаві Скотта', 3, '10 повторів'),
            ],
        ],
        'other': [
            ex('скручування на римському стільці', 3, '15 повторів', 6),
            ex('підйом ніг у висі', 3, '12 повторів', 6),
            ex('планка', 3, '45 секунд', 5),
            ex('скручування на блоці', 3, '15 повторів', 6),
        ],
    }


def female_extra():
    """Додаткові варіанти днів для жіночого банку."""
    return {
        'груди': [
            [
                ex('жим гантелей лежачи під кутом', 3, '12 повторів'),
                ex('розведення в тренажері', 3, '15 повторів'),
                ex('віджимання з колін', 3, '12 повторів'),
            ],
            [
                ex('зведення рук у кросовері', 3, '15 повторів'),
                ex('жим у тренажері на груди', 3, '12 повторів'),
                ex('пуловер із гантеллю', 3, '12 повторів'),
            ],
            [
                ex('жим у Сміті на похилій лаві', 3, '10-12 повторів'),
                ex('батерфляй', 3, '15 повторів'),
                ex('віджимання від лави', 3, '12 повторів'),
            ],
        ],
        'спина': [
            [
                ex('тяга гантелей у нахилі двома руками', 3, '12 повторів'),
                ex('тяга верхнього блоку вузьким хватом', 3, '12 повторів'),
                ex('гіперекстензія', 3, '15 повторів'),
            ],
            [
                ex('тяга в тренажері на спину', 3, '12 повторів'),
                ex('пуловер у кросовері', 3, '15 повторів'),
                ex('тяга нижнього блоку', 3, '12 повторів'),
            ],
            [
                ex('підтягування в гравітоні', 3, '10 повторів'),
                ex('тяга штанги в нахилі (легка вага)', 3, '12 повторів'),
                ex('тяга до обличчя (face pull)', 3, '15 повторів'),
            ],
        ],
        'ноги': [
            [
                ex('присідання сумо з гантеллю', 4, '12 повторів'),
                ex('сідничний місток (hip thrust)', 4, '10-12 повторів'),
                ex('відведення ноги назад у кросовері', 3, '15 повторів'),
            ],
            [
                ex('випади назад', 3, '12 повторів на ногу'),
                ex('жим ногами вузькою постановкою', 3, '12 повторів'),
                ex('згинання ніг сидячи', 3, '15 повторів'),
            ],
            [
                ex('станова тяга на прямих ногах', 3, '12 повторів'),
                ex('відведення ніг у тренажері', 3, '15 повторів'),
                ex('підйом на носки сидячи', 3, '20 повторів'),
            ],
        ],
        'руки': [
            [
                ex('жим гантелей сидячи (плечі)', 3, '12 повторів'),
                ex('згинання хватом молоток', 3, '12 повторів'),
                ex('розгинання рук на блоці з канатом', 3, '15 повторів'),
            ],
            [
                ex('розведення гантелей у нахилі (задня дельта)', 3, '15 повторів'),
                ex('згинання рук на біцепс на блоці', 3, '12 повторів'),
                ex('французький жим з EZ-грифом', 3, '12 повторів'),
            ],
            [
                ex('жим Арнольда', 3, '12 повторів'),
                ex('згинання рук з EZ-штангою на біцепс', 3, '12 повторів'),
                ex('віджимання на брусах у гравітоні', 3, '10 повторів'),
            ],
        ],
        'other': [
            ex('скручування на блоці', 3, '15 повторів', 6),
            ex('підйом ніг у висі', 3, '12 повторів', 6),
            ex('бічна планка', 3, '30 секунд на сторону', 5),
        ],
    }


def with_extra(base, extra):
    merged = {key: list(value) for key, value in base.items()}
    for key, value in extra.items():
        merged[key].extend(value)
    return merged


def balance_groups():
    """Інші групи, які додаються до тренування з акцентом."""
    return {
        'груди': ['спина', 'ноги', 'руки'],
        'спина': ['груди', 'ноги', 'руки'],
        'ноги': ['груди', 'спина', 'руки'],
        'руки': ['груди', 'спина', 'ноги'],
    }


def sets_word(n):
    n = int(n)
    if n == 1:
        return 'підхід'
    if 2 <= n <= 4:
        return 'підходи'
    return 'підходів'


def with_group(item, group):
    """Копія вправи з позначкою групи м'язів (від неї залежить відпочинок)."""
    return {**item, 'group': group}


def rest_seconds(item):
    """Відпочинок після підходу: мінімум групи + додаток, який з'являється при добиванні до ліміту."""
    base = REST_SECONDS.get(item.get('group', 'other'), REST_SECONDS['other'])
    return base + int(item.get('rest_extra', 0))


def exercise_seconds(item):
    """Скільки секунд іде на вправу: підходи × (40 с + відпочинок)."""
    return int(item['sets']) * (SET_WORK_SECONDS + rest_seconds(item))


def format_duration(seconds):
    seconds = int(round(seconds))
    minutes, sec = divmod(seconds, 60)
    if minutes and sec:
        return f"{minutes} хв {sec} с"
    if minutes:
        return f"{minutes} хв"
    return f"{sec} с"


def format_line(item):
    """Рядок програми. Після | йдуть відпочинок і час на вправу — їх читає parse_program."""
    return (
        f"— {item['name']}, {item['sets']} {sets_word(item['sets'])} {item['reps']}"
        f" | відпочинок {format_duration(rest_seconds(item))}"
        f" | {format_duration(exercise_seconds(item))}"
    )


def session_seconds(items):
    return WARMUP_MIN * 60 + sum(exercise_seconds(item) for item in items)


def session_minutes(items):
    """Тривалість тренування в хвилинах, округлена вгору."""
    return -(-session_seconds(items) // 60)


def trim_to_limit(items, max_minutes, min_keep=3):
    """Підганяє тренування під ліміт часу: спершу прибирає вправи з кінця,
    а якщо цього мало, зменшує кількість підходів у найдовшої вправи (не менше 2)."""
    limit = max_minutes * 60
    result = list(items)
    while len(result) > min_keep and session_seconds(result) > limit:
        result.pop()
    while session_seconds(result) > limit:
        longest = max(
            (i for i, item in enumerate(result) if int(item['sets']) > 2),
            key=lambda i: exercise_seconds(result[i]),
            default=None,
        )
        if longest is None:
            break
        result[longest] = {**result[longest], 'sets': int(result[longest]['sets']) - 1}
    while len(result) > 1 and session_seconds(result) > limit:
        result.pop()
    return result


def expand_to_limit(items, max_minutes):
    """Добиває тренування до ліміту часу: спершу додає підходи, потім відпочинок.
    items іде в порядку пріоритету (спочатку вправи акценту), тож вони отримують підходи першими."""
    limit = max_minutes * 60
    items = [{**item, 'rest_extra': int(item.get('rest_extra', 0))} for item in items]

    # 1) підходи: по одному по колу, до MAX_SETS
    changed = True
    while changed:
        changed = False
        for item in items:
            if int(item['sets']) >= MAX_SETS:
                continue
            if session_seconds(items) + SET_WORK_SECONDS + rest_seconds(item) <= limit:
                item['sets'] = int(item['sets']) + 1
                changed = True

    # 2) відпочинок: крок REST_STEP одразу для всієї групи м'язів, щоб відпочинок у групі був однаковий
    groups = []
    for item in items:
        if item['group'] not in groups:
            groups.append(item['group'])
    changed = True
    while changed:
        changed = False
        for group in groups:
            members = [i for i in items if i['group'] == group and i['rest_extra'] + REST_STEP <= MAX_REST_EXTRA]
            cost = sum(int(i['sets']) * REST_STEP for i in members)
            if members and session_seconds(items) + cost <= limit:
                for i in members:
                    i['rest_extra'] += REST_STEP
                changed = True

    # 3) дотягування: лишок часу роздаємо окремим вправам
    changed = True
    while changed:
        changed = False
        for item in items:
            if item['rest_extra'] + REST_STEP > MAX_REST_EXTRA:
                continue
            if session_seconds(items) + int(item['sets']) * REST_STEP <= limit:
                item['rest_extra'] += REST_STEP
                changed = True
    return items


def name_key(item):
    return item['name'].strip().lower()


def unique_by_name(items):
    """Залишає першу вправу з кожною назвою."""
    seen, result = set(), []
    for item in items:
        if name_key(item) not in seen:
            seen.add(name_key(item))
            result.append(item)
    return result


def flatten(entries):
    """Банк групи — список варіантів (списків) або плоский список вправ. Повертає унікальні вправи."""
    seen, result = set(), []
    for entry in entries:
        for item in (entry if isinstance(entry, list) else [entry]):
            if item['name'] not in seen:
                seen.add(item['name'])
                result.append(item)
    return result


def get_bank(gender):
    if (gender or '').lower() == 'жінка':
        return with_extra(female_bank(), female_extra())
    return with_extra(male_bank(), male_extra())


def add_from_bank(items, bank, focus, max_minutes, avoid_names=()):
    """Добирає нові вправи з банку, поки вони вміщуються в ліміт часу.

    Акцентна група отримує більше вправ, ніж інші. Спершу беруться вправи, яких немає в інших
    днях (avoid_names), і лише коли такі закінчились, дозволяються повтори. Якщо вправа з усіма
    підходами не влазить, пробуємо з меншою кількістю підходів (не менше 2)."""
    limit = max_minutes * 60
    items = list(items)
    if len(items) >= 7:
        return items
    names = {name_key(item) for item in items}
    others = balance_groups()[focus]
    queues = {}
    for group in [focus] + others + ['other']:
        queues[group] = flatten(bank[group])
        random.shuffle(queues[group])
    rotation = [focus, others[0], focus, others[1], focus, others[2], 'other']

    for allow_repeat in (False, True):
        progress = True
        while progress:
            progress = False
            for group in rotation:
                if len(items) >= 7:
                    break
                for entry in queues[group]:
                    key = name_key(entry)
                    if key in names or (not allow_repeat and key in avoid_names):
                        continue
                    candidate = None
                    for sets in range(int(entry['sets']), 1, -1):
                        trial = with_group({**entry, 'sets': sets}, group)
                        if session_seconds(items) + exercise_seconds(trial) <= limit:
                            candidate = trial
                            break
                    if candidate is None:
                        continue
                    items.append(candidate)
                    names.add(key)
                    progress = True
                    break
    return items


def compose_day(items, max_minutes, min_keep=3, bank=None, focus=None, avoid_names=()):
    """Готує день: підганяє під ліміт, добирає вправи з банку (якщо передано bank), добиває
    підходами й відпочинком та розставляє групи в порядку груди → спина → ноги → руки → інше."""
    items = trim_to_limit(items, max_minutes, min_keep=min_keep)
    if bank is not None and focus is not None:
        items = add_from_bank(items, bank, focus, max_minutes, avoid_names)
    items = expand_to_limit(items, max_minutes)
    order = {group: index for index, group in enumerate(GROUP_ORDER)}
    return sorted(items, key=lambda item: order.get(item['group'], len(GROUP_ORDER)))


def compose_week(base_days, max_minutes, bank, focus):
    """Готує всі дні тижня. Вправи між днями по можливості не повторюються."""
    days = [trim_to_limit(unique_by_name(day), max_minutes, min_keep=3) for day in base_days]
    for i in range(len(days)):
        elsewhere = {name_key(item) for j, day in enumerate(days) if j != i for item in day}
        days[i] = compose_day(days[i], max_minutes, bank=bank, focus=focus, avoid_names=elsewhere)
    return days


def build_workout_program(user: FitnessUser):
    gender = (user.gender or 'чоловік').lower()
    focus = (user.focus_muscle_group or 'груди').lower()
    if focus not in FOCUS_LABELS:
        focus = 'груди'

    hours = float(user.session_hours or 2.0)
    max_minutes = int(hours * 60)
    bank = get_bank(gender)
    is_mass = 'набір' in (user.fitness_goal or '').lower()

    n_days = int(user.workouts_per_week or 3)
    if n_days < 1: n_days = 1
    if n_days > 3: n_days = 3
    # різні варіанти днів при кожній генерації (без повторів у межах одного тижня)
    focus_order = [i % len(bank[focus]) for i in range(n_days)]
    random.shuffle(focus_order)
    base_days = []
    for day_idx in range(n_days):
        session = [with_group(item, focus) for item in bank[focus][focus_order[day_idx]][:3]]
        for group in balance_groups()[focus]:
            session.append(with_group(random.choice(random.choice(bank[group])[:2]), group))
        session.append(with_group(random.choice(bank['other']), 'other'))
        base_days.append(session)

    days = []
    peak_minutes = 0
    for day_idx, session in enumerate(compose_week(base_days, max_minutes, bank, focus)):
        used = session_minutes(session)
        peak_minutes = max(peak_minutes, used)
        days.append((day_idx + 1, session, used))

    gender_word = 'жінка' if gender == 'жінка' else 'чоловік'
    program_name = f'акцент: {FOCUS_LABELS[focus]}'
    lines = [
        f"програма тренувань {program_name}",
        f"стать: {gender_word} | ліміт сесії: {max_minutes} хв (не більше)",
        f"розминка: {WARMUP_MIN} хв | на підхід: {SET_WORK_SECONDS} с + відпочинок (мінімум за групою м'язів)",
        "",
    ]
    for num, session, used in days:
        lines.append(f"({num} тренування, ~{int(used)} хв)")
        lines.append("")
        for item in session:
            lines.append(format_line(item))
        lines.append("")
        lines.append("")

    title = f"Акцент {focus}"[:45]
    difficulty = "Hard" if is_mass or hours >= 2 else "Medium"
    return {
        'title': title,
        'difficulty': difficulty,
        'duration_min': min(max_minutes, int(peak_minutes) or max_minutes),
        'program_text': "\n".join(lines).strip(),
        'url': '',
        'focus_label': FOCUS_LABELS[focus],
        'max_minutes': max_minutes,
    }


class AiUnavailable(Exception):
    """AI недоступний (не налаштований ключ API)."""


def query_openrouter(messages, max_tokens=800, timeout=60):
    """Запит до OpenRouter. Та сама схема, що в test.py від викладача.

    messages: список {"role": "system"|"user"|"assistant", "content": "..."}.
    Повертає текст відповіді моделі."""
    if not settings.OPENROUTER_API_KEY:
        raise AiUnavailable("AI не налаштований: не задано змінну середовища OPENROUTER_API_KEY.")

    response = requests.post(
        settings.OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter {response.status_code}: {response.text[:300]}")

    data = response.json()
    choices = data.get("choices")
    if not choices:   # OpenRouter інколи повертає 200 з полем error
        raise RuntimeError(f"OpenRouter без відповіді: {str(data.get('error') or data)[:300]}")
    content = (choices[0].get("message") or {}).get("content")
    if not content or not content.strip():
        raise ValueError("Порожня відповідь AI")
    return content.strip()


def extract_json(text):
    """Дістає JSON з відповіді моделі, навіть якщо вона додала ```json ... ``` чи текст навколо."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("У відповіді AI немає JSON")
    return json.loads(text[start:end + 1])


SYSTEM_PROMPT = """Ти тренер, що складає програму тренувань у залі.
Відповідай ТІЛЬКИ валідним JSON без пояснень і без markdown.
Формат:
{
  "title": "до 45 символів",
  "difficulty": "Easy|Medium|Hard",
  "days": [
    {"exercises": [
      {"name": "...", "group": "груди|спина|ноги|руки|other", "sets": 3, "reps": "10-12 повторів"}
    ]}
  ]
}
Правила:
- КРИТИЧНО ВАЖЛИВО: Суворо враховуй обмеження по здоров'ю користувача ("обмеження_по_здоровю")!
  * При протрузіях, грижах або болю у попереку: ПОВНІСТЮ ВИКЛЮЧАЙ осьові навантаження на хребет (станову тягу, присідання зі штангою на плечах, жим штанги стоячи). Замінюй їх безпечними аналогами в тренажерах (жим ногами з безпечним кутом, згинання/розгинання ніг, тяга верхнього/нижнього блоку, гіперекстензія без ваги);
  * При болю у колінах: виключай болгарські випади та глибокі присідання, віддавай перевагу згинанню/розгинанню ніг у тренажерах та сідничному містку;
  * При травмах плечей: виключай жими з-за голови та травмонебезпечні амплітуди.
- Кількість днів (об'єктів у масиві "days") має суворо дорівнювати значенню "тренувань_на_тиждень" з профілю користувача (від 1 до 3 днів)! пронумеруй їх від 1 до N.
- назви вправ ВИКЛЮЧНО чистою українською мовою без суржику (використовуй професійну українську фітнес-термінологію (наприклад, 'зведення рук у кросовері', 'згинання рук зі штангою', 'підйом на носки', 'лавці', 'батерфляй')), вправи не повторюються між днями;
- на кожен день максимум 7 вправ (від 5 до 7 вправ);
- ПОРЯДОК ВПРАВ У ДНІ Є СУВОРИМ (незалежно від акценту): спочатку завжди 'груди', потім 'спина', потім 'ноги', потім 'руки', і в кінці 'other';
- group це група м'язів вправи: груди, спина, ноги, руки (біцепс, трицепс, плечі) або other (прес, литки, шраги тощо);
- sets від 3 до 6, reps відповідно до мети: набір маси 6-12 повторів, схуднення і витривалість 12-20;
- час виконання 1 підходу = 45 секунд;
- відпочинок між підходами: груди від 3 до 5 хв (залежить від вільного часу сесії), спина від 3 хв, ноги від 5 хв, руки від 2 хв, other 1.5 хв;
- ліміт часу не треба заповнювати вручну: додаток сам доповнить кожен день іншими вправами до ліміту, а зайві вправи прибере."""

def program_from_ai(user):
    max_minutes = int(float(user.session_hours or 2.0) * 60)

    profile = {
        "стать": user.gender,
        "вік": user.age,
        "вага_кг": float(user.weight),
        "зріст_см": float(user.height),
        "мета": user.fitness_goal,
        "акцент": user.focus_muscle_group,
        "тренувань_на_тиждень": int(user.workouts_per_week or 3),
        "обмеження_по_здоровю": user.health_restrictions or "немає",
        "ліміт_сесії_хв": max_minutes,
    }

    answer = query_openrouter(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(profile, ensure_ascii=False)},
        ],
        max_tokens=3000,
        timeout=60,
    )
    data = extract_json(answer)

    days = data["days"]
    n_days = int(user.workouts_per_week or 3)
    if len(days) < n_days:
        while len(days) < n_days:
            days.append(days[len(days) % len(days)])
    elif len(days) > n_days:
        days = days[:n_days]

    lines = [f"програма тренувань {data['title']}",
             f"ліміт сесії: {max_minutes} хв (не більше)",
             f"розминка: {WARMUP_MIN} хв | на підхід: {SET_WORK_SECONDS} с + відпочинок (мінімум за групою м'язів)",
             ""]
    focus = (user.focus_muscle_group or 'груди').lower()
    if focus not in FOCUS_LABELS:
        focus = 'груди'
    bank = get_bank(user.gender)

    base_days = []
    for i, day in enumerate(days, 1):
        items = []
        for e in day["exercises"]:
            group = e.get("group") if e.get("group") in REST_SECONDS else 'other'
            items.append({
                'name': str(e["name"]),
                'sets': min(MAX_SETS, max(1, int(e["sets"]))),
                'reps': str(e["reps"]),
                'group': group,
            })
        if not items:
            raise ValueError(f"День {i} порожній")
        base_days.append(items)

    peak = 0
    # підгонка під ліміт, добір вправ з банку, добивання й порядок груп
    for i, items in enumerate(compose_week(base_days, max_minutes, bank, focus), 1):
        used = session_minutes(items)
        peak = max(peak, used)
        lines.append(f"({i} тренування, ~{used} хв)")
        lines.append("")
        for item in items:
            lines.append(format_line(item))
        lines += ["", ""]

    difficulty = data.get("difficulty")
    return {
        "title": str(data["title"])[:45],
        "difficulty": difficulty if difficulty in ("Easy", "Medium", "Hard") else "Medium",
        "duration_min": int(peak),
        "program_text": "\n".join(lines).strip(),
        "url": "",
        "focus_label": user.focus_muscle_group or "груди",
        "max_minutes": max_minutes,
    }


CHAT_SYSTEM_PROMPT = """Ти AI-тренер застосунку FitLife. Відповідай українською, коротко й по справі \
(до 200 слів), простим текстом без таблиць і заголовків.
Допомагай з тренуваннями, технікою вправ, харчуванням, відновленням і мотивацією, \
спираючись на дані користувача нижче.
Не став медичних діагнозів: при болю, травмах чи хворобах раджі звернутися до лікаря.
Якщо питання не про фітнес, здоров'я чи харчування, ввічливо поверни розмову до цих тем."""


def build_chat_context(user):
    parts = [
        f"Стать: {user.gender}; вік: {user.age}; вага: {user.weight} кг; "
        f"зріст: {user.height} см; ІМТ: {user.bmi}.",
        f"Мета: {user.fitness_goal}. Акцент: {user.focus_muscle_group}. "
        f"Ліміт сесії: {user.session_hours} год.",
        f"Обмеження по здоров'ю / травми: {user.health_restrictions or 'немає'}.",
    ]
    meal = MealPlan.objects.filter(users=user).first()
    if meal:
        parts.append(
            f"Раціон: {meal.daily_calorie} ккал "
            f"(білки {meal.proteins} г, жири {meal.fats} г, вуглеводи {meal.carbs} г)."
        )
    workout = Workout.objects.filter(users=user).first()
    if workout and workout.program_text:
        parts.append("Поточна програма тренувань:\n" + workout.program_text[:3000])
    return "\n".join(parts)


def ask_ai_coach(user, history, question):
    """history — список {'role': 'user'|'assistant', 'content': str}. Повертає текст відповіді."""
    messages = (
        [{"role": "system", "content": CHAT_SYSTEM_PROMPT + "\n\nДані користувача:\n" + build_chat_context(user)}]
        + list(history)
        + [{"role": "user", "content": question}]
    )
    return query_openrouter(messages, max_tokens=800, timeout=45)


class FitnessRecommendationEngine:
    def __init__(self, fitness_user: FitnessUser):
        self.user = fitness_user

    def calculate_calories_and_macros(self):
        weight = float(self.user.weight)
        height = float(self.user.height)
        age = float(self.user.age)
        gender = (self.user.gender or 'чоловік').lower()

        if gender == 'жінка':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        tdee = bmr * 1.4

        goal = self.user.fitness_goal.lower()
        if "набір" in goal:
            daily_calorie = int(tdee * 1.15)
            summary_text = "Визначено мету: набір м'язової маси. Встановлено профіцит калорій (15%)."
        elif "схуд" in goal:
            daily_calorie = int(tdee * 0.8)
            summary_text = "Визначено мету: схуднення. Встановлено дефіцит калорій (20%)."
        else:
            daily_calorie = int(tdee)
            summary_text = "Визначено мету: підтримання форми."

        proteins = int(weight * 2.0)
        fats = int(weight * 1.0)
        carbs = int(max(0, daily_calorie - (proteins * 4 + fats * 9)) / 4)

        return {
            'daily_calorie': daily_calorie,
            'proteins': proteins,
            'fats': fats,
            'carbs': carbs,
            'summary_text': summary_text
        }

    def generate_recommendations(self):
        data = self.calculate_calories_and_macros()
        program = None
        if settings.OPENROUTER_API_KEY:
            try:
                program = program_from_ai(self.user)
            except Exception:
                logger.exception("AI не впорався, використовую правила")
        if program is None:
            previous = Workout.objects.filter(users=self.user).values_list('program_text', flat=True).first()
            for _ in range(8):  # прагнемо програми, відмінної від попередньої
                program = build_workout_program(self.user)
                if program['program_text'] != previous:
                    break

        meal_plan, _ = MealPlan.objects.update_or_create(
            users=self.user,
            defaults={
                'daily_calorie': data['daily_calorie'],
                'proteins': data['proteins'],
                'fats': data['fats'],
                'carbs': data['carbs'],
            }
        )

        workout, _ = Workout.objects.update_or_create(
            users=self.user,
            defaults={
                'title': program['title'],
                'difficulty': program['difficulty'],
                'duration_min': program['duration_min'],
                'url': program['url'],
                'program_text': program['program_text'],
            }
        )

        UserWorkout.objects.update_or_create(
            users=self.user,
            workouts=workout,
            defaults={'assigned_date': timezone.localdate()},
        )

        full_summary = (
            f"{data['summary_text']} Стать: {self.user.gender}. "
            f"Акцент: {program['focus_label']}. Сесія до {program['max_minutes']} хв. "
            f"Раціон: {data['daily_calorie']} ккал "
            f"(Б:{data['proteins']}г, Ж:{data['fats']}г, В:{data['carbs']}г). "
            f"Програма: {workout.title}."
        )[:1000]
        ai_log = AiLog.objects.create(
            users=self.user,
            recommendation_summary=full_summary
        )
        AiLogWorkout.objects.create(ai_logs=ai_log, workouts=workout)
        AiLogMealPlan.objects.create(ai_logs=ai_log, meal_plans=meal_plan)

        return meal_plan, workout, ai_log