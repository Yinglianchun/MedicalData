"""
病例主诉 → 疾病类型（type）预测：从 MySQL 读 cases，jieba 分词 + TF-IDF + 随机森林。
含相似文本分组、组级划分测试集、真实/合成训练对比，以及供接口使用的模型与指标缓存。
"""
import os
import re

import jieba
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text

# SQLAlchemy 连接串（账号库名与本机 MySQL、utils/query.py 一致）
conn = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/medicalinfo?charset=utf8')

BASE_DIR = os.path.dirname(__file__)
STOPWORDS_PATH = os.path.join(BASE_DIR, 'stopword.txt')
MEDICAL_TERMS_PATH = os.path.join(BASE_DIR, 'medical_terms.txt')
SIMILARITY_THRESHOLD = 0.90  # 组内「近似重复」的字符 n-gram 余弦相似度下限
TEST_SIZE = 0.20  # 按病类划分测试时，测试集约占该病类总样本比例

# 分词时过滤的停用词集合
stopwords = set(open(STOPWORDS_PATH, 'r', encoding='utf-8').read().splitlines())

# jieba 自定义词表默认种子；若存在 medical_terms.txt 则优先读文件
DEFAULT_MEDICAL_TERMS = [
    '高血压',
    '血压偏高',
    '降压药',
    '冠心病',
    '冠状动脉',
    '冠状动脉粥样硬化',
    '冠状动脉CTA',
    '颈动脉斑块',
    '心肌梗死',
    '胸痛',
    '胸闷',
    '心悸',
    '糖尿病',
    '血糖',
    '小儿感冒',
    '上呼吸道感染',
    '发热',
    '咳嗽',
    '月经失调',
    '痛经',
    '腰椎间盘突出',
    '腰腿痛',
    '颈椎病',
    '骨折',
    '胃炎',
    '慢性胃炎',
    '胃痛',
    '肺癌',
    '肺部结节',
    '脑梗',
    '脑梗死'
]


def load_medical_terms():
    """读取 medical_terms.txt；不存在或为空则返回内置 DEFAULT_MEDICAL_TERMS。"""
    terms = []
    if os.path.exists(MEDICAL_TERMS_PATH):
        with open(MEDICAL_TERMS_PATH, 'r', encoding='utf-8') as term_file:
            terms = [line.strip() for line in term_file if line.strip()]
    return terms or DEFAULT_MEDICAL_TERMS


def init_medical_terms():
    """将医学词加入 jieba 词典并调整词频，减少被错误切分。"""
    for term in load_medical_terms():
        jieba.add_word(term)
        jieba.suggest_freq(term, tune=True)


init_medical_terms()

# 全局缓存：预测时复用已训练向量化器与模型，避免每次请求重训
vectorizer = None
_cached_model = None
_cached_metrics = None
_cached_real_only = False


def tokenize(content):
    """jieba 分词并去停用词；医学复合词由 init_medical_terms 预先注入。"""
    content = '' if content is None else str(content)
    words = [word for word in jieba.cut(content) if word and word not in stopwords]
    return ' '.join(words)


def normalize_for_grouping(content):
    """去空白与标点、转小写，供相似度分组用。"""
    content = '' if content is None else str(content).lower()
    content = re.sub(r'\s+', '', content)
    content = re.sub(r'[，。、“”‘’；：？！,.!?（）()\-_/]+', '', content)
    return content


