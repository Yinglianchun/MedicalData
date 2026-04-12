import os
import json
import codecs

import requests
from flask import Flask,request,jsonify,session,Response,stream_with_context
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


def _load_local_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return

    with open(env_path, 'r', encoding='utf-8') as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


_load_local_env()

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


def _trim_text(value, max_len=4000):
    if value is None:
        return ''
    return str(value).strip()[:max_len]


def _resolve_qwen_api_url():
    api_url = (
        os.getenv('QWEN_API_URL')
        or os.getenv('OPENAI_API_URL')
        or os.getenv('OPENAI_BASE_URL')
        or os.getenv('NEWAPI_BASE_URL')
        or ''
    ).strip()

    if not api_url:
        raise ValueError('未配置 AI 接口地址，请在 .env 中设置 QWEN_API_URL 或 OPENAI_API_URL')

    if api_url.endswith('/v1'):
        return f'{api_url}/chat/completions'
    if api_url.endswith('/v1/'):
        return f'{api_url}chat/completions'
    return api_url


class AIRequestValidationError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _extract_text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get('text') or item.get('content')
                if text:
                    parts.append(str(text))
        return ''.join(parts)
    return ''


def _get_qwen_api_config():
    api_key = (
        os.getenv('DASHSCOPE_API_KEY')
        or os.getenv('QWEN_API_KEY')
        or os.getenv('OPENAI_API_KEY')
        or os.getenv('NEWAPI_API_KEY')
    )
    if not api_key:
        raise ValueError('未配置 AI API Key，请在后端环境变量中设置 DASHSCOPE_API_KEY、QWEN_API_KEY 或 OPENAI_API_KEY')

    model = os.getenv('QWEN_MODEL', 'qwen3.5-plus')
    api_url = _resolve_qwen_api_url()
    timeout = int(os.getenv('AI_HTTP_TIMEOUT', '90'))
    return api_key, model, api_url, timeout


