import os
import re
from datetime import datetime


HISTORY_FILE = "translation_history.txt"
SEPARATOR = "-" * 30

# 字段前缀与 load_records 返回字典键名的映射
FIELD_PREFIXES = {
    "时间：": "time",
    "源语言：": "source_language",
    "目标语言：": "target_language",
    "原文：": "source",
    "译文：": "target",
}


def save_record(source_language, target_language, text, result, time_str=None):
    """保存一条翻译记录，返回该条记录的时间字符串。"""
    if time_str is None:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"时间：{time_str}\n"
            f"源语言：{source_language}\n"
            f"目标语言：{target_language}\n"
            f"原文：{text}\n"
            f"译文：{result}\n"
            f"{SEPARATOR}\n"
        )

    return time_str


def save_translate_history(source_language, target_language, text, result):
    """保存翻译历史（保留给命令行版本使用）。"""
    save_record(source_language, target_language, text, result)


def load_records():
    """读取全部翻译记录。

    返回列表，每项为字典，包含：
    time、source_language、target_language、source、target。
    旧版本写入的记录没有时间字段，time 显示为“未知时间”。
    """
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    records = []
    # 按仅由短横线组成的分隔线切分为一条条记录
    blocks = re.split(r"^-{10,}\s*$", content, flags=re.MULTILINE)

    for block in blocks:
        record = {
            "time": "未知时间",
            "source_language": "",
            "target_language": "",
            "source": "",
            "target": "",
        }
        current_key = None

        for line in block.splitlines():
            matched_key = None
            for prefix, key in FIELD_PREFIXES.items():
                if line.startswith(prefix):
                    matched_key = key
                    record[key] = line[len(prefix):]
                    break

            if matched_key is not None:
                current_key = matched_key
            elif current_key is not None:
                # 原文/译文可能跨多行
                record[current_key] += "\n" + line

        # 跳过空块和没有任何实质内容的块
        if record["source"].strip() or record["target"].strip():
            records.append(record)

    return records


def show_translate_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if content.strip():
                print(content)
            else:
                print("暂无翻译历史")
    except OSError:
        print("暂无翻译历史")


if __name__ == "__main__":
    show_translate_history()
#test