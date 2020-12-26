import time
import psutil
import socket


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


if __name__ == '__main__':

    host_name = socket.gethostname()

    cpu_percent = get_cpu_percent()
    print(cpu_percent)

    mem_used_percent = get_memory_used_percent()
    print(mem_used_percent)

    disk_usage = get_disk_usage_percent()
    print(disk_usage)

    payload_cpu = {
        'metrics': {'cpu': cpu_percent},
        'tags': {'identifier': host_name, 'category': 'cpu_percent'}
    }
    print(payload_cpu)

    payload_mem = {
        'metrics': {'mem': mem_used_percent},
        'tags': {'identifier': host_name, 'category': 'memory_percent'}
    }
    print(payload_mem)

    for p in disk_usage:
        payload_disk = {
            'metrics': {'disk': p['disk']},
            'tags': {'identifier': host_name, 'category': 'disk_percent', 'partition': p['partition']}
        }
        print(payload_disk)
