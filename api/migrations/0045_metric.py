# Generated by Django 3.1.3 on 2020-12-26 17:38

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0044_auto_20201226_1719'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metrics', models.JSONField()),
                ('tags', models.JSONField()),
                ('created_on', models.DateTimeField(default=datetime.datetime.now)),
                ('org', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.org')),
            ],
        ),
    ]
