from __future__ import annotations

"""
将合成（或指定）病例 CSV 批量写入 MySQL 的 cases 表。
导入前会删除表中 is_synthetic=1 的旧行，避免重复堆积；库连接参数需与本机 MySQL 及项目 utils/query.py 一致。
"""

import argparse
import math
from pathlib import Path

import pandas as pd
import pymysql


BASE_DIR = Path(__file__).resolve().parent
# 未指定 --csv 时按顺序找第一个存在的文件
DEFAULT_CSV_CANDIDATES = [
    BASE_DIR / "synthetic_cases_train_only.csv",
    BASE_DIR / "synthetic_cases.csv",
]
# 与后端一致时可不改；否则请改成你的 host/用户/密码/库名
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "medicalinfo",
    "charset": "utf8mb4",
}

# 与 cases 表业务列一致；具体插入哪些列还要看表里是否存在对应字段
BASE_COLUMNS = [
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
    parser = argparse.ArgumentParser(description="将 CSV 行导入 cases 表（默认标记为合成数据）。")
    parser.add_argument("--csv", type=Path, default=None, help="要导入的 CSV 路径；省略则按默认候选文件查找")
    parser.add_argument(
        "--default-is-synthetic",
        type=int,
        default=1,
        help="CSV 无 is_synthetic 列时写入该值（0=真实，1=合成）",
    )
    return parser.parse_args()


def resolve_default_csv() -> Path:
    """返回 DEFAULT_CSV_CANDIDATES 中首个存在的路径；都不存在则返回首选路径（调用方需自行保证文件存在）。"""
    for candidate in DEFAULT_CSV_CANDIDATES:
        if candidate.exists():
            return candidate
    return DEFAULT_CSV_CANDIDATES[0]


def clean(value):
    """把 NaN/None 统一成 None，便于写入 SQL NULL。"""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def stringify_if_needed(column: str, value):
    if value is None:
        return None
    if column in {"age", "height", "weight", "time"}:
        return str(value)
    return value


def get_case_columns(cursor) -> set[str]:
    cursor.execute("SHOW COLUMNS FROM cases")
    return {row[0] for row in cursor.fetchall()}


def build_insert_columns(case_columns: set[str]) -> list[str]:
    """只插入表里真实存在的列；若表有 is_synthetic 则一并写入。"""
    insert_columns = [column for column in BASE_COLUMNS if column in case_columns]
    if "is_synthetic" in case_columns:
        insert_columns.append("is_synthetic")
    return insert_columns


def build_rows(df: pd.DataFrame, insert_columns: list[str], default_is_synthetic: int) -> list[tuple]:
    rows = []
    for _, row in df.iterrows():
        values = []
        for column in insert_columns:
            if column == "is_synthetic":
                value = row.get(column, default_is_synthetic)
                value = 1 if pd.isna(value) else int(value)
            else:
                value = stringify_if_needed(column, clean(row.get(column)))
            values.append(value)
        rows.append(tuple(values))
    return rows


def delete_existing_synthetic_rows(cursor, case_columns: set[str]) -> int:
    """清空历史合成行，防止多次导入重复；表无 is_synthetic 列则拒绝误删。"""
    if "is_synthetic" not in case_columns:
        raise RuntimeError("cases 表缺少 is_synthetic 列，为避免误删全部数据，已中止。")

    deleted_count = cursor.execute("DELETE FROM cases WHERE is_synthetic = 1")
    return int(deleted_count)


def reset_auto_increment_after_cleanup(cursor) -> int:
    """把自增主键重置到当前最大剩余 id 的下一个值。"""
    cursor.execute("SELECT COALESCE(MAX(id), 0) FROM cases")
    max_existing_id = int(cursor.fetchone()[0] or 0)
    next_id = max_existing_id + 1 if max_existing_id > 0 else 1
    cursor.execute(f"ALTER TABLE cases AUTO_INCREMENT = {next_id}")
    return next_id


def main() -> None:
    args = parse_args()
    csv_path = args.csv or resolve_default_csv()

    df = pd.read_csv(csv_path, encoding="utf-8-sig", engine="python", dtype={"time": str})
    print(f"CSV 路径：{csv_path}")
    print(f"待导入行数：{len(df)}")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        case_columns = get_case_columns(cursor)
        insert_columns = build_insert_columns(case_columns)
        rows = build_rows(df, insert_columns, args.default_is_synthetic)

        # 先删旧合成数据，再批量插入本次 CSV
        deleted_count = delete_existing_synthetic_rows(cursor, case_columns)
        print(f"已删除旧合成行数：{deleted_count}")
        next_auto_increment = reset_auto_increment_after_cleanup(cursor)
        print(f"已重置 AUTO_INCREMENT 为：{next_auto_increment}")
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        sql = f"INSERT INTO cases ({column_sql}) VALUES ({placeholders})"

        cursor.executemany(sql, rows)
        conn.commit()
        print(f"导入完成，本次插入行数：{len(rows)}")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
