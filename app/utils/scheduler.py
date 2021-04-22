from datetime import timedelta

import pytz
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron
from .app_logger import setup_log

log = setup_log('apscheduler', 'app/logs/scheduler.log')


class RMFScheduler(BackgroundScheduler):

    def __init__(self, **options):
        super().__init__(**options)
        self.add_listener(self.my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    def init_config(self, fetcher):
        self.fetcher = fetcher

    def my_listener(self, event):
        job = self.get_job(event.job_id)
        if not event.exception:
            log.info(f'Executed job: {job.name}, params: {job.kwargs}')
        else:
            log.error(f'Crashed job: {job.name}, params: {job.kwargs}, event:{event.exception}')

    def get_all_jobs(self, jobstore):
        jobs = {}
        for i in self.get_jobs(jobstore=jobstore):
            jobs[i.id] = i.kwargs
            i.kwargs.update({'next_run': (i.next_run_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")})
        sorted_jobs = sorted(jobs.items(), key=lambda k_v: k_v[1]['resource_name'])
        sorted_jobs = {k: v for k, v in sorted_jobs}
        return sorted_jobs

    def get_all_service_jobs(self, jobstore):
        jobs = {}
        for job in self.get_jobs(jobstore=jobstore):
            jobs[job.id] = {'title': job.kwargs['name'], 'description': job.name,
                            'next_run': job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")}
        return jobs

    def add_jobs(self, func, params, jobstore):
        for p in params['resources']:
            self.add_job(func, 'interval',
                         kwargs=p, jobstore=jobstore, executor='default',
                         minutes=int(p['interval']), replace_existing=True,
                         id=f'{p["host"][:4]}_{p["resource_url"]}_{p["metric_id"]}',
                         name=f'Resource: {p["resource_name"].lstrip(",")}, '
                              f'metric:{p["metric_description"]}')

    # сервисные задания ( удаление, усреднение и т.д.)
    def add_service_jobs(self, func, job_params, jobstore):
        # проход по циклу всех временных периодов
        for p in job_params['params']:
            # выполняем каждый день по умолчанию
            trigger_period = {'day': '*/1'}
            # назначаем время старта
            start_time = {'hour': job_params.get('start_time')[0:2], 'minute': job_params.get('start_time')[3:5]}
            trigger_period.update(start_time)

            if job_params.get('type', '') == 'summ':  # если это задание по суммаризации то меняем период тригера

                if p.get('unit') == 'day':
                    trigger_period.update(day='*/1')  # выполняем каждый день
                elif p.get('unit') == 'week':
                    trigger_period.update(day_of_week='0')  # выполняем каждую неделю
                elif p.get('unit') == 'month':
                    trigger_period.update(day='1')  # выполняем каждый месяц
                else:
                    trigger_period = {'hour': '*/1'}  # выполняем каждый час по умолчанию

            tz_moscow = pytz.timezone('Europe/Moscow')
            trigger = cron.CronTrigger(**trigger_period, timezone=tz_moscow)

            j_id = job_params.get("id", "")
            j_name = job_params.get("name", "")
            j_type = job_params.get("type", "")
            j_data = p.get("data", "")
            j_value = p.get("value", "")
            j_unit = p.get("unit", "")

            # устанавливаем параметры для задания
            kwargs = {'id': j_id, 'name': j_name, 'type': j_type}
            kwargs.update(p)  # добавляем временной период

            self.add_job(func, trigger=trigger, replace_existing=True,
                         jobstore=jobstore, executor='default',
                         kwargs=kwargs,
                         id=f'{j_id}_{j_data}_{j_value}_{j_unit}',
                         name=f'{j_type} {j_data} {j_value} {j_unit}')
