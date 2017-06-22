# Create your tasks here
from __future__ import absolute_import, unicode_literals
from aquila_v2.celery import app
from scripts import Inception
from scripts import functions
from scripts import MyThreadPool
from model_model import models
import time

from model_model import models


@app.task()
def addx(x, y):
    ret = a(x, y)
    return ret


def a(x, y):
    time.sleep(5)
    print('sleep 5')
    return x * y


@app.task()
def mul(x, y):
    return x * y


@app.task()
def xsum(numbers):
    return sum(numbers)


@app.task()
def work_run_task(host, user, passwd, port, sql_content, wid):
    result_dict = {'data': {}}

    ince = Inception.Inception(db_host=host, db_user=user, db_passwd=passwd, db_port=port, sql_content=sql_content)
    run_result = ince.run_sql(1)
    result = functions.result_tran(run_result, result_dict)
    run_error_id = 1
    for items in result['data']:
        if result['data'][items]['status'] == '执行失败' or \
                        result['data'][items]['status'] == 'Error':
            run_error_id = 0
        elif result['data'][items]['status'] == '执行成功,备份失败':
            run_error_id = 5
        models.InceptionAuditDetail.objects.create(
            work_order_id=wid,
            sql_sid=items,
            flag=3,
            status=result['data'][items]['status'],
            error_msg=result['data'][items]['error_msg'],
            sql_content=result['data'][items]['sql'],
            aff_row=result['data'][items]['rows'],
            rollback_id=result['data'][items]['rollback_id'],
            backup_dbname=result['data'][items]['backup_dbname'],
            execute_time=int(float(result['data'][items]['execute_time']) * 1000),
            sql_hash=result['data'][items]['sql_hash']
        )

    models.InceptionWorkOrderInfo.objects.filter(work_order_id=wid).update(work_status=run_error_id)
    models.WorkOrderTask.objects.filter(work_order_id=wid).update(work_status=run_error_id)


def get_matedata(account_info):
    for item in account_info:
        host = item['host__host_ip']
        app_user = item['app_user']
        app_port = item['app_port']
        app_pass = item['app_pass']

        os_user = item['host__host_user']
        os_pass = item['host__host_pass']
        os_port = item['host__host_port']

        conn_info = GetMetadataitem(host=host, user=app_user, port=app_port, passwd=app_pass)
        conn_info.get_columns()


class GetMetadataitem(object):
    def __init__(self, host, user, port, passwd):
        self.host = host
        self.user = user
        self.port = int(port)
        self.passwd = passwd
        self.cur = ''
        db = functions.DBAPI(host=self.host, user=self.user, password=self.passwd, port=self.port)
        if db.error:
            models.GetMetaDataError.objects.create(host=self.host, error_msg=db.error)
        else:
            self.cur = db

    def get_tables(self):
        sql = """SELECT table_schema, table_name, engine, row_format, table_rows, avg_row_length,
                   data_length, max_data_length, index_length, data_free, auto_increment,
                   table_collation, table_comment, create_time, update_time, check_time
            FROM information_schema.tables
            where table_schema not in ('sys', 'test', 'information_schema', 'performance_schema', 'mysql')"""
        if self.cur:
            result = self.cur.conn_query(sql)
            for item in result:
                try:
                    c_time = u_time = check_time = None
                    if item[13]:
                        c_time = time.strftime(item[13].strftime('%Y-%m-%d %H:%M:%S'))
                    if item[14]:
                        u_time = time.strftime(item[14].strftime('%Y-%m-%d %H:%M:%S'))
                    if item[15]:
                        check_time = time.strftime(item[15].strftime('%Y-%m-%d %H:%M:%S'))

                    models.MetaDataTables.objects.create(
                        host_ip=self.host,
                        table_schema=item[0],
                        table_name=item[1],
                        engine=item[2],
                        row_format=item[3],
                        table_rows=item[4],
                        avg_row_length=item[5],
                        max_data_length=item[7],
                        data_length=item[6],
                        index_length=item[8],
                        data_free=item[9],
                        auto_increment=item[10],
                        table_collation=item[11],
                        create_time=c_time,
                        update_time=u_time,
                        check_time=check_time,
                        table_comment=item[12],
                        chip_size=0
                    )
                except Exception as e:
                    print(e)
        else:
            print(11111)

    def get_indexs(self):
        sql = """
        select
            table_schema,
            table_name,
            column_name,
            non_unique,
            index_name,
            seq_in_index,
            cardinality,
            nullable,
            index_type,
            index_comment
        from information_schema.statistics
        where table_schema not in ('sys', 'test', 'information_schema', 'performance_schema', 'mysql') """
        if self.cur:
            result = self.cur.conn_query(sql)
            for item in result:
                try:
                    models.MetaDataIndexs.objects.create(
                        host_ip=self.host,
                        table_schema=item[0],
                        table_name=item[1],
                        column_name=item[2],
                        non_unique=item[3],
                        index_name=item[4],
                        seq_in_index=item[5],
                        cardinality=item[6] if item[6] else 0,
                        nullable=item[7],
                        index_type=item[8],
                        index_comment=item[9]
                    )
                except Exception as e:
                    print(e)

        else:
            print(11111)

    def get_columns(self):
        sql = """
          SELECT
            table_schema,
            table_name,
            column_name,
            column_type,
            collation_name,
            is_nullable,
            column_key,
            column_default,
            extra,
            PRIVILEGES,
            column_comment
        FROM information_schema.columns
        where table_schema not in ('sys', 'test', 'information_schema', 'performance_schema', 'mysql')
        """
        if self.cur:
            result = self.cur.conn_query(sql)
            for item in result:
                try:
                    models.MetaDataColumns.objects.create(
                        host_ip=self.host,
                        table_schema=item[0],
                        table_name=item[1],
                        column_name=item[2],
                        column_type=item[3],
                        collation_name=item[4] if item[4] else '---',
                        is_nullable=item[5],
                        column_key=item[6] if item[6] else '---',
                        column_default=item[7] if item[7] else '---',
                        extra=item[8] if item[8] else '---',
                        PRIVILEGES=item[9],
                        column_comment=item[10] if item[10] else '---'
                    )
                except Exception as e:
                    print(e)
        else:
            print(11111)

    def get_rocedure(self):
        sql = """
        select
            routine_schema,
            routine_name,
            routine_type,
            routine_definition,
            created,
            last_altered
        from information_schema.routines
        where routine_schema not in ('sys', 'test', 'information_schema', 'performance_schema')
        """
        if self.cur:
            result = self.cur.conn_query(sql)
            print(result)
        else:
            print(11111)

