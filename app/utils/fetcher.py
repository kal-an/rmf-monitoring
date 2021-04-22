import time
from _datetime import datetime

import pytz
import requests as r
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from app import db
from .db_engine import db_perform, db_log_error
from .xmlparser import *
from .app_logger import setup_log

log = setup_log('Http_Fetcher', 'app/logs/fetcher.log', 30)


class Http_Fetcher:

    def __init__(self):
        self.serialized_xml = {}
        self.headers = {}

    def init_config(self, headers):
        self.headers = headers

    def execute_request(self, host, xml, http_params={}):
        port = '8803'
        url = f'http://{host}:{port}/gpm/{xml}'
        try:
            headers = self.headers.get(host[5:], '')
            s = r.Session()
            # параметры на количество попыток для соединения. Повторяем также если были HTTP ошибки
            retries = Retry(total=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504))
            s.mount('http://', HTTPAdapter(max_retries=retries))
            response = s.get(url, headers=headers, params=http_params, timeout=5)
            if response.status_code == 200:
                return response
            else:
                log.error(f'Response code from {url} is {response.status_code}')
                return {'error': f'Response code from {url} is {response.status_code}'}
        except r.exceptions.ConnectionError as e:
            log.error(f'Connection error: {url}, {e}')
            return {'error': f'Connection error: {e}'}
        except r.exceptions.Timeout as e:
            log.error(f'Connection timeout with server: {url}, {e}')
            return {'error': f'Connection timeout with server: {e}'}
        except r.exceptions.RequestException as e:
            log.error(f'Exception with server: {url}, {e}')
            return {'error': f'Exception with server: {e}'}

    def request_performance(self, params):
        FILTER = 'HI=300'  # количество элементов для списка
        xml = 'perform.xml'
        http_params = {'id': params['id'], 'resource': params['resource'], }
        host = params['host']
        if 'list' in params.get('format', ''):  # если формат метрики список, то добавить filter
            http_params.update({'filter': FILTER})

        response = self.execute_request(host, xml, http_params)

        if 'error' not in response:  # если нет ошибок при ответе от сервера
            parser = XMLParser(response.text)
            serialized_xml = parser.get_serialized_xml()

            if len(serialized_xml['message']) == 0:  # если нет ошибок в метрике или ресурсе
                resource = serialized_xml['resources'].pop()
                restype = resource['restype']
                resname = resource['reslabel'].rstrip(restype).rstrip(',')
                metric = serialized_xml['listmetrics'].pop()
                metric_id, desc, format = metric['id'], metric['description'], metric['format']
                time_data = serialized_xml['time-data']
                time_start, time_end = time_data['display-start'], time_data['display-end']
                perform = serialized_xml['perform']
                tz_moscow = pytz.timezone('Europe/Moscow')
                time_collect = datetime.now(tz_moscow)

                inserted = False
                while not inserted:
                    try:  # записываем в базу значения о производительности
                        db_perform(host, resname, restype, metric_id, desc, format,
                                   time_collect, time_start, time_end, perform)
                        inserted = True
                    except Exception as e:
                        log.error(f'Error writing PERFORMANCE to DB: {e}, params: '
                                  f'{host, resname, restype, metric_id, desc, time_collect, time_end, perform}')
                    if not inserted:
                        log.info(f'Job writing PERFORMANCE will be repeated after 3 seconds')
                        time.sleep(3)
                    else:
                        break
                db.disconnect()
        else:
            try:  # пишем ошибку в базу
                db_log_error('connection', response['error'])
            except Exception as e:
                log.error(f'Error writing LOG to DB: {e}', exc_info=True)
            finally:
                db.disconnect()

    def request_resource(self, params):
        host = params.get('host', None)
        contained = params.get('contained', None)
        req_xml_type = params.get('request_type', '')
        xml = f'{req_xml_type}.xml'
        http_params = {}

        if contained is not None:
            http_params.update({'resource': contained})

        response = self.execute_request(host, xml, http_params)

        if 'error' not in response:
            parser = XMLParser(response.text)
            # Если запрашиваем метрику то обновить xml объект
            if req_xml_type == 'listmetrics':
                self.serialized_xml.update(listmetrics=parser.get_serialized_xml()['listmetrics'])
            else:
                self.serialized_xml.update(parser.get_serialized_xml())
        else:
            return response
        # Если запрашиваемый элемент - ресурс, то запрашиваем метрики по нему
        if req_xml_type == 'contained':
            self.request_resource({'host': host, 'contained': contained, 'request_type': 'listmetrics'})

        if len(self.serialized_xml) > 0:
            return self.serialized_xml
        else:
            return response
