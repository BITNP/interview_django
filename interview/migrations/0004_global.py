# Generated by Django 5.1.1 on 2024-09-10 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interview', '0003_alter_interviewer_interview_identity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Global',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='global_config', max_length=20)),
            ],
        ),
    ]