from time import sleep

import ldap

from app import admin_permission, scheduler, fetcher, login_manager, su_permission, setup_log
from . import main
from flask import current_app, render_template, request, redirect, jsonify, send_file, flash, url_for, session, \
    request_finished
from flask_login import login_required, login_user, logout_user, current_user
from flask_principal import RoleNeed, identity_changed, Identity, identity_loaded, UserNeed

from app.models import User
from app.utils.db_engine import *
from app.utils.tools import *
from app.utils.ldap_auth import LDAPAuth

logger = setup_log('app', 'app/logs/jobs.log')

@login_manager.user_loader
def load_user(user_id):
    return User.get(id=user_id)


@identity_loaded.connect
@db_session
def on_identity_loaded(sender, identity):
    identity.user = current_user

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role.name))


@request_finished.connect  # пишем действия пользователей в БД
def log_request(sender, **extra):
    if request.method in ['DELETE', 'POST'] and 'log' not in request.path:  # кроме входа/выхода
        try:
            db_log_user(current_user.id, f'{request.path}, {request.get_json()}')
        except Exception as e:
            current_app.logger.error(f'Error writing user action to DB : '
                         f'{current_user.login}, url: {request.path}, {request.get_json()}', exc_info=True)


@main.route("/", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('.get_reports'))
    else:
        return redirect(url_for('.login'))


@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.get_reports'))

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        try:
            user = User.get(login=username)
            if user is None:
                raise ValueError
        except ValueError:
            current_app.logger.warning(f'пользователь с именем {username} не существует')
            flash('пользователь не существует')
            return render_template('login.html', r=request)
        try:
            User.try_login(user.dn, password)
        except ldap.INVALID_CREDENTIALS:
            flash('неверный логин или пароль')
            return render_template('login.html', r=request)
        except ldap.SERVER_DOWN:
            current_app.logger.error(f'Error connect to LDAP', exc_info=True)
            flash('невозможно связаться с сервером LDAP для авторизации')
            return render_template('login.html', r=request)

        if user:
            login_user(user)
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
            try:
                db_log_user(user.id, request.path)
            except Exception as e:
                current_app.logger.error(f'Error writing user logon to DB : {user.login}, url: {request.path}', exc_info=True)
            return redirect(request.args.get('next') or url_for('.get_reports'))
        else:
            flash('пользователь не существует')
            return render_template('login.html', r=request)
    return render_template('login.html', r=request)


@main.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    user = User.get(id=current_user.id)
    try:
        db_log_user(user.id, request.path)
    except Exception as e:
        current_app.logger.error(f'Error writing user logout to DB : {user.login}, url: {request.path}', exc_info=True)
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    flash('выполнен выход')
    return redirect('/login')


@main.route("/admin", methods=['POST', 'GET', 'DELETE'])
@login_required
@su_permission.require(http_exception=401)
def admin():
    users = get_db_all_users()
    roles = get_db_all_roles()

    if request.method == 'POST':
        json = request.get_json(force=True)
        login = json.get('login', '')
        dn = json.get('dn', '')
        full_name = json.get('full_name', '')
        role_id = json.get('role_id', '')
        try:
            db_add_user(login, dn, full_name, role_id)
            response = get_db_all_users()
        except Exception as e:
            current_app.logger.error(f'Error adding user to DB : {e}', exc_info=True)
            return jsonify(error='ошибка добавления в БД')
        return jsonify(response)

    if request.method == 'DELETE':
        json = request.get_json(force=True)
        user_id = json.get('id', '')
        try:
            db_del_user(user_id)
            return jsonify(success=1)
        except Exception as e:
            current_app.logger.error(f'Error delete user from DB : {e}', exc_info=True)
            return jsonify(error='ошибка удаления из БД')

    return render_template('admin.html', entries=users, roles=roles)


