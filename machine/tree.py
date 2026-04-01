import jieba # 区分词组
import pandas as pd
from sklearn.model_selection import train_test_split  # 安装scikit-learn库 而不是sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sqlalchemy import create_engine,text

conn = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/medicalinfo?charset=utf8')
# 读取停用词表
stopwords = set(open("./stopword.txt", 'r', encoding='utf-8').read().splitlines())

def tokenize(text):
    text = '' if text is None else str(text)
    words = [word for word in jieba.cut(text) if word and word not in stopwords]  # 使用jieba库分词
    return ' '.join(words)
def getData(real_only=True, real_id_max=405):
    query = text('select * from cases')
    df = pd.read_sql(query,con=conn,index_col='id')

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

    data = df[['content', 'type']].copy()
    data['content'] = data['content'].fillna('').astype(str).str.strip()
    data['type'] = data['type'].fillna('').astype(str).str.strip()
    data = data[(data['content'] != '') & (data['content'].str.len() >= 4) & (data['type'] != '')]
    data['content'] = data['content'].apply(tokenize)  # 为每一条data['content']数据运用tokenize
    return data

def evaluate_with_fixed_test(train_df, test_df):
    """在固定测试集上训练并评估，避免 A/B 测试集不一致。"""
    if train_df.empty or test_df.empty:
        raise ValueError("训练集或测试集为空，请检查数据")

    vectorizer = TfidfVectorizer(max_features=10000)
    x_train_vectorizer = vectorizer.fit_transform(train_df['content'])
    x_test_vectorizer = vectorizer.transform(test_df['content'])

    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    model.fit(x_train_vectorizer, train_df['type'])
    y_pred = model.predict(x_test_vectorizer)

    accuracy = accuracy_score(test_df['type'], y_pred)
    macro_f1 = f1_score(test_df['type'], y_pred, average='macro', zero_division=0)
    print("Accuracy:", round(accuracy, 4))
    print("Macro-F1:", round(macro_f1, 4))
    print("Classification Report:")
    print(classification_report(test_df['type'], y_pred, zero_division=0))
    return {
        'train_sample_count': int(len(train_df)),
        'test_sample_count': int(len(test_df)),
        'class_count': int(train_df['type'].nunique()),
        'accuracy': round(float(accuracy), 4),
        'macro_f1': round(float(macro_f1), 4)
    }


def split_real_train_test(real_df):
    """先固定真实数据测试集，A/B 共用同一个 real_test。"""
    if real_df.empty:
        raise ValueError("真实数据为空，请检查 real_only 过滤规则")
    label_counts = real_df['type'].value_counts()
    can_stratify = (label_counts.min() >= 2) and (label_counts.shape[0] >= 2)
    train_df, test_df = train_test_split(
        real_df,
        test_size=0.2,
        random_state=42,
        stratify=real_df['type'] if can_stratify else None
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def get_synthetic_data(real_id_max=405):
    """获取合成数据（无 is_synthetic 字段时使用 id>405 约定）。"""
    full_df = getData(real_only=False, real_id_max=real_id_max)
    real_df = getData(real_only=True, real_id_max=real_id_max)
    # 通过 id 差集拿到 synthetic；index 来自 cases.id，天然可比
    synthetic_df = full_df.loc[~full_df.index.isin(real_df.index)].copy()
    return synthetic_df.reset_index(drop=True)


if __name__ == '__main__':
        real_df = getData(real_only=True)
        synthetic_df = get_synthetic_data()
        real_train_df, real_test_df = split_real_train_test(real_df)

        print("=== 固定真实测试集信息 ===")
        print("real_train:", len(real_train_df), "real_test:", len(real_test_df), "synthetic:", len(synthetic_df))

        print("\n=== A 组：仅真实训练 -> 真实测试 ===")
        a_metrics = evaluate_with_fixed_test(real_train_df, real_test_df)
        print("指标：", a_metrics)

        print("\n=== B 组：真实+合成训练 -> 同一真实测试 ===")
        b_train_df = pd.concat([real_train_df, synthetic_df], ignore_index=True)
        b_metrics = evaluate_with_fixed_test(b_train_df, real_test_df)
        print("指标：", b_metrics)

        print("\n=== 差值（B-A）===")
        print("Accuracy Diff:", round(b_metrics['accuracy'] - a_metrics['accuracy'], 4))
        print("Macro-F1 Diff:", round(b_metrics['macro_f1'] - a_metrics['macro_f1'], 4))
