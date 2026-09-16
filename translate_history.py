"""使用 SQLite 保存和查询翻译历史。"""

import csv
import os
import sqlite3
import sys
import tempfile
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path


def _default_database_path():
    if os.name == "nt":
        data_dir = Path(
            os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        )
    elif sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support"
    else:
        data_dir = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return data_dir / "AiTranslator" / "history.sqlite3"


# 测试可以将此路径替换为临时目录中的数据库。
DATABASE_PATH = _default_database_path()


class HistoryError(Exception):
    """历史记录操作失败。"""


@contextmanager
def _connection():
    """每次操作独立连接；异常时回滚，退出时关闭连接。"""
    database_path = Path(DATABASE_PATH)
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(database_path, timeout=5.0)) as connection:
            connection.row_factory = sqlite3.Row
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS translation_history (
                        id INTEGER PRIMARY KEY,
                        recorded_at TEXT NOT NULL,
                        source_language TEXT NOT NULL,
                        target_language TEXT NOT NULL,
                        source_text TEXT NOT NULL,
                        translated_text TEXT NOT NULL
                    )
                    """
                )
                yield connection
    except (OSError, sqlite3.Error) as exc:
        raise HistoryError("翻译历史数据库操作失败") from exc


def _record_from_row(row):
    return {
        "id": row["id"],
        "time": row["recorded_at"],
        "source_language": row["source_language"],
        "target_language": row["target_language"],
        "source": row["source_text"],
        "target": row["translated_text"],
    }


def save_record(source_language, target_language, text, result, time_str=None):
    """保存一条翻译记录，返回时间字符串，供现有 GUI 使用。"""
    if time_str is None:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO translation_history
                (recorded_at, source_language, target_language, source_text, translated_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (time_str, source_language, target_language, text, result),
        )
    return time_str


def save_translate_history(source_language, target_language, text, result):
    """保留命令行版本现有的保存入口和参数。"""
    save_record(source_language, target_language, text, result)


def load_records():
    """按写入顺序读取全部记录，返回兼容 GUI 的字典列表。"""
    with _connection() as connection:
        rows = connection.execute(
            "SELECT * FROM translation_history ORDER BY id"
        ).fetchall()
    return [_record_from_row(row) for row in rows]


def search_records(keyword):
    """在语言、原文和译文中搜索字面关键词；空关键词返回全部记录。"""
    if not isinstance(keyword, str):
        raise ValueError("搜索关键词必须是字符串")
    keyword = keyword.strip()
    if not keyword:
        return load_records()

    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM translation_history
            WHERE source_language LIKE ? ESCAPE '\\'
               OR target_language LIKE ? ESCAPE '\\'
               OR source_text LIKE ? ESCAPE '\\'
               OR translated_text LIKE ? ESCAPE '\\'
            ORDER BY id
            """,
            (pattern,) * 4,
        ).fetchall()
    return [_record_from_row(row) for row in rows]


def delete_record(record_id):
    """按稳定的记录 ID 删除单条记录，返回是否找到该记录。"""
    if type(record_id) is not int or record_id <= 0:
        raise ValueError("记录 ID 必须是正整数")
    with _connection() as connection:
        cursor = connection.execute(
            "DELETE FROM translation_history WHERE id = ?", (record_id,)
        )
        return cursor.rowcount == 1


def clear_records():
    """清空历史记录，返回删除条数。"""
    with _connection() as connection:
        cursor = connection.execute("DELETE FROM translation_history")
        return cursor.rowcount


def export_records(output_path):
    """导出全部记录为 UTF-8 BOM CSV；目标文件已存在时拒绝覆盖。"""
    records = load_records()
    output_path = Path(output_path)
    temporary_path = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=output_path.parent,
            prefix=".history-export-",
            suffix=".csv",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = csv.writer(output)
            writer.writerow(("id", "time", "source_language", "target_language", "source", "target"))
            for record in records:
                writer.writerow(
                    (
                        record["id"],
                        record["time"],
                        record["source_language"],
                        record["target_language"],
                        record["source"],
                        record["target"],
                    )
                )
        os.link(temporary_path, output_path)
    except FileExistsError:
        raise
    except OSError as exc:
        raise HistoryError("导出翻译历史失败") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return len(records)


def show_translate_history():
    """以原有文本布局显示 SQLite 中的历史记录。"""
    records = load_records()
    if not records:
        print("暂无翻译历史")
        return

    for record in records:
        print(
            f"时间：{record['time']}\n"
            f"源语言：{record['source_language']}\n"
            f"目标语言：{record['target_language']}\n"
            f"原文：{record['source']}\n"
            f"译文：{record['target']}\n"
            f"{'-' * 30}"
        )


if __name__ == "__main__":
    show_translate_history()
