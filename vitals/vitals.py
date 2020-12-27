import time
import json
import requests
import psutil
import socket
import logging

API_KEY = 'OEL_KEY'
SERVER_URL = 'https://api.connexion.me/api/metrics/%s' % API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cpu_percent():
    return psutil.cpu_percent(1)


def get_memory_used_percent():

    mem = psutil.virtual_memory()
    total = mem.total
    used = mem.used

    return used / total


def get_disk_usage_percent():

    partitions = []
    for p in psutil.disk_partitions():
        usage = psutil.disk_usage(p.mountpoint)
        total = usage.total
        used = usage.used

        partitions.append({'partition': p.mountpoint, 'disk': used / total})

    return partitions


def send_vitals():
    host_name = socket.gethostname()

    cpu_percent = get_cpu_percent()
    mem_used_percent = get_memory_used_percent()
    disk_usage = get_disk_usage_percent()

    payload_cpu = {
        'metrics': {'cpu': cpu_percent},
        'tags': {'identifier': host_name, 'category': 'cpu_percent'}
    }
    res = requests.post(
        SERVER_URL,
        data=json.dumps(payload_cpu)
    )
    logging.info('cpu result: %s' % res.status_code)

    payload_mem = {
        'metrics': {'mem': mem_used_percent},
        'tags': {'identifier': host_name, 'category': 'memory_percent'}
    }
    requests.post(
        SERVER_URL,
        data=json.dumps(payload_mem)
    )
    logging.info('mem result: %s' % res.status_code)

    for p in disk_usage:
        payload_disk = {
            'metrics': {'disk': p['disk']},
            'tags': {
                'identifier': host_name,
                'category': 'disk_percent',
                'partition': p['partition']
            }
        }
        requests.post(
            SERVER_URL,
            data=json.dumps(payload_disk)
        )
        logging.info('disk (%s) result: %s' % (
            p['disk'],
            res.status_code
        ))


if __name__ == '__main__':

    send_vitals()
