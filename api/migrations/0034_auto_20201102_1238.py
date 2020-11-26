# Generated by Django 3.1.1 on 2020-11-02 12:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_auto_20201101_2343'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orguser',
            name='oncall_order',
        ),
        migrations.AddField(
            model_name='failure',
            name='notify_org_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.orguser'),
        ),
    ]
