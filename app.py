from flask import Flask,request,jsonify,session
from utils.getAllData import *

from machine.pred import (
    get_or_train_model,
    pred,
    retrain_and_get_metrics,
    get_cached_metrics,
    get_data_source_stats
)
from utils.getPublicData import *
from utils.query import querys
from flask_cors import CORS
from functools import wraps


app = Flask(__name__)
# 配置CORS，允许携带凭证（cookie/session）
# 开发时 Vue 可能是 localhost 或 127.0.0.1、不同端口；带 cookie 时必须逐项列出 origin
CORS(
    app,
    supports_credentials=True,
    origins=[
        'http://localhost:8080',
        'http://127.0.0.1:8080',
        'http://localhost:8081',
        'http://127.0.0.1:8081',
    ],
)
app.secret_key = "medicaldata-secret-key"


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"message": "未登录", "code": 401, "data": None}), 401
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"message": "未登录", "code": 401, "data": None}), 401
        if session.get("role") != "admin":
            return jsonify({"message": "无管理员权限", "code": 403, "data": None}), 403
        return func(*args, **kwargs)
    return wrapper


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空', 'code': 400, 'data': None}), 400

    exists = querys('select id from users where username=%s', [username], 'select')
    if exists:
        return jsonify({'message': '用户名已存在', 'code': 409, 'data': None}), 409

    querys(
        'insert into users (username,password,role,status,create_time) '
        'values (%s,%s,%s,1,now())',
        [username, password, 'user']
    )
    return jsonify({'message': '注册成功', 'code': 200, 'data': None})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空', 'code': 400, 'data': None}), 400

    result = querys(
        'select id,username,role,status from users where username=%s and password=%s',
        [username, password],
        'select'
    )
    if not result:
        return jsonify({'message': '用户名或密码错误', 'code': 401, 'data': None}), 401

    user_id, username_db, role, status = result[0]
    if status != 1:
        return jsonify({'message': '账号已禁用', 'code': 403, 'data': None}), 403

    session['user_id'] = user_id
    session['username'] = username_db
    session['role'] = role

    return jsonify({
        'message': '登录成功',
        'code': 200,
        'data': {
            'id': user_id,
            'username': username_db,
            'role': role
        }
    })


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': '已退出登录', 'code': 200, 'data': None})


@app.route('/me', methods=['GET'])
def get_current_user():
    if not session.get('user_id'):
        return jsonify({'message': '未登录', 'code': 401, 'data': None}), 401
    return jsonify({
        'message': 'success',
        'code': 200,
        'data': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        }
    })


@app.route('/admin/users', methods=['GET'])
@admin_required
def admin_users():
    """管理员获取用户列表，支持按用户名模糊搜索或按 ID 精确查询"""
    keyword = request.args.get('username', '').strip()
    user_id_str = request.args.get('id', '').strip()
    if user_id_str:
        rows = querys(
            'select id,username,role,status,create_time from users where id=%s order by id asc',
            [int(user_id_str)],
            'select'
        )
    elif keyword:
        rows = querys(
            'select id,username,role,status,create_time from users where username like %s order by id asc',
            [f'%{keyword}%'],
            'select'
        )
    else:
        rows = querys(
            'select id,username,role,status,create_time from users order by id asc',
            [],
            'select'
        )
    result = []
    for row in rows:
        user_id, username, role, status, create_time = row
        result.append({
            'id': user_id,
            'username': username,
            'role': role,
            'status': status,
            'create_time': str(create_time)
        })
    return jsonify({'message': 'success', 'code': 200, 'data': {'users': result}})


@app.route('/admin/user/status', methods=['POST'])
@admin_required
def admin_update_user_status():
    """管理员修改用户状态（启用/禁用）"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    status = data.get('status')
    if user_id is None or status is None:
        return jsonify({'message': 'user_id 和 status 不能为空', 'code': 400, 'data': None}), 400

    querys('update users set status=%s where id=%s', [int(status), int(user_id)])
    return jsonify({'message': '更新成功', 'code': 200, 'data': None})


@app.route('/admin/user', methods=['POST'])
@admin_required
def admin_create_user():
    """管理员新增用户"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user')
    status = data.get('status', 1)

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空', 'code': 400, 'data': None}), 400
    if role not in ('admin', 'user'):
        return jsonify({'message': '角色值不合法', 'code': 400, 'data': None}), 400

    exists = querys('select id from users where username=%s', [username], 'select')
    if exists:
        return jsonify({'message': '用户名已存在', 'code': 409, 'data': None}), 409

    querys(
        'insert into users (username,password,role,status,create_time) values (%s,%s,%s,%s,now())',
        [username, password, role, int(status)]
    )
    return jsonify({'message': '创建成功', 'code': 200, 'data': None})


