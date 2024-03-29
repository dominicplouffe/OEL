# Generated by Django 3.1.3 on 2020-12-27 12:53

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0045_metric'),
    ]

    operations = [
        migrations.CreateModel(
            name='VitalInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instance_id', models.CharField(blank=True, max_length=256, null=True)),
                ('name', models.CharField(blank=True, max_length=256, null=True)),
                ('active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(default=datetime.datetime.now)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('org', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.org')),
            ],
        ),
    ]
