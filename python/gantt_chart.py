from pathlib import Path
from datetime import timedelta
import pandas as pd
import xlsxwriter

# ===== パス設定 =====
SRC_PATH = Path("src/治具検討_ガントチャート.xlsx")
OUT_PATH = Path("out/治具検討_ガントチャート_スケジュールビュー.xlsx")
SHEET_NAME = "ガント"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ===== 1) 元データ読込 =====
df = pd.read_excel(SRC_PATH, sheet_name="Sheet1", parse_dates=["開始日", "終了日"])

# 開始日・終了日が入っている行だけタスクとして使う
tasks = df[df["開始日"].notna() & df["終了日"].notna()].copy()

if tasks.empty:
    raise SystemExit("Sheet1 に開始日と終了日が入っている行がありません。")

# No. → 作業工程 → 日付 で並べると見やすい
tasks = tasks.sort_values(["No.", "開始日"]).reset_index(drop=True)

start_date = tasks["開始日"].min().date()
end_date   = tasks["終了日"].max().date()

# ===== 2) ガントの横軸（日付リスト） =====
days = []
cur = start_date
while cur <= end_date:
    days.append(cur)
    cur += timedelta(days=1)

# ===== 3) xlsxwriter でレイアウト作成 =====
workbook = xlsxwriter.Workbook(str(OUT_PATH))
ws = workbook.add_worksheet(SHEET_NAME)

# ---- フォーマット定義 ----
header_fmt = workbook.add_format({
    "bold": True, "align": "center", "valign": "vcenter",
    "border": 1, "bg_color": "#D9E1F2"
})
dow_fmt = workbook.add_format({
    "align": "center", "border": 1
})
weekday_cell_fmt = workbook.add_format({"border": 1})
weekend_cell_fmt = workbook.add_format({"border": 1, "bg_color": "#EEEEEE"})
bar_todo_fmt = workbook.add_format({"border": 1, "bg_color": "#9DC3E6"})  # 未完了
bar_done_fmt = workbook.add_format({"border": 1, "bg_color": "#A9D08E"})  # 完了

# ---- 列幅 ----
ws.set_column(0, 0, 6)   # No.
ws.set_column(1, 1, 30)  # 作業工程
ws.set_column(2, 2, 8)   # 担当
ws.set_column(3, 3, 10)  # ステータス
ws.set_column(4, 4 + len(days) - 1, 3)  # 日付列

# ---- ヘッダ行（上3段）----
row_month = 0
row_day = 1
row_dow = 2
col_offset = 4  # 日付のスタート列

# 左4列のヘッダ
ws.merge_range(row_month, 0, row_dow, 0, "No.", header_fmt)
ws.merge_range(row_month, 1, row_dow, 1, "作業工程", header_fmt)
ws.merge_range(row_month, 2, row_dow, 2, "担当", header_fmt)
ws.merge_range(row_month, 3, row_dow, 3, "ステータス", header_fmt)

# 月ごとのヘッダ（例：25年10月）
idx = 0
while idx < len(days):
    m = days[idx].month
    y = days[idx].year
    start_col = col_offset + idx
    j = idx
    while j < len(days) and days[j].month == m and days[j].year == y:
        j += 1
    end_col = col_offset + j - 1
    ws.merge_range(
        row_month, start_col, row_month, end_col,
        f"{y % 100}年{m}月",  # 25年10月 みたいな表記
        header_fmt,
    )
    idx = j

# 日付＆曜日
weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]
for i, d in enumerate(days):
    col = col_offset + i
    ws.write(row_day, col, d.day, header_fmt)
    ws.write(row_dow, col, weekday_labels[d.weekday()], dow_fmt)

# ---- ボディ部：まず背景（土日グレー）だけ作る ----
start_row = 3
max_body_rows = start_row + len(tasks)

for r in range(start_row, max_body_rows):
    for i, d in enumerate(days):
        col = col_offset + i
        if d.weekday() >= 5:  # 土日
            ws.write_blank(r, col, None, weekend_cell_fmt)
        else:
            ws.write_blank(r, col, None, weekday_cell_fmt)

# ---- 各タスク行＋バー塗り ----
for row_idx, (_, row) in enumerate(tasks.iterrows(), start=start_row):
    # No. 列はいったん空で枠だけ（あとでまとめて結合）
    ws.write_blank(row_idx, 0, None, weekday_cell_fmt)

    # 左側3列
    ws.write(row_idx, 1, str(row["作業工程"]), weekday_cell_fmt)
    ws.write(row_idx, 2, "" if pd.isna(row["担当"]) else str(row["担当"]), weekday_cell_fmt)
    status = "" if pd.isna(row["ステータス"]) else str(row["ステータス"])
    ws.write(row_idx, 3, status or "未着手", weekday_cell_fmt)

    # バーの塗りつぶし
    s = row["開始日"].date()
    e = row["終了日"].date()
    fmt = bar_done_fmt if "完" in status else bar_todo_fmt

    for i, d in enumerate(days):
        if s <= d <= e and d.weekday() < 5:
            col = col_offset + i
            ws.write_blank(row_idx, col, None, fmt)

# ---- No. 列を同じ番号ごとに縦結合 ----
prev_no = None
block_start = None
prev_row = None
no_col = 0

for row_idx, (_, row) in enumerate(tasks.iterrows(), start=start_row):
    no_val = row["No."]
    # NaN のときは None 扱い
    if pd.isna(no_val):
        no_val = None

    if no_val != prev_no:
        # 1つ前のブロックを閉じる
        if prev_no is not None and block_start is not None:
            if block_start == prev_row:
                ws.write(block_start, no_col, prev_no, weekday_cell_fmt)
            else:
                ws.merge_range(block_start, no_col, prev_row, no_col, prev_no, weekday_cell_fmt)

        # 新しいブロック開始
        prev_no = no_val
        block_start = row_idx if no_val is not None else None

    prev_row = row_idx

# ループ最後のブロックを閉じる
if prev_no is not None and block_start is not None:
    if block_start == prev_row:
        ws.write(block_start, no_col, prev_no, weekday_cell_fmt)
    else:
        ws.merge_range(block_start, no_col, prev_row, no_col, prev_no, weekday_cell_fmt)

workbook.close()

print(f"ガントチャートを作成しました → {OUT_PATH}")