def _build_ai_prompts(payload):
    task = _trim_text(payload.get('task'), 40)
    symptom_text = _trim_text(payload.get('symptom_text'))
    prediction_result = _trim_text(payload.get('prediction_result'), 1000)
    case_text = _trim_text(payload.get('case_text'))
    case_meta = payload.get('case_meta') if isinstance(payload.get('case_meta'), dict) else {}
    chart_title = _trim_text(payload.get('chart_title'), 100)
    chart_type = _trim_text(payload.get('chart_type'), 100)
    chart_data = payload.get('chart_data') if isinstance(payload.get('chart_data'), list) else []

    if task not in ('explain_prediction', 'summarize_case', 'analyze_chart'):
        raise AIRequestValidationError('不支持的 AI 任务类型')

    if task == 'explain_prediction':
        if not prediction_result:
            raise AIRequestValidationError('缺少预测结果，无法解释')

        system_prompt = (
            '你是医疗数据分析系统中的 AI 助手。'
            '你的职责是解释系统预测结果，帮助用户理解，不得把自己表述为医生。'
            '当前模型只支持有限病种分类，跨系统症状、开放场景症状或超出训练分布的输入，可能导致预测偏差。'
            '你必须先结合用户原始症状描述，判断症状与预测结果是否一致。'
            '如果症状与预测结果存在明显跨系统冲突，或预测结果看起来不够合理，必须明确提醒“该结果可能失真，仅供参考”，不能顺着预测结果做肯定式展开。'
            '不要给出明确诊断结论，不要开药，不要夸大确定性。'
            '请补充1到2个建议优先咨询的就诊科室或挂号方向，但必须写明这只是参考建议。'
            '回答要简洁、自然，控制在4点以内，并明确提醒“仅供参考，需结合医生诊断”。'
            '只能输出纯文本，不要使用 Markdown，不要使用标题、星号、减号、反引号、代码块、表格。'
            '如需分点，请使用“1. 2. 3. 4.”这种普通文本编号。'
        )
        user_prompt = (
            f'用户输入的症状描述：{symptom_text or "未提供"}\n'
            f'系统预测结果：{prediction_result}\n'
            '请先判断“症状描述”和“预测结果”是否基本一致。'
            '若不一致，请先指出模型可能因病种范围有限或跨系统症状而出现偏差。'
            '请输出：1. 症状与预测结果是否一致；2. 这个结果最多可能提示什么；3. 为什么结果只能作为参考；'
            '4. 建议优先咨询的就诊科室或挂号方向，以及用户下一步可关注的症状或检查方向。'
        )
        return task, system_prompt, user_prompt

    if task == 'summarize_case':
        if not case_text:
            raise AIRequestValidationError('缺少病例文本，无法总结')

        meta_parts = []
        for label, key in (
            ('编号', 'id'),
            ('疾病类型', 'type'),
            ('性别', 'gender'),
            ('年龄', 'age'),
            ('患病时长', 'illDuration'),
            ('医院', 'docHospital'),
            ('科室', 'department'),
        ):
            value = _trim_text(case_meta.get(key), 200)
            if value:
                meta_parts.append(f'{label}：{value}')

        system_prompt = (
            '你是医疗数据分析系统中的 AI 助手。'
            '你的职责是总结病例文本，方便用户快速阅读。'
            '不要虚构原文没有的信息，不要输出诊断建议。'
            '请用简洁中文输出，分成“症状概述”“关键信息”“建议挂号方向”“就诊建议”四部分，'
            '其中“建议挂号方向”只能写参考性的就诊科室建议，“就诊建议”只能写通用性的下一步关注点，不能代替医生意见。'
            '只能输出纯文本，不要使用 Markdown，不要使用标题符号、星号、减号、反引号、代码块、表格。'
            '如需分点，请使用“1. 2. 3. 4.”这种普通文本编号。'
        )
        user_prompt = (
            f'病例基础信息：{"；".join(meta_parts) if meta_parts else "无"}\n'
            f'病例文本：{case_text}\n'
            '请基于以上内容生成简明总结。'
        )
        return task, system_prompt, user_prompt

    if not chart_title or not chart_data:
        raise AIRequestValidationError('缺少图表标题或图表数据，无法分析')

    system_prompt = (
        '你是医疗数据可视化分析系统中的 AI 助手。'
        '你的职责是解读图表数据，帮助用户快速理解分布、集中趋势和关注重点。'
        '不要把图表解读成医学诊断，不要虚构图表中不存在的信息。'
        '如果图表与医院科室相关但未提供明确的空闲率指标，请使用“活跃度”“分布”“热度”表述，'
        '不要直接下结论为“空闲程度”。'
        '输出控制在3点以内，每点简洁自然。'
        '只能输出纯文本，不要使用 Markdown，不要使用标题、星号、减号、反引号、代码块、表格。'
        '如需分点，请使用“1. 2. 3.”这种普通文本编号。'
    )
    user_prompt = (
        f'图表标题：{chart_title}\n'
        f'图表类型：{chart_type or "统计图表"}\n'
        f'图表数据：{json.dumps(chart_data, ensure_ascii=False)}\n'
        '请输出：1. 图表主要结论；2. 数据分布特征；3. 值得关注的点。'
    )
    return task, system_prompt, user_prompt


def _format_sse(event_name, payload):
    return f'event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'


def _call_qwen_chat(system_prompt, user_prompt):
    api_key, model, api_url, timeout = _get_qwen_api_config()
    response = requests.post(
        api_url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.4
        },
        timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get('choices') or []
    if not choices:
        raise ValueError('千问接口未返回有效内容')
    message = choices[0].get('message') or {}
    content = _extract_text_content(message.get('content'))
    if not content:
        raise ValueError('千问接口返回内容为空')
    return content


