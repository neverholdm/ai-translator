import tkinter as tk
from tkinter import ttk

from translate import TranslationError, translate
from translate_history import load_records, save_record


def main():
    window = tk.Tk()

    window.title("AI 翻译器")
    window.geometry("600x600")

    # 源语言
    source_label = tk.Label(window, text="源语言：")
    source_label.pack()

    source_language = ttk.Combobox(
        window,
        values=["中文", "英语", "日语", "韩语"],
        state="readonly"
    )
    source_language.set("中文")
    source_language.pack()

    # 输入内容
    input_label = tk.Label(window, text="请输入翻译内容")
    input_label.pack()

    source_text = tk.Text(window, height=8, width=60)
    source_text.pack()

    # 目标语言
    target_label = tk.Label(window, text="目标语言：")
    target_label.pack()

    target_language = ttk.Combobox(
        window,
        values=["中文", "英语", "日语", "韩语"],
        state="readonly"
    )
    target_language.set("英语")
    target_language.pack()

    # 翻译结果
    result_label = tk.Label(window, text="翻译结果：")
    result_label.pack()

    result_text = tk.Text(window, height=8, width=60)
    result_text.pack()

    # ========== 翻译历史面板 ==========
    history_label = tk.Label(window, text="📜 翻译历史记录（只读）")
    history_label.pack(pady=(10, 0))

    history_frame = tk.Frame(window)
    history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    history_scroll = tk.Scrollbar(history_frame)
    history_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # 历史文本框，只读
    history_text = tk.Text(
        history_frame,
        height=8,
        yscrollcommand=history_scroll.set
    )
    history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    history_scroll.config(command=history_text.yview)
    history_text.config(state=tk.DISABLED)  # 设置只读，不能手动编辑

    # 是否已加载过历史（只有点击“查看历史”后才展示记录）
    history_loaded = False
    PLACEHOLDER = "点击「查看历史」按钮加载历史记录"

    # 启动时面板只显示提示，不读取历史文件
    history_text.config(state=tk.NORMAL)
    history_text.insert(tk.END, PLACEHOLDER)
    history_text.config(state=tk.DISABLED)

    # 加载历史记录函数（点击“查看历史”按钮时调用）
    def load_history():
        nonlocal history_loaded
        records = load_records()  # 调用 translate_history.py 的读取函数
        history_text.config(state=tk.NORMAL)  # 临时开启编辑，写入内容
        history_text.delete("1.0", tk.END)
        if not records:
            history_text.insert(tk.END, "暂无翻译历史")
        for item in records:
            line = (
                f"【{item['time']}】"
                f"{item['source_language']} → {item['target_language']}\n"
                f"原文：{item['source']}\n"
                f"译文：{item['target']}\n"
                f"---------\n"
            )
            history_text.insert(tk.END, line)
        history_text.config(state=tk.DISABLED)  # 改回只读
        history_text.see(tk.END)  # 滚动到最底部
        history_loaded = True

    # 添加一条新记录到界面
    def add_history_to_view(time_str, src_lang, tgt_lang, src, tgt):
        history_text.config(state=tk.NORMAL)
        if history_text.get("1.0", tk.END).strip() in (
            "暂无翻译历史",
            PLACEHOLDER,
        ):
            history_text.delete("1.0", tk.END)
        line = (
            f"【{time_str}】{src_lang} → {tgt_lang}\n"
            f"原文：{src}\n"
            f"译文：{tgt}\n"
            f"---------\n"
        )
        history_text.insert(tk.END, line)
        history_text.config(state=tk.DISABLED)
        history_text.see(tk.END)  # 自动滚动到最新记录

    def do_translate():
        text = source_text.get("1.0", "end-1c")
        try:
            result = translate(
                text,
                source_language.get(),
                target_language.get(),
            )
        except TranslationError as exc:
            result_text.delete("1.0", tk.END)
            result_text.insert("1.0", f"翻译失败：{exc}")
            return

        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", result)

        # 翻译成功后写入历史文件；仅在已加载历史面板时同步刷新界面
        time_str = save_record(
            source_language.get(),
            target_language.get(),
            text,
            result,
        )
        if history_loaded:
            add_history_to_view(
                time_str,
                source_language.get(),
                target_language.get(),
                text,
                result,
            )

    # 按钮区：开始翻译 / 查看历史
    button_frame = tk.Frame(window)
    button_frame.pack(pady=5)

    translate_button = tk.Button(
        button_frame,
        text="开始翻译",
        command=do_translate
    )
    translate_button.pack(side=tk.LEFT, padx=5)

    history_button = tk.Button(
        button_frame,
        text="查看历史",
        command=load_history
    )
    history_button.pack(side=tk.LEFT, padx=5)

    window.mainloop()


if __name__ == "__main__":
    main()
