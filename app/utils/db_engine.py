from collections import defaultdict
from datetime import datetime, timedelta

import pytz
from pony.orm import *
from pony.utils import between

from app import db


@db_session
def get_db_report(rid, unit, value, start_time):  # получить готовый отчет
    dt = datetime.strptime(start_time, '%d/%m/%Y %H:%M:%S')
    cls_select = db.Performance

    params = get_db_report_params(rid)
    if unit == '':
        unit = params.unit
        value = params.value
    data = {'unit': unit, 'value': value}  # для обновления в селекторе

    if unit == 'days':
        cls_select = db.Performance_H
    elif unit == 'weeks':
        cls_select = db.Performance_D
    elif unit == 'months':
        unit = 'days'
        value = 30 * int(value)
        cls_select = db.Performance_W
    elif unit == 'years':
        unit = 'days'
        value = 365 * int(value)
        cls_select = db.Performance_M

    interval = timedelta(**{unit: int(value)})
    result = select((p.col1, p.time_end, p.col2) for p in cls_select
                    if p.metric.metric_id == params.metric_id and p.col1 in params.elements
                    and p.resource.name == params.rname
                    and between(p.time_end, dt - interval, dt)).order_by(lambda: p.time_end)
    values = defaultdict(dict)
    for element, time, percent in result:
        values[element].update({time.strftime('%Y-%m-%d %H:%M:%S'): percent})
    return {'values': values, **data}


@db_session
def get_db_comparative_report(rid, unit, value, start_time):  # получить сравнительный готовый отчет
    dt = datetime.strptime(start_time, '%d/%m/%Y %H:%M:%S')
    cls_select = db.Performance

    params = get_db_report_params(rid)
    if unit == '':
        unit = params.unit
        value = params.value
    data = {'unit': unit, 'value': value}  # для обновления в селекторе

    if unit == 'days':
        cls_select = db.Performance_H
    elif unit == 'weeks':
        cls_select = db.Performance_D
    elif unit == 'months':
        unit = 'days'
        value = 30 * int(value)
        cls_select = db.Performance_W
    elif unit == 'years':
        unit = 'days'
        value = 365 * int(value)
        cls_select = db.Performance_M

    interval = timedelta(**{unit: int(value)})
    params = get_db_report_params(rid)
    result = select((concat(p.resource.host.name, ' ', p.col1), p.time_end, p.col2) for p in cls_select
                    if p.metric.metric_id == params.metric_id and p.col1 in params.elements
                    and between(p.time_end, dt - interval, dt)).order_by(lambda: p.time_end)
    values = defaultdict(dict)
    for element, time, percent in result:
        values[element].update({time.strftime('%Y-%m-%d %H:%M:%S'): percent})
    return {'values': values, **data}


@db_session
def get_db_perform(restype, resname, metric, elements, unit, value, start_time):
    dt = datetime.strptime(start_time, '%d/%m/%Y %H:%M:%S')
    value = int(value)
    cls_select = db.Performance

    if unit == 'days':
        cls_select = db.Performance_H
    elif unit == 'weeks':
        cls_select = db.Performance_D
    elif unit == 'months':
        unit = 'days'
        value = 30 * int(value)
        cls_select = db.Performance_W
    elif unit == 'years':
        unit = 'days'
        value = 365 * int(value)
        cls_select = db.Performance_M

    interval = timedelta(**{unit: value})
    result = select((p.time_end, p.col1, p.col2) for p in cls_select
                    if p.resource.name == resname and p.resource.type == restype and p.metric.metric_id == metric
                    and between(p.time_end, dt - interval, dt)).order_by(lambda: p.time_end)
    if elements != []:  # в случае если выбраны элементы в списке
        result = result.filter(lambda t, c1, c2: c1 in elements)  # выводим только по ним
    values = defaultdict(dict)
    for time, c1, c2 in result:
        values[c1].update({time.strftime('%Y-%m-%d %H:%M:%S'): c2})
    return {'values': values}


@db_session
def get_db_report_params(rid):  # параметры для отчета по id
    return db.R_Templates.get(id=rid)


@db_session
def get_db_host():  # список собранных хостов
    result = select(r for r in db.Host).order_by(lambda r: r.name)
    return [i.name for i in result]


@db_session
def get_db_restype():
    result = select(r.type for r in db.Resource)[:]
    return result


@db_session
def get_db_resname(restype):
    result = distinct(r.name for r in db.Resource if r.type == restype).order_by(lambda: r.name)
    return {'values': [i for i in result]}


