# 网协面试系统
[![Dockerhub image](https://img.shields.io/badge/dockerhub-image-important.svg?logo=Docker)](https://hub.docker.com/r/agpeng/bitnp-interview)
## 一些链接

部署位置：https://interview.bitnp.net/

面试模块：https://interview.bitnp.net/interview/

录取模块：https://interview.bitnp.net/admission/

候场教室公开看板（可以投屏大屏幕）：https://interview.bitnp.net/interview/public

管理员后台：https://interview.bitnp.net/admin/

## 面试流程

1. 初始状态下所有面试者的状态为未签到
2. 面试者到达候场教室后，候场教室的面试官为面试者签到，签到后状态从“未签到”变更为“已签到候场”，此时面试教室的面试官可以看到这位同学出现在界面
3. 某个面试教室在空闲时为时间安排靠前的面试者点击拉来面试，此时状态从“已签到候场”变更为“已分配教室准备出发”，此时候场教室的面试官可以看到这位同学的状态，并且在“面试教室”列可以看到其面试教室，候场教室的面试官需要通知面试者去对应的教室
4. 面试者到达对应的教室后，面试教室的面试官点击“开始面试”，此时状态从“已分配教室准备出发”变更为“面试开始”，此时这位同学从候场教室界面消失。
5. 面试教室的面试官可以在面试过程中在面试界面填写评论，面试结束并填写完所有评论后，面试官点击结束面试，状态变成“面试结束”。

## 录取流程

建议每个部门都选出一个人在系统操作本部门的录取，以防止数据混乱。录取时部门内和各个部门间请充分沟通。

首先，管理员将所有面试结束的人员放入第一录取队列。根据面试官的面试身份（INTERVIEWER，修改请联系管理员），各部门的面试官在“部门待录取队列”可以看到本部门待录取的同学。界面中可以看到是第一志愿队列还是第二志愿队列以及是否接受调剂，点击查看可以看到之前填写的评论，讨论后请决定录取还是拒绝。如果录取，则进入本部门，可以在系统内查看或导出，如果拒绝，则根据是否接受调剂和志愿填写情况进入第二志愿或捡漏队列（捡漏队列中是不接受调剂的或者所有志愿都不录取的，其他部分可以看看要不要）。

## 部署文档

### 第一次启动

```shell
docker compose up -d
```
具体配置见`docker-compose.yml`，数据库位置在`data/db.sqlite3`。全新开始时，数据库会自动建立，若要删除原有数据重新开始，需要备份原有的数据库，并将其改名，此后启动应用，会自动建立数据库。

应用启动后，需要管理员进入容器内，创建管理员用户（下文中使用`python manage.py`命令都在容器内进行）。
```shell
docker exec -it <容器名或容器id> bash
python manage.py createsuperuser
```
此处需要注意用户名和邮箱需要和网协通行证中的用户名邮箱一致，密码随便填，系统不使用这个密码。

### 加载数据

加载数据使用django的fixtures功能，示例数据见仓库中路径`interview/fixtures/init_data.json`。

```shell
python manage.py loaddata <fixtures文件路径>
```

### 面试官身份

位置：https://interview.bitnp.net/admin/auth/user/

只有当登录系统的用户有关联的身份时，用户才能进入系统，因此需要管理员赋予正确的身份。

方法：点击要修改的用户，翻到最下面，在INTERVIEWER节里，填写正确的Interview identity，Department和Room。

身份为观察者的用户可以看所有数据，但是不能操作，给希望围观的网协成员的身份。

### 开始录取

位置：https://interview.bitnp.net/admission/admission_start

所有面试结束后，面试过的用户状态为面试结束，要开始录取，需要管理员在此处操作，此页面会显示所有面试完成的人员，确认无误后，点击submit，系统将这些人全部放入第一录取队列。

### 修正数据

如果面试官误操作，管理员可以在后台修改面试者信息，注意保持数据一致性（主要是面试状态）。
