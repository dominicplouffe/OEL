# Generated by Django 3.1.1 on 2020-10-09 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0012_periodictask_expire_seconds'),
        ('api', '0012_remove_ping_callback_num_calls'),
    ]

    operations = [
        migrations.AddField(
            model_name='ping',
            name='task',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.periodictask'),
        ),
    ]
