from datetime import datetime, timedelta

from flask import Blueprint

main = Blueprint('main', __name__)
bp_filters = Blueprint('filters', __name__)


@bp_filters.app_template_filter('timerange')
def get_time_range(lst):
    # вывод на странице списка со временем
    start = datetime.strptime('00:00', '%H:%M')
    end = datetime.strptime('23:30', '%H:%M')
    current = start
    lst = []
    while current <= end:
        lst.append(current.time())
        current += timedelta(minutes=30)
    return lst


@bp_filters.app_template_filter('translate')  # форматирование описания заданий
def make_word_translate(text):
    for _ in text.split():
        if 'trunc' in text:
            text = text.replace('trunc', 'Хранить:')
        elif 'log' in text:
            text = text.replace('log', 'Чистка логов:')
        elif 'summ' in text:
            text = text.replace('summ', 'Суммаризация:')
        elif 'detail' in text:
            text = text.replace('detail', 'подробные')
        elif 'hour' in text:
            text = text.replace('hour', 'час.')
        elif 'day' in text:
            text = text.replace('day', 'дн.')
        elif 'week' in text:
            text = text.replace('week', 'нед.')
        elif 'month' in text:
            text = text.replace('month', 'мес.')
        elif 'after' in text:
            text = text.replace('after', '')
    return text




from . import views
