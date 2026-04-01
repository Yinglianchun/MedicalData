# 用于操作数据库
from pymysql import *
conn = connect(host='localhost', user='root', password='123456', database='medicalinfo', port=3306,
                                   charset='utf8mb4')
cursor = conn.cursor()

def querys(sql,params,type='no_select'):  # 定义一个函数(sql语句,参数,非查询)
    parma = tuple(params)
    cursor.execute(sql,params) # 执行sql语句
    if type != 'no_select':  # 如果是查询语句
        data_list = cursor.fetchall()  # 将查询到的数据返回
        conn.commit()
        return data_list
    else:  # 如果是增删属性的语句则直接执行
        conn.commit()
        return '执行成功'