@main.route("/designer", methods=['GET', 'POST'])
@login_required
def get_designer():
    restypes = get_db_restype()

    if request.method == 'POST':
        json = request.get_json(force=True)
        request_type = json.get('request_type', '')
        rtype = json.get('rtype', None)
        rname = json.get('rname', None)
        metric = json.get('metric', None)

        if request_type == 'rname':
            return get_db_resname(rtype)
        elif request_type == 'metric':
            return get_db_metric(rtype, rname)
        elif request_type == 'perform':
            unit = json.get('unit', '')
            value = json.get('value', '')
            start_time = json.get('start-time', '')
            elements = json.get('elements', [])
            return get_db_perform(rtype, rname, metric, elements, unit, value, start_time)

    return render_template('designer.html', restypes=restypes)


@main.route("/reports", methods=['GET', 'POST'])
@login_required
def get_reports():
    templates = get_db_report_templates()

    if request.method == 'POST':
        json = request.get_json(force=True)
        request_report = json.get('report', '')
        is_compare = json.get('is-compare', False)
        unit = json.get('unit', '')
        value = json.get('value', '')
        start_time = json.get('start-time', '')

        if is_compare:
            return get_db_comparative_report(request_report, unit, value, start_time)

        return get_db_report(request_report, unit, value, start_time)

    return render_template('reports.html', templates=templates)


@main.route("/reports/delete", methods=['POST'])
@login_required
@admin_permission.require(http_exception=401)
def remove_reports():
    if request.method == 'POST':  # удаляем шаблон из списка
        json = request.get_json(force=True)
        report_id = json.get('id', '')
        try:
            db_del_report_template(report_id)
            return jsonify(success=1)
        except Exception as e:
            current_app.logger.error(f'Error delete report from DB : {e}', exc_info=True)
            return jsonify(error='ошибка удаления из БД')


@main.route("/get_xls", methods=['POST'])
@login_required
def get_xls():
    if request.method == 'POST':
        json = request.get_json(force=True)
        request_report = json.get('request_report', '')
        unit = json.get('unit', '')
        value = json.get('value', '')
        start_time = json.get('start-time', '')

        if json.get('request_type', '') == 'perform':
            rtype = json.get('rtype', '')
            rname = json.get('rname', '')
            metric = json.get('metric', '')
            start_time = json.get('start-time', '')
            elements = json.get('elements', [])
            report = get_db_perform(rtype, rname, metric, elements, unit, value, start_time)
        else:
            is_compare = json.get('is-compare', False)
            if is_compare:
                report = get_db_comparative_report(request_report, unit, value, start_time)
            else:
                report = get_db_report(request_report, unit, value, start_time)

        output = create_xls(report['values'])
        output.seek(0)

        return send_file(output, attachment_filename=f'{datetime.today().strftime("%Y-%m-%d_%H-%M-%S")}.xls',
                         mimetype='application/vnd.ms-excel',
                         as_attachment=True)


@main.route("/scheduler/delete", methods=["POST"])
@login_required
@admin_permission.require(http_exception=401)
def remove_job():
    jobstore = 'default'
    json_parms = request.get_json(force=True)
    job_id = json_parms.get('job_id', '')
    if job_id != '':
        scheduler.remove_job(job_id, jobstore)
        return jsonify('success')


@main.route("/scheduler", methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=401)
def get_scheduler():
    jobstore = 'default'
    jobs = scheduler.get_all_jobs(jobstore)
    hosts = get_db_all_hosts()
    if request.method == 'POST':
        resources = request.get_json(force=True)
        scheduler.add_jobs(execute_job, resources, jobstore)
        jobs = scheduler.get_all_jobs(jobstore)
        return jsonify(jobs=jobs)
    return render_template('scheduler.html', entries=jobs, hosts=hosts)


@main.route("/get_resources", methods=['POST'])
def get_resources():
    json_parms = request.get_json(force=True)
    response = fetcher.request_resource(json_parms)
    return jsonify(response)