def getData(real_only=True, real_id_max=405):
    """
    从库中读取病例并做基础清洗（正文、类型非空等），再对 content 做分词。
    real_only=True 时优先只取真实样本：有 is_synthetic 且列有区分度则取 0；否则退回 id<=real_id_max。
    """
    df = pd.read_sql(text('select * from cases'), con=conn, index_col='id')

    if real_only:
        use_id_fallback = False
        if 'is_synthetic' in df.columns:
            syn_col = pd.to_numeric(df['is_synthetic'], errors='coerce').fillna(0).astype(int)
            if syn_col.nunique(dropna=False) <= 1:
                use_id_fallback = True
            else:
                df = df[syn_col == 0]
        else:
            use_id_fallback = True

        if use_id_fallback:
            df = df[df.index <= real_id_max]

    if 'content' not in df.columns or 'type' not in df.columns:
        raise ValueError('cases 表中缺少 content/type 字段')

    df = df[['content', 'type']].copy()
    df['raw_content'] = df['content'].fillna('').astype(str).str.strip()
    df['type'] = df['type'].fillna('').astype(str).str.strip()
    df = df[(df['raw_content'] != '') & (df['raw_content'].str.len() >= 4) & (df['type'] != '')]
    df['content'] = df['raw_content'].apply(tokenize)
    return df[['raw_content', 'content', 'type']]


def build_vectorizer():
    """训练/预测用的词级 TF-IDF（用于随机森林输入）。"""
    return TfidfVectorizer(max_features=10000)


def build_group_vectorizer():
    """相似度分组用的字符 n-gram TF-IDF（与 generate_synthetic 思路一致）。"""
    return TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))


def build_model():
    """多分类随机森林；class_weight 缓解类别不平衡。"""
    return RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')


def build_metrics(y_true, y_pred, train_sample_count, test_sample_count, class_count, stratify_used, extra=None):
    """汇总准确率、宏/加权 F1 及样本统计，供管理端展示。"""
    report_dict = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    metrics = {
        'train_sample_count': int(train_sample_count),
        'test_sample_count': int(test_sample_count),
        'class_count': int(class_count),
        'stratify_used': bool(stratify_used),
        'accuracy': round(float(accuracy_score(y_true, y_pred)), 4),
        'macro_f1': round(float(f1_score(y_true, y_pred, average='macro', zero_division=0)), 4),
        'weighted_f1': round(float(report_dict.get('weighted avg', {}).get('f1-score', 0.0)), 4)
    }
    if extra:
        metrics.update(extra)
    return metrics


def fit_model(data, update_global=True):
    """在指定数据上拟合向量化器 + 模型；update_global 为 True 时写入全局 vectorizer。"""
    if data.empty:
        raise ValueError('训练数据为空，请检查 cases 数据')

    fitted_vectorizer = build_vectorizer()
    x_vectors = fitted_vectorizer.fit_transform(data['content'])

    model = build_model()
    model.fit(x_vectors, data['type'])

    if update_global:
        global vectorizer
        vectorizer = fitted_vectorizer
    return model


def build_similarity_groups(real_df, similarity_threshold=SIMILARITY_THRESHOLD):
    """在每个病类内，将完全相同或相似度达阈值的样本用并查集合并为若干组。"""
    if real_df.empty:
        raise ValueError('真实数据为空，无法构建相似病例分组')

    group_ids = pd.Series(index=real_df.index, dtype='object')
    duplicate_sample_count = 0
    non_singleton_group_count = 0
    max_group_size = 1
    label_group_counts = {}
    total_group_count = 0

    for label_order, (label, label_df) in enumerate(real_df.groupby('type', sort=True), start=1):
        row_indices = list(label_df.index)
        normalized_texts = []
        for position, raw_content in enumerate(label_df['raw_content'].tolist()):
            normalized = normalize_for_grouping(raw_content)
            normalized_texts.append(normalized or f'empty_{label_order}_{position}')

        sample_count = len(row_indices)
        parent = list(range(sample_count))

        def find(node):
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def union(left, right):
            root_left = find(left)
            root_right = find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        if sample_count > 1:
            group_vectors = build_group_vectorizer().fit_transform(normalized_texts)
            similarity_matrix = cosine_similarity(group_vectors)
            for left in range(sample_count):
                for right in range(left + 1, sample_count):
                    if normalized_texts[left] == normalized_texts[right] or similarity_matrix[left][right] >= similarity_threshold:
                        union(left, right)

        local_groups = {}
        for position, row_index in enumerate(row_indices):
            root = find(position)
            local_groups.setdefault(root, []).append(row_index)

        label_group_counts[label] = len(local_groups)
        total_group_count += len(local_groups)

        for local_order, members in enumerate(local_groups.values(), start=1):
            group_id = f'{label}::{label_order:02d}::{local_order:03d}'
            for row_index in members:
                group_ids.at[row_index] = group_id

            group_size = len(members)
            if group_size > 1:
                non_singleton_group_count += 1
                duplicate_sample_count += group_size - 1
            max_group_size = max(max_group_size, group_size)

    stats = {
        'group_count': int(total_group_count),
        'non_singleton_group_count': int(non_singleton_group_count),
        'duplicate_sample_count': int(duplicate_sample_count),
        'max_group_size': int(max_group_size),
        'label_group_counts': label_group_counts
    }
    return group_ids, stats


