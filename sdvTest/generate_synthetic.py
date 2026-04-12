from __future__ import annotations

"""
病例数据流水线：先按「病类 + 内容相似度」把真实样本聚成组，再严格划分 train/test（同组不跨集，减轻泄露），
最后仅用真实训练集训练 SDV（GaussianCopula）按病类补全合成行并导出 CSV。
依赖 sdv 包；若未安装则只完成划分、跳过合成。
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    # 单表合成：元数据推断 + 高斯 Copula 拟合再采样
    from sdv.metadata import SingleTableMetadata
    from sdv.single_table import GaussianCopulaSynthesizer
except ModuleNotFoundError as exc:  # pragma: no cover - depends on local SDV env
    SingleTableMetadata = None
    GaussianCopulaSynthesizer = None
    SDV_IMPORT_ERROR = exc
else:
    SDV_IMPORT_ERROR = None


BASE_DIR = Path(__file__).resolve().parent
# 默认输入/输出路径（可用命令行覆盖）
DEFAULT_SOURCE_CSV = BASE_DIR / "cases_origin.csv"
DEFAULT_REAL_TRAIN_CSV = BASE_DIR / "cases_real_train_grouped.csv"
DEFAULT_REAL_TEST_CSV = BASE_DIR / "cases_real_test_grouped.csv"
DEFAULT_SYNTHETIC_CSV = BASE_DIR / "synthetic_cases_train_only.csv"

MIN_ROWS_PER_TYPE = 10  # 某病类真实训练行数低于此则不做合成
TEST_SIZE = 0.20  # 测试集约占该病类总样本的比例（按「相似组」为单位抽）
SIMILARITY_THRESHOLD = 0.90  # 字符 n-gram 余弦相似度 ≥ 此阈值的样本并入同一相似组
RANDOM_STATE = 42

ISO_DATE_RE = re.compile(r"^(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})$")
DOT_DATE_RE = re.compile(r"^(?P<month>\d{1,2})\.(?P<day>\d{1,2})$")
PUNCT_RE = re.compile(r"[\s,.;:!?()\-_/\u3002\uff0c\u3001\uff1b\uff1a\uff1f\uff01\u201c\u201d\u2018\u2019\uff08\uff09]+")

REQUIRED_COLUMNS = [
    "id",
    "type",
    "gender",
    "age",
    "time",
    "content",
    "docName",
    "docHospital",
    "department",
    "detailUrl",
    "height",
    "weight",
    "illDuration",
    "allergy",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="先做严格的训练/测试划分（按相似组避免泄露），再仅用真实训练集做 SDV 合成并导出。"
    )
    parser.add_argument("--source-csv", type=Path, default=DEFAULT_SOURCE_CSV, help="原始病例 CSV 路径")
    parser.add_argument("--real-train-csv", type=Path, default=DEFAULT_REAL_TRAIN_CSV, help="输出：真实训练集 CSV")
    parser.add_argument("--real-test-csv", type=Path, default=DEFAULT_REAL_TEST_CSV, help="输出：真实测试集 CSV")
    parser.add_argument("--synthetic-csv", type=Path, default=DEFAULT_SYNTHETIC_CSV, help="输出：合成病例 CSV")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="测试集约占该病类总样本的比例")
    parser.add_argument("--similarity-threshold", type=float, default=SIMILARITY_THRESHOLD, help="内容相似度阈值（余弦，0~1）")
    parser.add_argument("--min-rows-per-type", type=int, default=MIN_ROWS_PER_TYPE, help="某病类训练行数低于此则跳过合成")
    parser.add_argument(
        "--target-total-rows-per-type",
        type=int,
        default=None,
        help="增强后每个病类的目标总行数；省略则取真实训练集中最大病类规模",
    )
    return parser.parse_args()


def normalize_time(value: object) -> str | None:
    """把日期统一成 MM.DD 或保留原串，供模型与规则使用。"""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None

    match = ISO_DATE_RE.match(text)
    if match:
        month = max(1, min(12, int(match.group("month"))))
        day = max(1, min(31, int(match.group("day"))))
        return f"{month:02d}.{day:02d}"

    match = DOT_DATE_RE.match(text)
    if match:
        month = max(1, min(12, int(match.group("month"))))
        day = max(1, min(31, int(match.group("day"))))
        return f"{month:02d}.{day:02d}"

    return text


def normalize_for_grouping(value: object) -> str:
    text = "" if value is None else str(value).lower()
    text = PUNCT_RE.sub("", text)
    return text


def load_source_csv(csv_path: Path) -> pd.DataFrame:
    """读取原始病例表，校验必需列，清洗 type/content/time，并标记真实数据 is_synthetic=0。"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig", engine="python", dtype={"time": str})
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"缺少必需列：{missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["type"] = df["type"].fillna("").astype(str).str.strip()
    df["content"] = df["content"].fillna("").astype(str).str.strip()
    df["raw_content"] = df["content"]
    df["time"] = df["time"].apply(normalize_time)
    df = df[(df["type"] != "") & (df["raw_content"].str.len() >= 4)]
    df["is_synthetic"] = 0
    return df.reset_index(drop=True)


