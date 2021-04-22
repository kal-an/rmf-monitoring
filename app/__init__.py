import json
import atexit
import logging
from logging.handlers import TimedRotatingFileHandler

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask import Flask
from flask.logging import default_handler
from flask_login import LoginManager
from flask_principal import Principal, Permission, RoleNeed
from pony.flask import Pony
from sqlalchemy import engine_from_config

from .models import User, db
from .utils.fetcher import Http_Fetcher
from .utils.scheduler import RMFScheduler
from .utils.app_logger import setup_log

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Пожалуйста, авторизуйтесь'

principals = Principal()
admin_permission = Permission(RoleNeed('admin'), RoleNeed('su'))
su_permission = Permission(RoleNeed('su'))

fetcher = Http_Fetcher()
scheduler = RMFScheduler()


def create_app(config=None):
    app = Flask(__name__)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = TimedRotatingFileHandler('app/logs/application.log', when="midnight", backupCount=7)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    app.logger.removeHandler(default_handler)
    app.logger.addHandler(file_handler)

    if config is None:
        config = 'config.TestingConfig'
    app.config.from_object(config)

    db.bind(env_json(app.config['PONY']))
    db.generate_mapping(create_tables=True)
    Pony(app)

    login_manager.init_app(app)
    principals.init_app(app)

    fetcher.init_config(env_json(app.config['HTTP_HEADER']))

    engine = engine_from_config(env_json(app.config['SQLALCHEMY']), prefix='sqlalchemy.')
    jobstores = {
        'default': SQLAlchemyJobStore(engine=engine, tablename=app.config['JOBSTORES']['default']),
        'service_jobs': SQLAlchemyJobStore(engine=engine, tablename=app.config['JOBSTORES']['service_jobs'])
    }
    scheduler.init_config(fetcher)

    scheduler.configure(jobstores=jobstores, executors=app.config['EXECUTORS'], job_defaults=app.config['JOB_DEFAULTS'])
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())

    from .main import main as main_blueprints, bp_filters

    app.register_blueprint(main_blueprints)
    app.register_blueprint(bp_filters)
    return app


def env_json(json_str) -> dict:
    json_str = json_str.replace("'", "\"")
    return json.loads(json_str)
