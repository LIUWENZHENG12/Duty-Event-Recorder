import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import csv

# ---------- AI 嚴重度判斷（可替換） ----------
def ai_severity(text):
    rules = {
        "高": ["火災", "冒煙", "斷電", "跳電", "警報", "漏水"],
        "中": ["異常", "不穩", "延遲", "故障"]
    }
    for level, keywords in rules.items():
        for k in keywords:
            if k in text:
                return level
    return "低"

# ---------- 資料庫 ----------
conn = sqlite3.connect("duty_log.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    system TEXT,
    description TEXT,
    severity TEXT
)
""")
conn.commit()

# ---------- GUI ----------
root = tk.Tk()
root.title("中控室值班事件紀錄系統")
root.geometry("700x520")

# 系統選擇
tk.Label(root, text="系統類型").pack()
system_var = tk.StringVar(value="消防")
tk.OptionMenu(
    root, system_var,
    "消防", "電力", "弱電", "空調", "給排水", "其他"
).pack()

# 描述
tk.Label(root, text="事件描述").pack()
desc_entry = tk.Text(root, height=4)
desc_entry.pack(fill="x", padx=10)

# 新增事件
def add_event():
    desc = desc_entry.get("1.0", tk.END).strip()
    if not desc:
        messagebox.showwarning("錯誤", "請輸入事件描述")
        return

    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    severity = ai_severity(desc)

    cursor.execute(
        "INSERT INTO logs (time, system, description, severity) VALUES (?, ?, ?, ?)",
        (time_now, system_var.get(), desc, severity)
    )
    conn.commit()

    desc_entry.delete("1.0", tk.END)
    refresh_list()

tk.Button(root, text="新增事件", command=add_event).pack(pady=5)

# ---------- 搜尋 / 篩選 ----------
filter_frame = tk.Frame(root)
filter_frame.pack()

severity_filter = tk.StringVar(value="全部")
tk.OptionMenu(filter_frame, severity_filter, "全部", "高", "中", "低").pack(side="left")

search_entry = tk.Entry(filter_frame)
search_entry.pack(side="left", padx=5)
search_entry.insert(0, "關鍵字搜尋")

def refresh_list():
    listbox.delete(0, tk.END)

    sev = severity_filter.get()
    keyword = search_entry.get()

    query = "SELECT time, system, severity, description FROM logs WHERE 1=1"
    params = []

    if sev != "全部":
        query += " AND severity=?"
        params.append(sev)

    if keyword and keyword != "關鍵字搜尋":
        query += " AND description LIKE ?"
        params.append(f"%{keyword}%")

    query += " ORDER BY id DESC"

    for row in cursor.execute(query, params):
        listbox.insert(
            tk.END,
            f"[{row[0]}] [{row[1]}] 嚴重度:{row[2]} | {row[3]}"
        )

tk.Button(filter_frame, text="套用", command=refresh_list).pack(side="left")

# ---------- 清單 ----------
listbox = tk.Listbox(root, width=95, height=15)
listbox.pack(pady=10)

# ---------- 匯出 CSV ----------
def export_csv():
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )
    if not path:
        return

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["時間", "系統", "嚴重度", "描述"])
        for row in cursor.execute(
            "SELECT time, system, severity, description FROM logs ORDER BY id DESC"
        ):
            writer.writerow(row)

    messagebox.showinfo("完成", "CSV 匯出成功")

tk.Button(root, text="匯出 CSV", command=export_csv).pack(pady=5)

refresh_list()
root.mainloop()
conn.close()