def build_group_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))


def build_similarity_groups(
    real_df: pd.DataFrame, similarity_threshold: float
) -> tuple[pd.Series, dict[str, int | dict[str, int]]]:
    """按病类分组，用语义相近（完全相同或 TF-IDF 余弦 ≥ 阈值）的样本并查集合并，生成每行的 similarity_group_id。"""
    if real_df.empty:
        raise ValueError("源数据表为空，无法构建相似度分组。")

    group_ids = pd.Series(index=real_df.index, dtype="object")
    duplicate_sample_count = 0
    non_singleton_group_count = 0
    max_group_size = 1
    total_group_count = 0
    label_group_counts: dict[str, int] = {}

    for label_order, (label, label_df) in enumerate(real_df.groupby("type", sort=True), start=1):
        row_indices = list(label_df.index)
        normalized_texts = []
        for position, raw_content in enumerate(label_df["raw_content"].tolist()):
            normalized = normalize_for_grouping(raw_content)
            normalized_texts.append(normalized or f"empty_{label_order}_{position}")

        sample_count = len(row_indices)
        parent = list(range(sample_count))

        def find(node: int) -> int:
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def union(left: int, right: int) -> None:
            root_left = find(left)
            root_right = find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        if sample_count > 1:
            group_vectors = build_group_vectorizer().fit_transform(normalized_texts)
            similarity_matrix = cosine_similarity(group_vectors)
            for left in range(sample_count):
                for right in range(left + 1, sample_count):
                    if (
                        normalized_texts[left] == normalized_texts[right]
                        or similarity_matrix[left][right] >= similarity_threshold
                    ):
                        union(left, right)

        local_groups: dict[int, list[int]] = {}
        for position, row_index in enumerate(row_indices):
            root = find(position)
            local_groups.setdefault(root, []).append(row_index)

        label_group_counts[label] = len(local_groups)
        total_group_count += len(local_groups)

        for local_order, members in enumerate(local_groups.values(), start=1):
            group_id = f"{label}::{label_order:02d}::{local_order:03d}"
            for row_index in members:
                group_ids.at[row_index] = group_id

            group_size = len(members)
            if group_size > 1:
                non_singleton_group_count += 1
                duplicate_sample_count += group_size - 1
            max_group_size = max(max_group_size, group_size)

    stats = {
        "group_count": int(total_group_count),
        "non_singleton_group_count": int(non_singleton_group_count),
        "duplicate_sample_count": int(duplicate_sample_count),
        "max_group_size": int(max_group_size),
        "label_group_counts": label_group_counts,
    }
    return group_ids, stats


