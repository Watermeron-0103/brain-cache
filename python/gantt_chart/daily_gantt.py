from pathlib import Path
from datetime import datetime, timedelta, time, date
import datetime as dt
import pandas as pd
import xlsxwriter

BASE_DATE = date(2025, 12, 18)  # 一日ガントの対象日（固定したい日）

SRC_PATH = Path("src/daily_gantt.xlsx")
OUT_PATH = Path("out/一日ガント_スケジュールビュー.xlsx")
SHEET = "ガント"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ===== 1) 読む（列がなくても落ちない＆時刻だけを日付付きにする）=====
df = pd.read_excel(SRC_PATH, sheet_name="Sheet1")
df.columns = df.columns.astype(str).str.strip()

# 列名ゆれ吸収（Excelが「タスク」列の場合）
if "作業工程" not in df.columns and "タスク" in df.columns:
    df = df.rename(columns={"タスク": "作業工程"})

# 必須列の補完
if "作業工程" not in df.columns:
    df["作業工程"] = ""

if "担当" not in df.columns:
    df["担当"] = ""

if "No." not in df.columns:
    df["No."] = range(1, len(df) + 1)

def coerce_datetime(series, base_date: date):
    """Excelの値（datetime / time / str）を datetime に統一する。
    timeだけなら base_date と結合する。
    """
    def conv(x):
        if pd.isna(x):
            return pd.NaT
        if isinstance(x, dt.datetime):
            return x
        if isinstance(x, dt.time):
            return dt.datetime.combine(base_date, x)
        return pd.to_datetime(x, errors="coerce")
    return series.apply(conv)

for c in ["開始", "終了", "実績開始", "実績終了"]:
    if c in df.columns:
        df[c] = coerce_datetime(df[c], BASE_DATE)

tasks = df[df["開始"].notna() & df["終了"].notna()].copy()
if tasks.empty:
    # デバッグしやすいように、列名も出す
    raise SystemExit(f"開始/終了が入っている行がありません。列名={list(df.columns)}")

for c in ["実績開始", "実績終了"]:
    if c not in tasks.columns:
        tasks[c] = pd.NaT

tasks = tasks.sort_values(["No.", "開始"]).reset_index(drop=True)

# ===== 2) 横軸（30分刻みの時刻）=====
base_date = BASE_DATE  # ← ここを固定（変な日付混入でもズレない）

start_t = time(8, 0)    # 表示開始時刻
end_t   = time(18, 0)   # 表示終了時刻
step_min = 30

def combine_dt(t: time) -> datetime:
    return datetime.combine(base_date, t)

slots = []
cur = combine_dt(start_t)
end_dt = combine_dt(end_t)
while cur <= end_dt:
    slots.append(cur)
    cur += timedelta(minutes=step_min)

# ===== 3) xlsxwriter で書く =====
wb = xlsxwriter.Workbook(str(OUT_PATH))
ws = wb.add_worksheet(SHEET)

# formats
header_fmt = wb.add_format({"bold": True, "align": "center", "valign": "vcenter", "border": 1, "bg_color": "#D9E1F2"})
cell_fmt   = wb.add_format({"border": 1})
bg_off_fmt = wb.add_format({"border": 1, "bg_color": "#F2F2F2"})  # 休憩帯など
plan_fmt   = wb.add_format({"border": 1, "bg_color": "#9DC3E6"})  # 計画（青）
actual_fmt = wb.add_format({"border": 1, "bg_color": "#A9D08E"})  # 実績（緑）
delay_fmt  = wb.add_format({"border": 1, "bg_color": "#F4B084"})  # 遅延（橙）

# column widths
ws.set_column(0, 0, 6)   # No.
ws.set_column(1, 1, 30)  # 作業工程
ws.set_column(2, 2, 10)  # 担当
ws.set_column(3, 3 + len(slots) - 1, 3)  # time columns

row_time = 0
row_sub  = 1
start_row = 2
col_offset = 3

# left headers
ws.merge_range(row_time, 0, row_sub, 0, "No.", header_fmt)
ws.merge_range(row_time, 1, row_sub, 1, "作業工程", header_fmt)
ws.merge_range(row_time, 2, row_sub, 2, "担当", header_fmt)

# top time header
ws.merge_range(
    row_time, col_offset, row_time, col_offset + len(slots) - 1,
    f"{base_date}（{step_min}分刻み）",
    header_fmt
)

for i, d in enumerate(slots):
    ws.write(row_sub, col_offset + i, d.strftime("%H:%M"), header_fmt)

# background（例：12:00-13:00 をグレーアウト）
def is_break(s: datetime) -> bool:
    return time(12, 0) <= s.time() < time(13, 0)

for r in range(start_row, start_row + len(tasks)):
    for i, s in enumerate(slots):
        ws.write_blank(r, col_offset + i, None, bg_off_fmt if is_break(s) else cell_fmt)

# ===== バー判定：スロット時間帯と予定が「少しでも重なれば塗る」 =====
def overlaps(range_s: datetime, range_e: datetime, slot_s: datetime, slot_e: datetime) -> bool:
    # [range_s, range_e) と [slot_s, slot_e) が重なるか
    return (range_s < slot_e) and (range_e > slot_s)

for r, (_, row) in enumerate(tasks.iterrows(), start=start_row):
    ws.write(r, 0, row.get("No.", ""), cell_fmt)
    ws.write(r, 1, str(row.get("作業工程", "")), cell_fmt)
    ws.write(r, 2, "" if pd.isna(row.get("担当")) else str(row.get("担当")), cell_fmt)

    plan_s = row["開始"]
    plan_e = row["終了"]

    for i, slot_s in enumerate(slots):
        slot_e = slot_s + timedelta(minutes=step_min)
        if overlaps(plan_s, plan_e, slot_s, slot_e):
            ws.write_blank(r, col_offset + i, None, plan_fmt)

    if pd.notna(row["実績開始"]) and pd.notna(row["実績終了"]):
        a_s = row["実績開始"]
        a_e = row["実績終了"]
        fmt = delay_fmt if a_e > plan_e else actual_fmt

        for i, slot_s in enumerate(slots):
            slot_e = slot_s + timedelta(minutes=step_min)
            if overlaps(a_s, a_e, slot_s, slot_e):
                ws.write_blank(r, col_offset + i, None, fmt)

wb.close()
print(f"作成しました → {OUT_PATH}")
