import jieba
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text

# 创建数据库连接
conn = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/medicalinfo?charset=utf8')

# 读取停用词表
stopwords = set(
    open(os.path.join(os.path.dirname(__file__), "stopword.txt"), 'r', encoding='utf-8')
    .read()
    .splitlines()
)

# 全局模型缓存：避免每次预测都重新训练
vectorizer = None
_cached_model = None
_cached_metrics = None
_cached_real_only = False


def tokenize(text):
    """使用结巴分词，并去除停用词。"""
    text = '' if text is None else str(text)
    words = [word for word in jieba.cut(text) if word and word not in stopwords]
    return ' '.join(words)


def getData(real_only=True, real_id_max=405):
    """
    从数据库读取病例数据并做基础清洗。
    real_only=True 时优先仅使用真实数据：
    1) 若表中有 is_synthetic 字段 -> is_synthetic=0
    2) 否则回退到 id<=real_id_max
    """
    df = pd.read_sql(text('select * from cases'), con=conn, index_col='id')

    if real_only:
        # 优先使用 is_synthetic；若该列失真（例如全是 0），自动回退到 id 阈值策略
        use_id_fallback = False
        if 'is_synthetic' in df.columns:
            syn_col = pd.to_numeric(df['is_synthetic'], errors='coerce').fillna(0).astype(int)
            # 全为同一取值时，通常说明导入时没有正确标注 synthetic
            if syn_col.nunique(dropna=False) <= 1:
                use_id_fallback = True
            else:
                df = df[syn_col == 0]
        else:
            use_id_fallback = True

        if use_id_fallback:
            df = df[df.index <= real_id_max]

    if 'content' not in df.columns or 'type' not in df.columns:
        raise ValueError("cases 表中缺少 content/type 字段")

    df = df[['content', 'type']].copy()
    df['content'] = df['content'].fillna('').astype(str).str.strip()
    df['type'] = df['type'].fillna('').astype(str).str.strip()
    df = df[(df['content'] != '') & (df['content'].str.len() >= 4) & (df['type'] != '')]
    df['content'] = df['content'].apply(tokenize)
    return df


def model_train(data, update_global=True):
    """
    训练模型并打印评估结果。
    - 默认 stratify 切分，类别分布更稳
    - 输出 accuracy + macro_f1 + 分类报告
    """
    if data.empty:
        raise ValueError("训练数据为空，请检查 cases 数据")

    x = data['content']
    y = data['type']
    label_counts = y.value_counts()
    can_stratify = (label_counts.min() >= 2) and (label_counts.shape[0] >= 2)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if can_stratify else None
    )

    fitted_vectorizer = TfidfVectorizer(max_features=10000)
    x_train_vectors = fitted_vectorizer.fit_transform(x_train)
    x_test_vectors = fitted_vectorizer.transform(x_test)

    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    model.fit(x_train_vectors, y_train)

    y_pred = model.predict(x_test_vectors)
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    report_text = classification_report(y_test, y_pred, zero_division=0)
    report_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)

    metrics = {
        'sample_count': int(len(data)),
        'class_count': int(y.nunique()),
        'stratify_used': bool(can_stratify),
        'accuracy': round(float(acc), 4),
        'macro_f1': round(float(macro_f1), 4),
        'weighted_f1': round(float(report_dict.get('weighted avg', {}).get('f1-score', 0.0)), 4)
    }

    # 保持原有命令行输出习惯
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro-F1: {metrics['macro_f1']:.4f}")
    print("Classification Report:")
    print(report_text)

    if update_global:
        global vectorizer
        vectorizer = fitted_vectorizer
    return model, metrics


def retrain_and_get_metrics(real_only=True, compare=False):
    """
    重训并返回结构化评估指标。
    compare=True 时会额外训练对照组并返回 A/B 对比结果：
    - active: 当前使用配置（real_only 参数决定）
    - compare: 对照配置
    """
    model, active_metrics = model_train(getData(real_only=real_only), update_global=True)

    global _cached_model, _cached_metrics, _cached_real_only
    _cached_model = model
    _cached_metrics = {**active_metrics, 'real_only': bool(real_only)}
    _cached_real_only = bool(real_only)

    result = {'active': _cached_metrics}
    if compare:
        # 额外训练对照组，仅用于观测，不覆盖当前缓存模型
        _, compare_metrics = model_train(getData(real_only=not bool(real_only)), update_global=False)
        compare_payload = {**compare_metrics, 'real_only': not bool(real_only)}
        result['compare'] = compare_payload
        result['delta'] = {
            'accuracy_diff': round(result['active']['accuracy'] - result['compare']['accuracy'], 4),
            'macro_f1_diff': round(result['active']['macro_f1'] - result['compare']['macro_f1'], 4)
        }
    return result


def get_or_train_model(force_retrain=False, real_only=False):
    """获取缓存模型；无缓存或强制重训时重新训练。"""
    global _cached_model, _cached_metrics, _cached_real_only
    mode_changed = bool(real_only) != bool(_cached_real_only)
    if _cached_model is None or force_retrain or mode_changed:
        model, metrics = model_train(getData(real_only=real_only), update_global=True)
        _cached_model = model
        _cached_metrics = {**metrics, 'real_only': bool(real_only)}
        _cached_real_only = bool(real_only)
    return _cached_model


def get_cached_metrics():
    return _cached_metrics


def get_data_source_stats(real_id_max=405):
    """
    返回病例数据来源统计，帮助判断 real_only 策略是否真的生效。
    """
    # 兼容 cases 不存在 is_synthetic 字段的情况
    columns_df = pd.read_sql(text("show columns from cases"), con=conn)
    col_names = set(columns_df['Field'].astype(str).tolist())
    has_is_synthetic = 'is_synthetic' in col_names

    if has_is_synthetic:
        df = pd.read_sql(text('select id, is_synthetic from cases'), con=conn)
    else:
        df = pd.read_sql(text('select id from cases'), con=conn)

    total = int(len(df))
    stats = {
        'total': total,
        'has_is_synthetic': has_is_synthetic
    }

    if 'is_synthetic' in df.columns:
        syn_col = pd.to_numeric(df['is_synthetic'], errors='coerce').fillna(0).astype(int)
        stats.update({
            'is_synthetic_unique': int(syn_col.nunique(dropna=False)),
            'real_by_flag': int((syn_col == 0).sum()),
            'synthetic_by_flag': int((syn_col == 1).sum()),
            'fallback_real_by_id': int((df['id'] <= real_id_max).sum()),
            'fallback_synthetic_by_id': int((df['id'] > real_id_max).sum())
        })
    else:
        stats.update({
            'fallback_real_by_id': int((df['id'] <= real_id_max).sum()),
            'fallback_synthetic_by_id': int((df['id'] > real_id_max).sum())
        })
    return stats


def pred(model, content):
    global vectorizer
    if vectorizer is None:
        raise ValueError("vectorizer 未初始化，请先训练模型")
    content_tokens = tokenize(content)
    content_vector = vectorizer.transform([content_tokens])
    prediction = model.predict(content_vector)
    return prediction[0]