@main.route("/host_editor", methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=401)
def get_host_editor():
    hosts = get_db_all_hosts()
    if request.method == 'POST':
        json_parms = request.get_json(force=True)
        if 'request_type' in json_parms:
            response = fetcher.request_resource(json_parms)
            if 'error' not in response:
                return jsonify(success=1)
        else:
            response = db_add_host(json_parms['host'])
            if 'error' in response:
                return response
            response = get_db_all_hosts()
        return jsonify(response)
    else:
        return render_template('host_editor.html', hosts=hosts)


@main.route("/host_editor/delete", methods=['POST'])
@login_required
@admin_permission.require(http_exception=401)
def remove_host():
    json_parms = request.get_json(force=True)
    name = json_parms.get('host', '')
    try:
        db_del_host(name)
        response = get_db_all_hosts()
    except Exception as e:
        current_app.logger.error(f'Error delete host from DB : {e}', exc_info=True)
        return {'error': 'ошибка удаления из БД'}
    return jsonify(response)


@main.route("/storage_config", methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=401)
def get_storage_config():
    jobstore = 'service_jobs'
    jobs = scheduler.get_all_service_jobs(jobstore)
    metrics = get_db_all_metrics()

    if request.method == 'POST':
        json_parms = request.get_json(force=True)
        scheduler.add_service_jobs(execute_service_job, json_parms, jobstore)
        jobs = scheduler.get_all_service_jobs(jobstore)
        return jsonify(jobs=jobs)

    return render_template('storage_config.html', jobs=jobs, metrics=metrics)


@main.route("/storage_config/delete", methods=['POST'])
@login_required
@admin_permission.require(http_exception=401)
def remove_service_job():
    jobstore = 'service_jobs'
    json_parms = request.get_json(force=True)
    id = json_parms.get('id', '')
    scheduler.remove_job(id, jobstore)
    response = scheduler.get_all_service_jobs(jobstore)
    return jsonify(response)


@main.route("/log_error")
@login_required
@admin_permission.require(http_exception=401)
def get_log_error():
    logs = get_db_log_error()

    return render_template('log_error.html', logs=logs)


@main.route("/log_user")
@login_required
@su_permission.require(http_exception=401)
def get_log_user():
    logs = get_db_log_user()

    return render_template('log_user.html', logs=logs)


@main.route("/add_template", methods=['POST'])
@login_required
@admin_permission.require(http_exception=401)
def add_template():
    if request.method == 'POST':
        json_parms = request.get_json(force=True)
        try:
            db_add_report_template(json_parms)
            return jsonify(success=1)
        except Exception as e:
            current_app.logger.error(f'Error adding report to DB : {e}', exc_info=True)
            return jsonify(error=f'Ошибка сохранения в БД {e}')


@main.errorhandler(401)
def permission_denied(e):
    return redirect(url_for('.get_reports'))


@main.errorhandler(404)
def page_not_found(e):
    return render_template('error_404.html')


@main.errorhandler(500)
def internal_error(e):
    return render_template('error_500.html')


def execute_job(**job_params):  # выполняем задания по планировщику
    params = {'host': job_params['host'],
              'resource': job_params['resource_url'],
              'id': job_params['metric_id'],
              'format': job_params.get('metric_format', '')
              }
    inserted = False
    while not inserted:
        try:
            fetcher.request_performance(params)
            inserted = True
        except Exception as e:
            logger.error(f'Error execution job, params {job_params}: {e}')
        if not inserted:
            logger.debug(f'Job execution will be repeated after 3 seconds')
            sleep(3)
        else:
            break


def execute_service_job(**job_params):  # выполняем сервисные задания
    tz_moscow = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(tz_moscow)
    inserted = False
    while not inserted:
        try:
            db_service_job(current_time, job_params)
            inserted = True
        except Exception as e:
            logger.error(f'Error execution service job : {e}', exc_info=True)
        if not inserted:
            logger.debug(f'Job execution will be repeated after 3 seconds')
            sleep(3)
        else:
            break


def get_ldap_connection():
    conn = LDAPAuth.get_ldap_connection(current_app.config['LDAP_URI'])
    return conn