@app.route('/admin/user/<int:user_id>', methods=['PUT'])
@admin_required
def admin_update_user(user_id):
    """管理员修改用户信息（用户名/角色/密码）"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    role = data.get('role')
    password = data.get('password', '').strip()
    status = data.get('status')

    if not username:
        return jsonify({'message': '用户名不能为空', 'code': 400, 'data': None}), 400
    if role not in ('admin', 'user'):
        return jsonify({'message': '角色值不合法', 'code': 400, 'data': None}), 400

    # 检查用户名是否被其他人占用
    dup = querys('select id from users where username=%s and id!=%s', [username, user_id], 'select')
    if dup:
        return jsonify({'message': '用户名已被占用', 'code': 409, 'data': None}), 409

    if password:
        querys(
            'update users set username=%s, role=%s, status=%s, password=%s where id=%s',
            [username, role, int(status), password, user_id]
        )
    else:
        querys(
            'update users set username=%s, role=%s, status=%s where id=%s',
            [username, role, int(status), user_id]
        )
    return jsonify({'message': '修改成功', 'code': 200, 'data': None})


@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """管理员删除用户"""
    if user_id == session.get('user_id'):
        return jsonify({'message': '不能删除当前登录账号', 'code': 400, 'data': None}), 400

    exists = querys('select id from users where id=%s', [user_id], 'select')
    if not exists:
        return jsonify({'message': '用户不存在', 'code': 404, 'data': None}), 404

    querys('delete from users where id=%s', [user_id])
    return jsonify({'message': '删除成功', 'code': 200, 'data': None})


@app.route('/admin/cases', methods=['GET'])
@admin_required
def admin_list_cases():
    """管理员查看病例数据（分页 + 按ID查询）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
    except ValueError:
        page = 1
        size = 10
    if page < 1:
        page = 1
    if size <= 0 or size > 50:
        size = 10
    offset = (page - 1) * size

    case_id_raw = (request.args.get('case_id') or '').strip()
    where_sql = ''
    where_params = []
    if case_id_raw:
        try:
            case_id = int(case_id_raw)
            where_sql = ' where id=%s'
            where_params.append(case_id)
        except ValueError:
            return jsonify({'message': 'case_id 必须是整数', 'code': 400, 'data': None}), 400

    count_rows = querys(
        'select count(*) from cases' + where_sql,
        where_params,
        'select'
    )
    total = int(count_rows[0][0]) if count_rows else 0

    list_sql = (
        'select id,type,gender,age,time,content,docName,docHospital,department,detailUrl,'
        'height,weight,illDuration,allergy from cases' + where_sql +
        ' order by id asc limit %s offset %s'
    )
    cases = querys(list_sql, where_params + [size, offset], 'select')
    result = []
    for row in cases:
        (cid, ctype, gender, age, time, content, docName, docHospital,
         department, detailUrl, height, weight, illDuration, allergy) = row
        result.append({
            'id': cid,
            'type': ctype,
            'gender': gender,
            'age': age,
            'time': time,
            'content': content,
            'docName': docName,
            'docHospital': docHospital,
            'department': department,
            'detailUrl': detailUrl,
            'height': height,
            'weight': weight,
            'illDuration': illDuration,
            'allergy': allergy
        })
    return jsonify({
        'message': 'success',
        'code': 200,
        'data': {
            'cases': result,
            'page': page,
            'size': size,
            'total': total
        }
    })


