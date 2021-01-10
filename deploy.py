"""
deploy.py

Usage:
    deploy.py --type=<type>

Example:
    trainer.py --type=general
    trainer.py --type=dev
"""

from tools import zip
from docopt import docopt
import paramiko
import boto3
import time
import os

BUILD_DIRS = [
    'api',
    'tasks',
    'oel',
    'tools',
    'manage.py',
    'requirements.txt',

]
ZIP_FILENAME = 'oel.zip'


def create_zip():
    if ZIP_FILENAME in os.listdir('.'):
        print('Deleting %s ' % ZIP_FILENAME)
        os.remove(ZIP_FILENAME)

    print('Packaging Files')
    utilities = zip.ZipUtilities()
    utilities.to_zip(BUILD_DIRS, ZIP_FILENAME)


def create_ssh_connection(public_ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        public_ip,
        username='ubuntu',
        key_filename='/home/dplouffe/.ssh/dom-ec2-2020.pem'
    )

    return ssh


def copy_code(ssh):
    print('Copying Code')
    res = ssh.exec_command('unzip %s' % ZIP_FILENAME)
    print('****')
    print(res)
    print('****')
    ssh.exec_command('sudo rm -r /opt/oel/*')

    ssh.exec_command('sudo cp -r oel /opt/oel')
    ssh.exec_command('sudo cp -r api /opt/oel')
    ssh.exec_command('sudo cp -r tasks /opt/oel')
    ssh.exec_command('sudo cp -r tools /opt/oel')
    ssh.exec_command('sudo cp manage.py /opt/oel')
    ssh.exec_command('sudo cp requirements.txt /opt/oel')
    # ssh.exec_command('PYTHONPATH=/opt/oel python3 /opt/oel/manage.py migrate')
    ssh.exec_command('sudo systemctl restart oel')
    ssh.exec_command('sudo systemctl restart oelsup')


def put_file(ssh):
    print('Uploading Zip File')
    ssh.exec_command('sudo rm -r oel')
    ssh.exec_command('sudo rm -r api')
    ssh.exec_command('sudo rm -r tasks')
    ssh.exec_command('sudo rm manage.py')
    ssh.exec_command('sudo rm requirements.txt')
    ssh.exec_command('sudo rm %s' % ZIP_FILENAME)

    sftp = ssh.open_sftp()
    sftp.put(ZIP_FILENAME, ZIP_FILENAME)


def deploy(deploy_type):
    create_zip()

    ec2 = boto3.client('ec2', region_name='us-east-1')
    response = ec2.describe_instances()
    for r in response['Reservations']:
        for i in r['Instances']:
            deploy_to_instance = False
            for t in i['Tags']:
                if t['Key'].upper() == 'TYPE' and t[
                        'Value'].lower() == deploy_type.lower():
                    deploy_to_instance = True
                    break

            if deploy_to_instance:
                print(i.keys())
                print(i['PublicDnsName'])
                ipaddress = i.get('PublicIpAddress', None)
                print('Deploying to %s' % ipaddress)
                ssh = create_ssh_connection(ipaddress)
                put_file(ssh)
                time.sleep(5.0)
                copy_code(ssh)


if __name__ == '__main__':
    args = docopt(__doc__)

    deploy_type = args['--type']

    deploy(deploy_type)