def split_real_train_test(real_df, test_size=TEST_SIZE, similarity_threshold=SIMILARITY_THRESHOLD, random_state=42):
    """
    按「相似组」为单位抽测试集，使相近主诉不会同时出现在训练与测试中，减轻模板化重复带来的虚高指标。
    """
    if real_df.empty:
        raise ValueError('真实数据为空，请检查 real_only 过滤规则')

    split_df = real_df.copy()
    split_df['similarity_group_id'], group_stats = build_similarity_groups(split_df, similarity_threshold=similarity_threshold)

    group_frame = (
        split_df.groupby(['type', 'similarity_group_id'])
        .size()
        .rename('sample_count')
        .reset_index()
    )

    selected_test_groups = set()
    labels_without_group_holdout = []

    for label_order, (label, label_groups) in enumerate(group_frame.groupby('type', sort=True), start=1):
        label_groups = label_groups.sample(frac=1, random_state=random_state + label_order).reset_index(drop=True)
        total_label_samples = int(label_groups['sample_count'].sum())

        if len(label_groups) <= 1:
            labels_without_group_holdout.append(label)
            continue

        target_test_count = max(1, int(round(total_label_samples * test_size)))
        current_test_count = 0
        chosen_groups = []

        for position, row in label_groups.iterrows():
            groups_left_after_pick = len(label_groups) - (position + 1)
            if len(chosen_groups) >= len(label_groups) - 1:
                break

            chosen_groups.append(row['similarity_group_id'])
            current_test_count += int(row['sample_count'])

            if current_test_count >= target_test_count and groups_left_after_pick >= 1:
                break

        if len(chosen_groups) == len(label_groups):
            chosen_groups = chosen_groups[:-1]

        if not chosen_groups:
            chosen_groups = [label_groups.iloc[0]['similarity_group_id']]

        selected_test_groups.update(chosen_groups)

    test_mask = split_df['similarity_group_id'].isin(selected_test_groups)
    train_df = split_df.loc[~test_mask].copy()
    test_df = split_df.loc[test_mask].copy()

    # 仅当按组划分导致训练或测试一侧为空时，退回普通随机划分
    if train_df.empty or test_df.empty:
        label_counts = split_df['type'].value_counts()
        can_stratify = (label_counts.min() >= 2) and (label_counts.shape[0] >= 2)
        train_df, test_df = train_test_split(
            split_df,
            test_size=test_size,
            random_state=random_state,
            stratify=split_df['type'] if can_stratify else None
        )
        labels_without_group_holdout = sorted(split_df['type'].unique().tolist())
        test_set_strategy = 'sample_fallback_holdout'
    else:
        test_set_strategy = 'grouped_similarity_holdout'

    split_meta = {
        'stratify_used': bool(
            train_df['type'].nunique() == split_df['type'].nunique()
            and test_df['type'].nunique() == split_df['type'].nunique()
        ),
        'group_count': int(group_stats['group_count']),
        'non_singleton_group_count': int(group_stats['non_singleton_group_count']),
        'duplicate_sample_count': int(group_stats['duplicate_sample_count']),
        'max_group_size': int(group_stats['max_group_size']),
        'train_group_count': int(train_df['similarity_group_id'].nunique()),
        'test_group_count': int(test_df['similarity_group_id'].nunique()),
        'similarity_threshold': round(float(similarity_threshold), 2),
        'labels_without_group_holdout': labels_without_group_holdout,
        'test_set_strategy': test_set_strategy
    }

    train_df = train_df[['raw_content', 'content', 'type']].reset_index(drop=True)
    test_df = test_df[['raw_content', 'content', 'type']].reset_index(drop=True)
    return train_df, test_df, split_meta


