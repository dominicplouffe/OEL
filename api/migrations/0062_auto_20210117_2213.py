# Generated by Django 3.1.3 on 2021-01-17 22:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0012_periodictask_expire_seconds'),
        ('api', '0061_auto_20210117_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='pong',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.periodictask'),
        ),
        migrations.AlterField(
            model_name='failure',
            name='reason',
            field=models.CharField(blank=True, choices=[('invalid_value', 'Invalid Value'), ('key_error', 'Key Error'), ('value_error', 'Value Error'), ('status_code', 'Status Code'), ('connection_error', 'Connection Error'), ('timeout_error', 'Timeout Error'), ('http_error', 'HTTP Error'), ('receive_alert', 'Receive Alert'), ('Metric triggered', 'Metric Triggered'), ('start_not_triggered', 'Heartbeat Start'), ('comp_not_triggered', 'Heartbeat Complete')], max_length=20, null=True),
        ),
    ]
