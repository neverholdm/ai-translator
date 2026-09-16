from translate import TranslationError, translate
from translate_history import (
    HistoryError,
    clear_records,
    delete_record,
    export_records,
    load_records,
    save_translate_history,
    search_records,
)


def print_records(records):
    if not records:
        print("暂无翻译历史")
        return

    for record in records:
        print(
            f"ID：{record['id']}\n"
            f"时间：{record['time']}\n"
            f"源语言：{record['source_language']}\n"
            f"目标语言：{record['target_language']}\n"
            f"原文：{record['source']}\n"
            f"译文：{record['target']}\n"
            f"{'-' * 30}"
        )


def once_translate():
    source_language = input("请输入源语言\n")
    target_language = input("请输入目标语言\n")
    while True:
        text = input("请输入翻译内容\n")
        if text:
            break
        print("内容不能为空")
    try:
        result = translate(text, source_language, target_language)
    except TranslationError as exc:
        print(f"翻译失败：{exc}")
        return

    print(f"翻译结果：\n{result}")
    try:
        save_translate_history(source_language, target_language, text, result)
    except HistoryError as exc:
        print(f"翻译已完成，但历史记录未保存：{exc}")


def manage_history():
    while True:
        choice = input(
            """
========翻译历史========

1. 查看全部历史
2. 按关键词搜索
3. 删除单条记录
4. 清空历史
5. 导出 CSV
6. 返回上级菜单

"""
        )
        try:
            if choice == "1":
                print_records(load_records())
            elif choice == "2":
                print_records(search_records(input("请输入搜索关键词\n")))
            elif choice == "3":
                record_id = input("请输入要删除的记录 ID\n")
                if not record_id.isdigit() or int(record_id) <= 0:
                    print("记录 ID 必须是正整数")
                elif delete_record(int(record_id)):
                    print("记录已删除")
                else:
                    print("未找到该记录")
            elif choice == "4":
                if input("输入 yes 确认清空全部历史：\n").lower() == "yes":
                    print(f"已清空 {clear_records()} 条历史记录")
                else:
                    print("已取消清空")
            elif choice == "5":
                output_path = input("请输入 CSV 导出路径\n").strip()
                if not output_path:
                    print("导出路径不能为空")
                else:
                    print(f"已导出 {export_records(output_path)} 条历史记录")
            elif choice == "6":
                return
            else:
                print("请输入 1-6 之间的数字")
        except (HistoryError, ValueError, FileExistsError) as exc:
            print(f"历史记录操作失败：{exc}")


def main():
    while True:
        choice = input(
            """
========AI 翻译器========

1. 开始翻译
2. 管理历史记录
3. 退出

"""
        )
        if choice == "1":
            once_translate()
        elif choice == "2":
            manage_history()
        elif choice == "3":
            break
        else:
            print("请输入 1-3 之间的数字")


if __name__ == "__main__":
    main()