@db_session
def get_db_all_metrics():
    result = select((m.metric_id, m.desc) for m in db.Metric).order_by(lambda: desc(m.desc))[:]
    return result


@db_session
def get_db_metric(restype, resname):
    result = distinct((m.metric_id, m.desc) for m in db.Metric for r in m.resources
                      if r.type == restype and r.name == resname).order_by(lambda: m.desc)[:]
    return {'values': [(id, desc) for id, desc in result]}


@db_session(retry=3)
def db_perform(host, resname, restype, metric_id, desc, format, time_collect, time_start, time_end, perform):
    h = db.Host.get(name=host[:4], dns=host)
    if h is None:
        h = db.Host(name=host[:4], dns=host)

    r = db.Resource.get(name=resname, type=restype, host=h)
    if r is None:
        r = db.Resource(name=resname, type=restype, host=h)

    m = db.Metric.get(metric_id=metric_id, desc=desc)
    if m is None:
        m = db.Metric(metric_id=metric_id, desc=desc, format=format)
    r.metrics.add(m)

    for el in perform:
        col1, col2 = el['columns'][0]['col'], el['columns'][1]['col']

        db.Performance(time_collect=time_collect, time_start=time_start, time_end=time_end,
                       resource=r, metric=m, col1=col1, col2=col2)


@db_session(retry=3)
def db_log_error(type, text):
    tz_moscow = pytz.timezone('Europe/Moscow')
    time = datetime.now(tz_moscow)
    db.Log_Error(time_write=time, type=type, text=text)


@db_session
def get_db_log_error():
    return select((r.time_write, r.type, r.text) for r in db.Log_Error).order_by(lambda: desc(r.time_write))[:]


@db_session
def get_db_log_user():
    return select((r.time_write, r.user.login, r.text) for r in db.Log_User).order_by(lambda: desc(r.time_write))[:100]


@db_session(retry=3)
def db_trunc_logs(interval):  # удаление логов с ошибками
    tz_moscow = pytz.timezone('Europe/Moscow')
    unit = next(iter(interval))  # единица времени
    current_time = datetime.now(tz_moscow).replace(hour=0, minute=0, second=0, microsecond=0)
    if unit == 'hours':  # для часовых значений
        # обнуляем последующие цифры после ЧАСА (HH:00:00:00)
        current_time = datetime.now(tz_moscow).replace(minute=0, second=0, microsecond=0)
    elif unit == 'months':  # для месячных значений
        period = timedelta(**{'days': 30 * interval['months']})
    elif unit == 'years':  # для годовых значений
        period = timedelta(**{'days': 365 * interval['years']})
    else:
        period = timedelta(**interval)

    delete(r for r in db.Log_Error if r.time_write < current_time - period)


@db_session(retry=3)
def db_trunc_metrics(id, data, interval):  # удаление данных по метрикам
    tz_moscow = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(tz_moscow).replace(hour=0, minute=0, second=0, microsecond=0)
    cls_delete = db.Performance

    if data == 'hour':  # для часовых значений
        cls_delete = db.Performance_H
    elif data == 'day':  # для суточных значений
        cls_delete = db.Performance_D
    elif data == 'week':  # для недельных значений
        cls_delete = db.Performance_W
    elif data == 'month':  # для месячных значений
        cls_delete = db.Performance_M

    unit = next(iter(interval))  # единица времени
    if unit == 'hours':  # для часовых значений
        # обнуляем последующие цифры после ЧАСА (HH:00:00:00)
        current_time = datetime.now(tz_moscow).replace(minute=0, second=0, microsecond=0)
    elif unit == 'months':  # для месячных значений
        period = timedelta(**{'days': 30 * int(interval['months'])})
    elif unit == 'years':  # для годовых значений
        period = timedelta(**{'days': 365 * int(interval['years'])})
    else:
        period = timedelta(**interval)
    delete(p for p in cls_delete if p.metric.metric_id == id and p.time_end < current_time - period)