@app.route('/admin/case', methods=['POST'])
@admin_required
def admin_create_case():
    """管理员新增病例，可选关联 user_id"""
    data = request.get_json() or {}
    fields = ['type', 'gender', 'age', 'time', 'content',
              'docName', 'docHospital', 'department', 'detailUrl',
              'height', 'weight', 'illDuration', 'allergy']
    values = [data.get(f) for f in fields]

    if not data.get('type') or not data.get('gender'):
        return jsonify({'message': '类型和性别不能为空', 'code': 400, 'data': None}), 400

    user_id = data.get('user_id')
    if user_id:
        # 管理员选择了关联某个用户
        querys(
            'insert into cases (type,gender,age,time,content,docName,docHospital,department,detailUrl,'
            'height,weight,illDuration,allergy,user_id) '
            'values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            values + [user_id]
        )
    else:
        # 仍然是公共病例
        querys(
            'insert into cases (type,gender,age,time,content,docName,docHospital,department,detailUrl,'
            'height,weight,illDuration,allergy) '
            'values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            values
        )

    return jsonify({'message': '新增成功', 'code': 200, 'data': None})



@app.route('/admin/case/<int:case_id>', methods=['PUT'])
@admin_required
def admin_update_case(case_id):
    """管理员更新病例"""
    data = request.get_json() or {}
    fields = ['type', 'gender', 'age', 'time', 'content',
              'docName', 'docHospital', 'department', 'detailUrl',
              'height', 'weight', 'illDuration', 'allergy']
    set_parts = []
    params = []
    for f in fields:
        if f in data:
            set_parts.append(f"{f}=%s")
            params.append(data[f])
    if not set_parts:
        return jsonify({'message': '没有需要更新的字段', 'code': 400, 'data': None}), 400
    params.append(case_id)
    sql = f"update cases set {', '.join(set_parts)} where id=%s"
    querys(sql, params)
    return jsonify({'message': '更新成功', 'code': 200, 'data': None})


@app.route('/admin/case/<int:case_id>', methods=['DELETE'])
@admin_required
def admin_delete_case(case_id):
    """管理员删除病例"""
    querys('delete from cases where id=%s', [case_id])
    return jsonify({'message': '删除成功', 'code': 200, 'data': None})
@app.route('/getHomeData',methods=['GET','POST']) # 创建接口
@admin_required  # 管理员权限限制
def getHomeData():

    try:
        pieData = getPieData()
        configOne,wordData = getConfigOne()
        casesData = list(getAllCasesData())
        maxNum,maxType,maxDep,maxHos,maxAge,minAge = getFoundData()
        boyList,girlList,ratioData = getGenderData()
        dataResult = getCircleData()
        xData,y1Data,y2Data = getBodyData()
        # print(casesData)
        # print('======', pieData)


        return jsonify({
            'message': 'success',
            'code': 200,
            'data': {  # 将数据以json 形式返回到前端
                'pieData': pieData,
                'ConfigOne': configOne,
                'casesData': casesData,
                'maxNum': maxNum,
                'maxType': maxType,
                'maxDep': maxDep,
                'maxHos': maxHos,
                'maxAge': maxAge,
                'minAge': minAge,
                'boyList': boyList,
                'girlList': girlList,
                'ratioData': ratioData,
                'circleData': dataResult,
                'wordData': wordData,
                'lastData':{
                    'xData':xData,
                    'y1Data':y1Data,
                    'y2Data':y2Data
                }
            }
        })
    except Exception as e:
        # 处理异常，返回错误信息
        return jsonify({
            'message': str(e),
            'code': 500,
            'data': None
        }), 500
        
        