def get_synthetic_data(real_id_max=405):
    """在全量与真实子集差集中取出合成行，规则与线上训练用的 getData 一致。"""
    full_df = getData(real_only=False, real_id_max=real_id_max)
    real_df = getData(real_only=True, real_id_max=real_id_max)
    synthetic_df = full_df.loc[~full_df.index.isin(real_df.index)].copy()
    return synthetic_df.reset_index(drop=True)


def train_and_eval_on_fixed_test(train_df, test_df, stratify_used, test_set_strategy, update_global=False):
    """在给定训练集上拟合模型，在固定真实测试集上算指标；可选更新全局 vectorizer。"""
    if train_df.empty or test_df.empty:
        raise ValueError('训练集或测试集为空，请检查数据过滤规则')

    fitted_vectorizer = build_vectorizer()
    x_train_vectors = fitted_vectorizer.fit_transform(train_df['content'])
    x_test_vectors = fitted_vectorizer.transform(test_df['content'])

    model = build_model()
    model.fit(x_train_vectors, train_df['type'])

    y_pred = model.predict(x_test_vectors)
    metrics = build_metrics(
        test_df['type'],
        y_pred,
        train_sample_count=len(train_df),
        test_sample_count=len(test_df),
        class_count=train_df['type'].nunique(),
        stratify_used=stratify_used,
        extra={
            'test_set_strategy': test_set_strategy,
            'test_real_only': True
        }
    )

    if update_global:
        global vectorizer
        vectorizer = fitted_vectorizer
    return model, metrics


def compose_training_data(real_train_df, synthetic_df, real_only):
    """real_only 则只用真实训练行；否则拼接合成样本。"""
    if real_only:
        return real_train_df.copy()
    return pd.concat([real_train_df, synthetic_df], ignore_index=True)


