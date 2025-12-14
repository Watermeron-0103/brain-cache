from pathlib import Path
from datetime import timedelta
import pandas as pd
import xlsxwriter

# ===== パス設定 =====
SRC_PATH = Path("src/治具検討_gantt_chart.xlsx")
OUT_PATH = Path("out/治具検討_ガントチャート_スケジュールビュー.xlsx")
SHEET_NAME = "ガント"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ===== 1) 元データ読込 =====
# ★変更: 実績開始日/実績終了日 も parse_dates に追加（列が無い場合は後で吸収する）
df = pd.read_excel(
    SRC_PATH,
    sheet_name="Sheet1",
    parse_dates=["開始日", "終了日", "実績開始日", "実績終了日"],
)

# 開始日・終了日が入っている行だけタスクとして使う
tasks = df[df["開始日"].notna() & df["終了日"].notna()].copy()

if tasks.empty:
    raise SystemExit("Sheet1 に開始日と終了日が入っている行がありません。")

# 列が無いExcelでも落ちないように保険（空列を作る）
for col in ["実績開始日", "実績終了日"]:
    if col not in tasks.columns:
        tasks[col] = pd.NaT

# No. → 作業工程 → 日付 で並べると見やすい
tasks = tasks.sort_values(["No.", "開始日"]).reset_index(drop=True)

# ★変更: 横軸は「計画」だけじゃなく「実績」も含めて広げる（実績が後ろに伸びても表示される）
min_date = tasks["開始日"].min()
max_date = tasks["終了日"].max()

if tasks["実績開始日"].notna().any():
    min_date = min(min_date, tasks["実績開始日"].min())
if tasks["実績終了日"].notna().any():
    max_date = max(max_date, tasks["実績終了日"].max())

start_date = min_date.date()
end_date = max_date.date()

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
dow_fmt = workbook.add_format({"align": "center", "border": 1})
weekday_cell_fmt = workbook.add_format({"border": 1})
weekend_cell_fmt = workbook.add_format({"border": 1, "bg_color": "#EEEEEE"})

# ★変更: バーの意味を分離（計画/実績/遅延）
bar_plan_fmt = workbook.add_format({"border": 1, "bg_color": "#9DC3E6"})   # 計画（青）
bar_actual_fmt = workbook.add_format({"border": 1, "bg_color": "#A9D08E"}) # 実績（緑）
bar_delay_fmt = workbook.add_format({"border": 1, "bg_color": "#F4B084"})  # 遅延（オレンジ）

# ---- 列幅 ----
ws.set_column(0, 0, 6)   # No.
ws.set_column(1, 1, 30)  # 作業工程
ws.set_column(2, 2, 8)   # 担当
ws.set_column(3, 3, 10)  # ステータス（※使わないなら後で消してOK）
ws.set_column(4, 4 + len(days) - 1, 3)  # 日付列

# ---- ヘッダ行（上3段）----
row_month = 0
row_day = 1
row_dow = 2
col_offset = 4  # 日付のスタート列

ws.merge_range(row_month, 0, row_dow, 0, "No.", header_fmt)
ws.merge_range(row_month, 1, row_dow, 1, "作業工程", header_fmt)
ws.merge_range(row_month, 2, row_dow, 2, "担当", header_fmt)
ws.merge_range(row_month, 3, row_dow, 3, "ステータス", header_fmt)

# 月ごとのヘッダ
idx = 0
while idx < len(days):
    m = days[idx].month
    y = days[idx].year
    start_col = col_offset + idx
    j = idx
    while j < len(days) and days[j].month == m and days[j].year == y:
        j += 1
    end_col = col_offset + j - 1
    ws.merge_range(row_month, start_col, row_month, end_col, f"{y % 100}年{m}月", header_fmt)
    idx = j

weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]
for i, d in enumerate(days):
    col = col_offset + i
    ws.write(row_day, col, d.day, header_fmt)
    ws.write(row_dow, col, weekday_labels[d.weekday()], dow_fmt)

# ---- 背景（土日グレー） ----
start_row = 3
max_body_rows = start_row + len(tasks)

for r in range(start_row, max_body_rows):
    for i, d in enumerate(days):
        col = col_offset + i
        ws.write_blank(r, col, None, weekend_cell_fmt if d.weekday() >= 5 else weekday_cell_fmt)

# ---- 各タスク行＋バー塗り ----
for row_idx, (_, row) in enumerate(tasks.iterrows(), start=start_row):
    ws.write_blank(row_idx, 0, None, weekday_cell_fmt)

    ws.write(row_idx, 1, str(row["作業工程"]), weekday_cell_fmt)
    ws.write(row_idx, 2, "" if pd.isna(row["担当"]) else str(row["担当"]), weekday_cell_fmt)

    status = "" if pd.isna(row.get("ステータス")) else str(row.get("ステータス"))
    ws.write(row_idx, 3, status or "未着手", weekday_cell_fmt)

    # ① 計画バー（常に青で描く：計画は消さない）
    plan_s = row["開始日"].date()
    plan_e = row["終了日"].date()
    for i, d in enumerate(days):
        if plan_s <= d <= plan_e and d.weekday() < 5:
            ws.write_blank(row_idx, col_offset + i, None, bar_plan_fmt)

    # ② 実績バー（あれば上に重ねる：緑 or 遅延オレンジ）
    if pd.notna(row["実績開始日"]) and pd.notna(row["実績終了日"]):
        actual_s = row["実績開始日"].date()
        actual_e = row["実績終了日"].date()

        fmt = bar_delay_fmt if actual_e > plan_e else bar_actual_fmt

        for i, d in enumerate(days):
            if actual_s <= d <= actual_e and d.weekday() < 5:
                ws.write_blank(row_idx, col_offset + i, None, fmt)

# ---- No. 列を同じ番号ごとに縦結合 ----
prev_no = None
block_start = None
prev_row = None
no_col = 0

for row_idx, (_, row) in enumerate(tasks.iterrows(), start=start_row):
    no_val = None if pd.isna(row["No."]) else row["No."]

    if no_val != prev_no:
        if prev_no is not None and block_start is not None:
            if block_start == prev_row:
                ws.write(block_start, no_col, prev_no, weekday_cell_fmt)
            else:
                ws.merge_range(block_start, no_col, prev_row, no_col, prev_no, weekday_cell_fmt)

        prev_no = no_val
        block_start = row_idx if no_val is not None else None

    prev_row = row_idx

if prev_no is not None and block_start is not None:
    if block_start == prev_row:
        ws.write(block_start, no_col, prev_no, weekday_cell_fmt)
    else:
        ws.merge_range(block_start, no_col, prev_row, no_col, prev_no, weekday_cell_fmt)

workbook.close()
print(f"ガントチャートを作成しました → {OUT_PATH}")