def split_real_train_test(
    real_df: pd.DataFrame,
    test_size: float,
    similarity_threshold: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """以「相似组」为单元划分 train/test，避免同一组内样本分属两套集导致评估偏乐观。"""
    if real_df.empty:
        raise ValueError("源数据表为空，无法划分训练集/测试集。")

    split_df = real_df.copy()
    split_df["similarity_group_id"], group_stats = build_similarity_groups(
        split_df, similarity_threshold=similarity_threshold
    )

    group_frame = (
        split_df.groupby(["type", "similarity_group_id"])
        .size()
        .rename("sample_count")
        .reset_index()
    )

    selected_test_groups: set[str] = set()
    labels_without_group_holdout: list[str] = []

    for label_order, (label, label_groups) in enumerate(group_frame.groupby("type", sort=True), start=1):
        label_groups = label_groups.sample(frac=1, random_state=random_state + label_order).reset_index(drop=True)
        total_label_samples = int(label_groups["sample_count"].sum())

        if len(label_groups) <= 1:
            labels_without_group_holdout.append(label)
            continue

        target_test_count = max(1, int(round(total_label_samples * test_size)))
        current_test_count = 0
        chosen_groups: list[str] = []

        for position, row in label_groups.iterrows():
            groups_left_after_pick = len(label_groups) - (position + 1)
            if len(chosen_groups) >= len(label_groups) - 1:
                break

            chosen_groups.append(row["similarity_group_id"])
            current_test_count += int(row["sample_count"])

            if current_test_count >= target_test_count and groups_left_after_pick >= 1:
                break

        if len(chosen_groups) == len(label_groups):
            chosen_groups = chosen_groups[:-1]

        if not chosen_groups:
            chosen_groups = [label_groups.iloc[0]["similarity_group_id"]]

        selected_test_groups.update(chosen_groups)

    test_mask = split_df["similarity_group_id"].isin(selected_test_groups)
    train_df = split_df.loc[~test_mask].copy()
    test_df = split_df.loc[test_mask].copy()

    split_meta = {
        "group_count": int(group_stats["group_count"]),
        "non_singleton_group_count": int(group_stats["non_singleton_group_count"]),
        "duplicate_sample_count": int(group_stats["duplicate_sample_count"]),
        "max_group_size": int(group_stats["max_group_size"]),
        "train_group_count": int(train_df["similarity_group_id"].nunique()),
        "test_group_count": int(test_df["similarity_group_id"].nunique()),
        "similarity_threshold": round(float(similarity_threshold), 2),
        "labels_without_group_holdout": labels_without_group_holdout,
    }

    keep_columns = REQUIRED_COLUMNS + ["is_synthetic"]
    train_df = train_df[keep_columns].reset_index(drop=True)
    test_df = test_df[keep_columns].reset_index(drop=True)
    return train_df, test_df, split_meta


def prepare_model_dataframe(df_type: pd.DataFrame) -> pd.DataFrame:
    """喂给 SDV 前去掉 id / is_synthetic 等非生成列。"""
    model_df = df_type.drop(columns=[column for column in ("id", "is_synthetic") if column in df_type.columns]).copy()
    return model_df.reset_index(drop=True)


def synthesize_for_type(df_type: pd.DataFrame, type_name: str, num_rows: int) -> pd.DataFrame:
    """对单个病类的训练子表拟合 GaussianCopulaSynthesizer 并采样 num_rows 条。"""
    if GaussianCopulaSynthesizer is None or SingleTableMetadata is None:
        raise RuntimeError(f"无法使用 SDV：{SDV_IMPORT_ERROR}")

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df_type)
    if "time" in df_type.columns:
        metadata.update_column(column_name="time", sdtype="categorical")

    synthesizer = GaussianCopulaSynthesizer(metadata)
    synthesizer.fit(df_type)

    synthetic_df = synthesizer.sample(num_rows=num_rows)
    if "type" in synthetic_df.columns:
        synthetic_df["type"] = type_name
    else:
        synthetic_df.insert(0, "type", type_name)
    return synthetic_df