def refresh_model_cache(real_only=False, compare=False, real_id_max=405):
    """
    用组级真实测试集重算指标；再在「当前选用的训练数据」上拟合可部署模型并写入全局缓存。
    compare=True 时会多算一套对比模式下的指标与差值。
    """
    real_df = getData(real_only=True, real_id_max=real_id_max)
    real_train_df, real_test_df, split_meta = split_real_train_test(real_df)
    synthetic_df = get_synthetic_data(real_id_max=real_id_max)

    active_train_df = compose_training_data(real_train_df, synthetic_df, real_only=real_only)
    _, active_metrics = train_and_eval_on_fixed_test(
        active_train_df,
        real_test_df,
        stratify_used=split_meta['stratify_used'],
        test_set_strategy=split_meta['test_set_strategy'],
        update_global=False
    )
    active_metrics = {
        **active_metrics,
        'real_only': bool(real_only),
        'real_train_count': int(len(real_train_df)),
        'synthetic_train_count': 0 if real_only else int(len(synthetic_df)),
        'group_count': int(split_meta['group_count']),
        'non_singleton_group_count': int(split_meta['non_singleton_group_count']),
        'duplicate_sample_count': int(split_meta['duplicate_sample_count']),
        'max_group_size': int(split_meta['max_group_size']),
        'train_group_count': int(split_meta['train_group_count']),
        'test_group_count': int(split_meta['test_group_count']),
        'similarity_threshold': split_meta['similarity_threshold'],
        'labels_without_group_holdout': split_meta['labels_without_group_holdout']
    }

    result = {'active': active_metrics}

    if compare:
        compare_real_only = not bool(real_only)
        compare_train_df = compose_training_data(real_train_df, synthetic_df, real_only=compare_real_only)
        _, compare_metrics = train_and_eval_on_fixed_test(
            compare_train_df,
            real_test_df,
            stratify_used=split_meta['stratify_used'],
            test_set_strategy=split_meta['test_set_strategy'],
            update_global=False
        )
        compare_metrics = {
            **compare_metrics,
            'real_only': compare_real_only,
            'real_train_count': int(len(real_train_df)),
            'synthetic_train_count': 0 if compare_real_only else int(len(synthetic_df)),
            'group_count': int(split_meta['group_count']),
            'non_singleton_group_count': int(split_meta['non_singleton_group_count']),
            'duplicate_sample_count': int(split_meta['duplicate_sample_count']),
            'max_group_size': int(split_meta['max_group_size']),
            'train_group_count': int(split_meta['train_group_count']),
            'test_group_count': int(split_meta['test_group_count']),
            'similarity_threshold': split_meta['similarity_threshold'],
            'labels_without_group_holdout': split_meta['labels_without_group_holdout']
        }
        result['compare'] = compare_metrics
        result['delta'] = {
            'accuracy_diff': round(active_metrics['accuracy'] - compare_metrics['accuracy'], 4),
            'macro_f1_diff': round(active_metrics['macro_f1'] - compare_metrics['macro_f1'], 4)
        }

    deploy_df = getData(real_only=real_only, real_id_max=real_id_max)
    deploy_model = fit_model(deploy_df, update_global=True)

    global _cached_model, _cached_metrics, _cached_real_only
    _cached_model = deploy_model
    _cached_metrics = {
        **active_metrics,
        'deploy_sample_count': int(len(deploy_df)),
        'evaluation_strategy': 'grouped_similarity_holdout_then_full_retrain'
    }
    _cached_real_only = bool(real_only)

    return result


def retrain_and_get_metrics(real_only=True, compare=False):
    """触发 refresh_model_cache，返回结构化指标供管理端接口使用。"""
    return refresh_model_cache(real_only=real_only, compare=compare)


def get_or_train_model(force_retrain=False, real_only=False):
    """返回缓存的预测用模型；无缓存、强制重训或 real_only 模式变化时先刷新缓存。"""
    global _cached_model, _cached_real_only
    mode_changed = bool(real_only) != bool(_cached_real_only)
    if _cached_model is None or force_retrain or mode_changed:
        refresh_model_cache(real_only=real_only, compare=False)
    return _cached_model


def get_cached_metrics():
    """返回最近一次 refresh 写入的指标字典（可能为 None）。"""
    return _cached_metrics


def get_data_source_stats(real_id_max=405):
    """统计库中真实/合成条数与 is_synthetic 列是否生效，便于核对对比实验数据是否按预期划分。"""
    columns_df = pd.read_sql(text('show columns from cases'), con=conn)
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


def pred(model, content, top_k=3):
    """对单条主诉预测 type，返回最高概率标签与 top_k 候选及概率。"""
    global vectorizer
    if vectorizer is None:
        raise ValueError('vectorizer 未初始化，请先训练模型')

    content_tokens = tokenize(content)
    content_vector = vectorizer.transform([content_tokens])

    prediction = model.predict(content_vector)[0]
    probabilities = model.predict_proba(content_vector)[0]
    classes = model.classes_

    ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)[:top_k]
    top_predictions = [
        {
            'label': label,
            'probability': round(float(probability), 4),
            'percent': f"{round(float(probability) * 100, 2)}%"
        }
        for label, probability in ranked
    ]

    return {
        'label': prediction,
        'top_predictions': top_predictions
    }
