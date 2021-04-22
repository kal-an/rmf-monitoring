import os


class BaseConfig:
    HTTP_HEADER = os.environ.get('HTTP_HEADER')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'db4mDMW9%202s'
    LDAP_URI = 'ldap://domain:3268'
    SQLALCHEMY_PREFIX = {'prefix': 'sqlalchemy.'}
    JOBSTORES = {
        'default': 'scheduled_jobs',
        'service_jobs': 'scheduled_service_jobs'
    }
    EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 150},
    }
    JOB_DEFAULTS = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 10
    }


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY = os.environ.get('SQLALCHEMY_DEVELOPMENT')
    PONY = os.environ.get('PONY_DEVELOPMENT')
    PORT = '8080'


class TestingConfig(BaseConfig):
    SQLALCHEMY = os.environ.get('SQLALCHEMY_TESTING')
    PONY = os.environ.get('PONY_TESTING')
    PORT = '8081'


class ProductionConfig(BaseConfig):
    SQLALCHEMY = os.environ.get('SQLALCHEMY_PRODUCTION')
    PONY = os.environ.get('PONY_PRODUCTION')
    PORT = '80'