def apply_light_domain_rules(df: pd.DataFrame) -> pd.DataFrame:
    """合成后轻量清洗：换行、年龄裁剪、月经失调强制女、time 再规范化、id 置空、标记 is_synthetic=1。"""
    cleaned = df.copy()

    if "content" in cleaned.columns:
        cleaned["content"] = (
            cleaned["content"]
            .astype(str)
            .str.replace("\r", " ", regex=False)
            .str.replace("\n", " ", regex=False)
        )

    for column in ("docName", "docHospital", "department", "detailUrl", "illDuration", "allergy"):
        if column in cleaned.columns:
            cleaned[column] = (
                cleaned[column]
                .astype(str)
                .str.replace("\r", " ", regex=False)
                .str.replace("\n", " ", regex=False)
            )

    if "type" in cleaned.columns and "gender" in cleaned.columns:
        menstrual_mask = cleaned["type"] == "月经失调"
        cleaned.loc[menstrual_mask, "gender"] = "女"

    if "age" in cleaned.columns:
        cleaned["age"] = pd.to_numeric(cleaned["age"], errors="coerce")
        cleaned["age"] = cleaned["age"].clip(lower=0, upper=100)
        cleaned = cleaned[cleaned["age"].notna()]
        cleaned["age"] = cleaned["age"].round().astype(int)

    if "time" in cleaned.columns:
        cleaned["time"] = cleaned["time"].apply(normalize_time)

    if "id" in cleaned.columns:
        cleaned["id"] = np.nan
    else:
        cleaned.insert(0, "id", np.nan)

    cleaned["is_synthetic"] = 1
    return cleaned


def save_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()

    # 1) 读原始表 → 2) 组级划分真实 train/test 并落盘
    source_df = load_source_csv(args.source_csv)
    real_train_df, real_test_df, split_meta = split_real_train_test(
        source_df,
        test_size=args.test_size,
        similarity_threshold=args.similarity_threshold,
        random_state=RANDOM_STATE,
    )

    save_csv(real_train_df, args.real_train_csv)
    save_csv(real_test_df, args.real_test_csv)

    print("严格划分已完成。")
    print(
        f"真实训练行数：{len(real_train_df)}，真实测试行数：{len(real_test_df)}，"
        f"相似组数：{split_meta['group_count']}，组内重复样本数：{split_meta['duplicate_sample_count']}"
    )
    print(f"已保存真实训练集：{args.real_train_csv}")
    print(f"已保存真实测试集：{args.real_test_csv}")

    if GaussianCopulaSynthesizer is None or SingleTableMetadata is None:
        print(f"未检测到 SDV，已跳过合成：{SDV_IMPORT_ERROR}")
        return

    # 3) 按病类用真实训练集补到目标条数（默认对齐最大病类规模），导出合成 CSV
    target_total_rows_per_type = args.target_total_rows_per_type
    if target_total_rows_per_type is None:
        target_total_rows_per_type = int(real_train_df["type"].value_counts().max())

    all_synthetic: list[pd.DataFrame] = []
    skipped_labels: list[str] = []

    for type_name, df_type in real_train_df.groupby("type", sort=True):
        if len(df_type) < args.min_rows_per_type:
            skipped_labels.append(type_name)
            continue

        synthetic_count = max(target_total_rows_per_type - len(df_type), 0)
        if synthetic_count == 0:
            continue

        model_df = prepare_model_dataframe(df_type)
        synthetic_df = synthesize_for_type(model_df, type_name, synthetic_count)
        all_synthetic.append(synthetic_df)
        print(
            f"病类「{type_name}」真实训练 {len(df_type)} 行，本次合成增补 {synthetic_count} 行，"
            f"目标总条数 {target_total_rows_per_type}"
        )

    if not all_synthetic:
        print("未生成任何合成行，请检查 --min-rows-per-type 或 --target-total-rows-per-type。")
        return

    synthetic_df = pd.concat(all_synthetic, ignore_index=True)
    synthetic_df = apply_light_domain_rules(synthetic_df)

    export_columns = REQUIRED_COLUMNS + ["is_synthetic"]
    for column in export_columns:
        if column not in synthetic_df.columns:
            synthetic_df[column] = np.nan
    synthetic_df = synthetic_df[export_columns]

    save_csv(synthetic_df, args.synthetic_csv)

    print(f"已保存合成数据：{args.synthetic_csv}")
    print(f"合成行数：{len(synthetic_df)}")
    if skipped_labels:
        print(f"已跳过病类（训练行数过少）：{sorted(skipped_labels)}")


if __name__ == "__main__":
    main()