def _stream_qwen_chat(system_prompt, user_prompt):
    api_key, model, api_url, timeout = _get_qwen_api_config()
    response = requests.post(
        api_url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.4,
            'stream': True
        },
        stream=True,
        timeout=timeout
    )
    response.raise_for_status()

    content_type = (response.headers.get('content-type') or '').lower()
    if 'text/event-stream' not in content_type:
        data = response.json()
        choices = data.get('choices') or []
        if not choices:
            raise ValueError('千问接口未返回有效内容')
        message = choices[0].get('message') or {}
        content = _extract_text_content(message.get('content'))
        if content:
            yield 'message', {'content': content}
        yield 'done', {'done': True}
        return

    status_sent = False
    done_sent = False

    buffer = ''
    utf8_decoder = codecs.getincrementaldecoder('utf-8')()
    for raw_chunk in response.iter_content(chunk_size=None, decode_unicode=False):
        if not raw_chunk:
            continue

        buffer += utf8_decoder.decode(raw_chunk).replace('\r\n', '\n')
        while '\n\n' in buffer:
            block, buffer = buffer.split('\n\n', 1)
            lines = block.split('\n')
            data_lines = []
            for raw_line in lines:
                line = raw_line.strip()
                if not line or line.startswith(':'):
                    continue
                if line.startswith('data:'):
                    data_lines.append(line[5:].strip())

            if not data_lines:
                continue

            payload_text = '\n'.join(data_lines).strip()
            if payload_text == '[DONE]':
                if not done_sent:
                    done_sent = True
                    yield 'done', {'done': True}
                break

            payload = json.loads(payload_text)
            choices = payload.get('choices') or []
            if not choices:
                continue

            choice = choices[0]
            delta = choice.get('delta') or {}
            content_piece = _extract_text_content(delta.get('content'))

            if content_piece:
                yield 'message', {'content': content_piece}
                continue

            if delta.get('reasoning_content') and not status_sent:
                status_sent = True
                yield 'status', {'stage': 'thinking', 'message': 'AI 正在思考，请稍等...'}

            if choice.get('finish_reason') and not done_sent:
                done_sent = True
                yield 'done', {'done': True}
                break

        if done_sent:
            break

    buffer += utf8_decoder.decode(b'', final=True).replace('\r\n', '\n')

    if not done_sent:
        yield 'done', {'done': True}


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
        prediction_payload = pred(model, content)
        result_label = prediction_payload['label']

        # 如果当前有登录用户，则把预测记录写入 pred_records
        user_id = session.get('user_id')
        if user_id:
            try:
                querys(
                    'insert into pred_records (user_id,input_content,pred_result,create_time) '
                    'values (%s,%s,%s,now())',
                    [user_id, content, result_label]
                )
            except Exception as e:
                print("save pred_records error:", e)

        return jsonify({
            'message': 'success',
            'code': 200,
            'data': {
                'resultData': result_label,
                'topPredictions': prediction_payload['top_predictions'],
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


@app.route('/ai/assistant', methods=['POST'])
@login_required
def ai_assistant():
    payload = request.get_json(silent=True) or {}

    try:
        task, system_prompt, user_prompt = _build_ai_prompts(payload)
        content = _call_qwen_chat(system_prompt, user_prompt)
        return jsonify({
            'message': 'success',
            'code': 200,
            'data': {
                'task': task,
                'content': content
            }
        })
    except AIRequestValidationError as e:
        return jsonify({'message': str(e), 'code': e.status_code, 'data': None}), e.status_code
    except requests.HTTPError as e:
        detail = e.response.text[:500] if e.response is not None and e.response.text else str(e)
        return jsonify({'message': f'调用千问接口失败: {detail}', 'code': 500, 'data': None}), 500
    except Exception as e:
        return jsonify({'message': f'AI 助手调用失败: {e}', 'code': 500, 'data': None}), 500


@app.route('/ai/assistant/stream', methods=['POST'])
@login_required
def ai_assistant_stream():
    payload = request.get_json(silent=True) or {}

    try:
        task, system_prompt, user_prompt = _build_ai_prompts(payload)
    except AIRequestValidationError as e:
        return jsonify({'message': str(e), 'code': e.status_code, 'data': None}), e.status_code

    def generate():
        yield _format_sse('status', {'stage': 'connecting', 'message': 'AI 正在连接模型...'})
        try:
            for event_name, event_payload in _stream_qwen_chat(system_prompt, user_prompt):
                yield _format_sse(event_name, event_payload)
        except requests.HTTPError as e:
            detail = e.response.text[:500] if e.response is not None and e.response.text else str(e)
            yield _format_sse('error', {'message': f'调用千问接口失败: {detail}'})
        except Exception as e:
            yield _format_sse('error', {'message': f'AI 助手调用失败: {e}'})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )



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