@db_session(retry=3)
def db_summ_metrics(c_time, id, unit):  # суммаризация данных
    cls_select = db.Performance
    cls_insert = db.Performance_H
    try:
        interval = timedelta(**{unit: 1})
    except TypeError:
        pass

    if unit == 'hours':  # для часовых значений
        time_start = c_time.replace(minute=00, second=00, microsecond=0) - interval
        time_end = time_start.replace(minute=59, second=59, microsecond=0)
    elif unit == 'days':  # для суточных значений
        time_start = c_time.replace(hour=00, minute=00, second=00, microsecond=0) - interval
        time_end = time_start.replace(hour=23, minute=59, second=59, microsecond=0)
        cls_select = db.Performance_H
        cls_insert = db.Performance_D
    elif unit == 'weeks':  # для недельных значений
        time_start = c_time.replace(hour=00, minute=00, second=00, microsecond=0) - interval
        time_end = c_time.replace(hour=23, minute=59, second=59, microsecond=0) - timedelta(days=1)
        cls_select = db.Performance_D
        cls_insert = db.Performance_W
    elif unit == 'months':  # для месячных значений
        last_day_of_previous_month = c_time - timedelta(days=1)
        time_start = last_day_of_previous_month.replace(day=1, hour=00, minute=00, second=00, microsecond=0)
        time_end = last_day_of_previous_month.replace(hour=23, minute=59, second=59, microsecond=0)
        cls_select = db.Performance_W
        cls_insert = db.Performance_M

    result = select((p.resource.id, p.metric.id, p.col1, avg(float(p.col2))) for p in cls_select
                    if p.metric.metric_id == id
                    and between(p.time_end, time_start, time_end))[:]
    tz_moscow = pytz.timezone('Europe/Moscow')
    time_collect = datetime.now(tz_moscow)

    for rid, mid, c1, c2 in result:
        # вставка суммарных значений
        db.insert(cls_insert, resource=rid, metric=mid, time_collect=time_collect,
                  time_start=time_start, time_end=time_end, col1=c1, col2=str(round(c2, 2)))


def db_service_job(current_time, params):
    if params.get('type', '') == 'log':
        db_trunc_logs({f"{params.get('unit', '')}s": int(params.get('value', ''))})  # -s для формата timedelta
    elif params.get('type', '') == 'trunc':
        db_trunc_metrics(params.get('id', ''), params.get('data', ''),
                         {f"{params.get('unit', '')}s": int(
                             params.get('value', ''))})  # -s для формата timedelta
    elif params.get('type', '') == 'summ':
        db_summ_metrics(current_time, params.get('id', ''), f"{params.get('unit', '')}s")  # -s для формата timedelta

    db.disconnect()


@db_session
def db_log_user(username, text):  # лог по действиям пользователей
    tz_moscow = pytz.timezone('Europe/Moscow')
    db.Log_User(user=username, time_write=datetime.now(tz_moscow), text=text)


@db_session
def db_add_user(login, dn, full_name, role_id):  # добавление пользователей
    db.User(login=login, dn=dn, full_name=full_name, role=role_id)


@db_session
def db_del_user(user_id):  # удаление пользователей
    delete(u for u in db.User if u.id == user_id)


@db_session
def get_db_all_users():  # вывод всех пользователей
    result = select(u for u in db.User)
    return {u.id: {'login': u.login, 'dn': u.dn, 'full_name': u.full_name, 'role': u.role.name} for u in result}


@db_session
def get_db_all_roles():  # вывод всех ролей
    result = select(r for r in db.Role)
    return {r.id: r.name for r in result}


@db_session
def db_add_host(name):  # добавление хоста
    h = db.Host_Config.get(host=name)
    if h is None:
        db.Host_Config(host=name)
        return {'success': 'хост добавлен'}
    else:
        return {'error': 'хост уже существует в БД'}


@db_session
def db_del_host(name):  # удаление хоста
    delete(h for h in db.Host_Config if h.host == name)


@db_session
def get_db_all_hosts():  # список всех хостов из таблицы конфигурации
    result = select(h.host for h in db.Host_Config).order_by(lambda: h.host)[:]
    return {'hosts': [name for name in result]}


@db_session
def get_db_report_templates():  # список отчетов
    result = select((r.id, r.title, r.desc) for r in db.R_Templates).order_by(lambda: r.desc)[:]
    return result


@db_session
def db_add_report_template(parms):  # добавить шаблон
    db.R_Templates(host=parms.get('host', '-'), rtype=parms['rtype'], rname=parms['rname'],
                   metric_id=parms['metric_id'], title=parms['title'],
                   desc=parms['desc'], elements=parms['elements'],
                   unit=parms['unit'], value=parms['value'])


@db_session
def db_del_report_template(report_id):  # удалить  шаблон
    delete(r for r in db.R_Templates if r.id == report_id)
