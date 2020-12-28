#!/bin/sh
mkdir /opt/onerrorlog
curl https://onerrorlog.s3.amazonaws.com/vitals.py -o /opt/onerrorlog/vitals.py
pip3 install psutil
rm /etc/cron.d/onerrorlog
echo "*/1 * * * * root python3 /opt/onerrorlog/vitals.py >> /var/log/onerrorlog.log 2>&1" >> /etc/cron.d/onerrorlog
sed -i "s/OEL_KEY/$1/" /opt/onerrorlog/vitals.py