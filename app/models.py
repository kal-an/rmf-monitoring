from datetime import datetime

from flask_login import UserMixin
from pony.orm import *

db = Database()


class Host(db.Entity):
    _table_ = 'HOST'
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    dns = Optional(str, unique=True)
    resources = Set('Resource')


class Resource(db.Entity):
    _table_ = 'RESOURCE'
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    type = Required(str)
    host = Required(Host)
    performances = Set('Performance')
    performances_h = Set('Performance_H')
    performances_d = Set('Performance_D')
    performances_w = Set('Performance_W')
    performances_m = Set('Performance_M')
    metrics = Set('Metric')


class Metric(db.Entity):
    _table_ = 'METRIC'
    id = PrimaryKey(int, auto=True)
    metric_id = Required(str)
    desc = Required(str)
    format = Optional(str)
    resources = Set(Resource)
    performances = Set('Performance')
    performances_h = Set('Performance_H')
    performances_d = Set('Performance_D')
    performances_w = Set('Performance_W')
    performances_m = Set('Performance_M')
    composite_index(metric_id, desc)


class Performance(db.Entity):
    _table_ = 'PERFORMANCE'
    id = PrimaryKey(int, auto=True)
    time_collect = Required(datetime)
    time_db_write = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    time_start = Required(datetime)
    time_end = Required(datetime)
    col1 = Optional(str)
    col2 = Required(str)
    resource = Required(Resource)
    metric = Required(Metric)


class Performance_H(db.Entity):
    _table_ = 'PERFORMANCE_H'
    id = PrimaryKey(int, auto=True)
    time_collect = Required(datetime)
    time_db_write = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    time_start = Required(datetime)
    time_end = Required(datetime)
    col1 = Optional(str)
    col2 = Required(str)
    resource = Required(Resource)
    metric = Required(Metric)


class Performance_D(db.Entity):
    _table_ = 'PERFORMANCE_D'
    id = PrimaryKey(int, auto=True)
    time_collect = Required(datetime)
    time_db_write = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    time_start = Required(datetime)
    time_end = Required(datetime)
    col1 = Optional(str)
    col2 = Required(str)
    resource = Required(Resource)
    metric = Required(Metric)


class Performance_W(db.Entity):
    _table_ = 'PERFORMANCE_W'
    id = PrimaryKey(int, auto=True)
    time_collect = Required(datetime)
    time_db_write = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    time_start = Required(datetime)
    time_end = Required(datetime)
    col1 = Optional(str)
    col2 = Required(str)
    resource = Required(Resource)
    metric = Required(Metric)


class Performance_M(db.Entity):
    _table_ = 'PERFORMANCE_M'
    id = PrimaryKey(int, auto=True)
    time_collect = Required(datetime)
    time_db_write = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    time_start = Required(datetime)
    time_end = Required(datetime)
    col1 = Optional(str)
    col2 = Required(str)
    resource = Required(Resource)
    metric = Required(Metric)


class Log_Error(db.Entity):
    _table_ = 'LOG_ERROR'
    id = PrimaryKey(int, auto=True)
    type = Optional(str)
    time_write = Required(datetime)
    text = Required(str)


class User(db.Entity, UserMixin):
    _table_ = 'USER'
    id = PrimaryKey(int, auto=True)
    login = Required(str, max_len=20, unique=True)
    dn = Required(str, max_len=50, unique=True)
    full_name = Required(str, max_len=100, unique=True)
    role = Required('Role')
    resources = Set('Log_User')
    created_at = Required(datetime, sql_default='CURRENT_TIMESTAMP')

    @staticmethod
    def try_login(dn, password):
        from app.main.views import get_ldap_connection
        conn = get_ldap_connection()
        conn.simple_bind_s(dn, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False


class Role(db.Entity):
    _table_ = 'ROLE'
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    users = Set(User)


class Log_User(db.Entity):
    _table_ = 'LOG_USER'
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    time_write = Required(datetime)
    text = Required(str)


class Host_Config(db.Entity):
    _table_ = 'HOST_CONFIG'
    id = PrimaryKey(int, auto=True)
    host = Required(str, unique=True)


class R_Templates(db.Entity):
    _table_ = 'REPORT_TEMPLATES'
    id = PrimaryKey(int, auto=True)
    host = Required(str)
    rtype = Required(str)
    rname = Required(str)
    metric_id = Required(str)
    title = Required(str)
    desc = Required(str)
    elements = Required(StrArray)
    unit = Required(str)
    value = Required(str)
    created_at = Required(datetime, sql_default='CURRENT_TIMESTAMP')
