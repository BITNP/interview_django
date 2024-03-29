# Generated by Django 4.2.5 on 2023-09-16 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interview', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interviewee',
            name='interview_status',
            field=models.IntegerField(choices=[(1, '未签到'), (2, '已签到候场'), (3, '已分配教室准备出发'), (4, '面试开始'), (5, '面试结束'), (6, '第一志愿队列'), (7, '第二志愿队列'), (8, '最终队列'), (9, '已录取')]),
        ),
        migrations.AlterField(
            model_name='interviewer',
            name='interview_identity',
            field=models.IntegerField(choices=[(1, '候场教室'), (2, '面试教室'), (3, '围观')]),
        ),
    ]