@app.route('/myCases', methods=['GET'])
@login_required
def my_cases():
    """当前登录用户的就诊病例记录（cases 表中 user_id=当前用户）"""
    user_id = session.get('user_id')
    try:
        # 读取 cases 表字段，避免字段缺失导致 500
        columns_raw = querys('show columns from cases', [], 'select')
        column_names = {str(col[0]) for col in columns_raw}

        # user_id 不存在时无法做“个人病例”过滤，直接返回空列表
        if 'user_id' not in column_names:
            return jsonify({
                'message': 'success',
                'code': 200,
                'data': {'cases': []}
            })

        has_create_time = 'create_time' in column_names
        order_field = 'create_time desc' if has_create_time else 'id desc'
        time_expr = 'create_time' if has_create_time else 'time'

        rows = querys(
            'select id,type,gender,age,time,content,docName,docHospital,department,detailUrl,'
            'height,weight,illDuration,allergy,' + time_expr + ' as create_time '
            'from cases where user_id=%s order by ' + order_field,
            [user_id],
            'select'
        )

        cases = []
        for row in rows:
            (cid, ctype, gender, age, time, content, docName, docHospital,
             department, detailUrl, height, weight, illDuration, allergy, create_time) = row
            cases.append({
                'id': cid,
                'type': ctype,
                'gender': gender,
                'age': age,
                'time': time,
                'content': content,
                'docName': docName,
                'docHospital': docHospital,
                'department': department,
                'detailUrl': detailUrl,
                'height': height,
                'weight': weight,
                'illDuration': illDuration,
                'allergy': allergy,
                'create_time': str(create_time) if create_time else ''
            })

        return jsonify({'message': 'success', 'code': 200, 'data': {'cases': cases}})
    except Exception as e:
        return jsonify({'message': f'加载病例失败: {e}', 'code': 500, 'data': None}), 500


# @app.route('/submitModel', methods=['POST'])
# def submitModel():
#     if request.method == 'POST':
#         content = request.json['content']
#         print("Received content from front end:", content)  # 打印前端发送的内容
#         model = model_train(getData())
#         result = pred(model, content)
#         print("Predicted result:", result)  # 打印预测结果
#         return jsonify({
#             'message': 'success',
#             'code': 200,
#             'data': {
#                 'resultData': result
#             }
#         })
@app.route('/submitModel', methods=['POST'])
def submitModel():
    def to_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        return default

    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        content = payload.get('content', '')
        real_only = to_bool(payload.get('real_only'), False)
        model = get_or_train_model(real_only=real_only)
        result = pred(model, content)

        # 如果当前有登录用户，则把预测记录写入 pred_records
        user_id = session.get('user_id')
        if user_id:
            try:
                querys(
                    'insert into pred_records (user_id,input_content,pred_result,create_time) '
                    'values (%s,%s,%s,now())',
                    [user_id, content, result]
                )
            except Exception as e:
                print("save pred_records error:", e)

        return jsonify({
            'message': 'success',
            'code': 200,
            'data': {
                'resultData': result,
                'modelMode': 'real_only' if real_only else 'real_plus_synthetic'
            }
        })


@app.route('/admin/model/retrain', methods=['POST'])
@admin_required
def admin_retrain_model():
    """管理员手动重训模型，可选返回 A/B 对比指标。"""
    def to_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
        return default

    try:
        payload = request.get_json(silent=True) or {}
        real_only = to_bool(payload.get('real_only'), False)
        compare = to_bool(payload.get('compare'), False)
        metrics_result = retrain_and_get_metrics(real_only=real_only, compare=compare)
        return jsonify({
            'message': '模型重训完成',
            'code': 200,
            'data': metrics_result
        })
    except Exception as e:
        return jsonify({'message': f'模型重训失败: {e}', 'code': 500, 'data': None}), 500


@app.route('/admin/model/metrics', methods=['GET'])
@admin_required
def admin_model_metrics():
    """查看当前缓存模型的指标（若还未训练则先训练一次）。"""
    try:
        # 若当前没有缓存模型，这里会先触发一次默认训练
        get_or_train_model(force_retrain=False, real_only=False)
        return jsonify({'message': 'success', 'code': 200, 'data': get_cached_metrics()})
    except Exception as e:
        return jsonify({'message': f'获取模型指标失败: {e}', 'code': 500, 'data': None}), 500


@app.route('/admin/model/data-stats', methods=['GET'])
@admin_required
def admin_model_data_stats():
    """查看病例来源统计（真实/合成），用于验证对比实验是否有效。"""
    try:
        stats = get_data_source_stats(real_id_max=405)
        return jsonify({'message': 'success', 'code': 200, 'data': stats})
    except Exception as e:
        return jsonify({'message': f'获取数据来源统计失败: {e}', 'code': 500, 'data': None}), 500



@app.route('/tableData', methods=['GET', 'POST'])
def tableData():
    tableDataList = getAllCasesData()
    resultData = [x[1:] for x in tableDataList]
    print(resultData)
    return jsonify({
        'message': 'success',
        'code': 200,
        'data': {
            'resultData': resultData[:50]
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
