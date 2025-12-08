from datetime import date, timedelta
import math
from pathlib import Path
import xlsxwriter


# ===== パラメータ（ここだけいじれば別案件にも使い回せる）=====
TOTAL_ITEMS = 77                 # 改訂対象の件数
PER_WEEK = 10                    # 1週間でさばく件数
START_DATE = date(2025, 12, 8)   # 着手開始の月曜日

OUT_PATH = Path("out/先端キャップ_ガントチャート.xlsx")
SHEET_NAME = "スケジュール"
# ============================================================

# 何週必要か
weeks = math.ceil(TOTAL_ITEMS / PER_WEEK)

# ガントの横軸（日付）を決める
start = START_DATE
last_week_start = START_DATE + timedelta(weeks=weeks - 1)
end = last_week_start + timedelta(days=4)   # 各週はとりあえず 月〜金 で確保

days = []
cur = start
while cur <= end:
    days.append(cur)
    cur += timedelta(days=1)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

workbook = xlsxwriter.Workbook(str(OUT_PATH))
ws = workbook.add_worksheet(SHEET_NAME)

# ---- 書式（フォーマット）定義 ----
header_fmt = workbook.add_format({
    "bold": True, "align": "center", "valign": "vcenter",
    "border": 1, "bg_color": "#D9E1F2"
})
dow_fmt = workbook.add_format({
    "align": "center", "border": 1
})
weekday_cell_fmt = workbook.add_format({"border": 1})
weekend_cell_fmt = workbook.add_format({"border": 1, "bg_color": "#EEEEEE"})

# マイルストーン用の色（週ごとにローテーション）
bar_formats = [
    workbook.add_format({"border": 1, "bg_color": "#F8CBAD"}),  # ピンク
    workbook.add_format({"border": 1, "bg_color": "#FFE699"}),  # 黄色
    workbook.add_format({"border": 1, "bg_color": "#C9DAF8"}),  # 青
]

# 列幅調整
ws.set_column(0, 0, 16)  # 作業工程
ws.set_column(1, 1, 8)   # 担当
ws.set_column(2, 2, 10)  # ステータス
ws.set_column(3, 3 + len(days) - 1, 3)  # 日付列

# ---- ヘッダ部（左3列）----
row_month = 0
row_day = 1
row_dow = 2
col_offset = 3

ws.merge_range(row_month, 0, row_dow, 0, "作業工程", header_fmt)
ws.merge_range(row_month, 1, row_dow, 1, "担当", header_fmt)
ws.merge_range(row_month, 2, row_dow, 2, "ステータス", header_fmt)

# ---- ヘッダ部（日付側）月ごとにセル結合 ----
idx = 0
while idx < len(days):
    m = days[idx].month
    start_col = col_offset + idx
    j = idx
    while j < len(days) and days[j].month == m:
        j += 1
    end_col = col_offset + j - 1
    ws.merge_range(row_month, start_col, row_month, end_col, f"{m}月", header_fmt)
    idx = j

# 日付・曜日を書き込む
weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]

for i, d in enumerate(days):
    col = col_offset + i
    ws.write(row_day, col, d.day, header_fmt)                     # 日にち
    ws.write(row_dow, col, weekday_labels[d.weekday()], dow_fmt)  # 曜日

# ボディ部の土日をグレーに塗っておく（空のマス）
max_body_rows = 3 + weeks + 5  # 余裕をもって少し多めに
for r in range(3, max_body_rows):
    for i, d in enumerate(days):
        col = col_offset + i
        if d.weekday() >= 5:  # 土日
            ws.write_blank(r, col, None, weekend_cell_fmt)
        else:
            ws.write_blank(r, col, None, weekday_cell_fmt)

# ---- マイルストーン行を描く（横の色付きバー）----
start_row = 3

for i in range(weeks):
    row = start_row + i

    # 左側の情報
    ws.write(row, 0, f"マイルストーン{i + 1}", weekday_cell_fmt)
    ws.write(row, 1, "", weekday_cell_fmt)            # 担当は手入力用
    ws.write(row, 2, "未着手", weekday_cell_fmt)      # ステータス初期値

    # この週の期間（とりあえず 月〜金）
    week_start = START_DATE + timedelta(weeks=i)
    week_end = week_start + timedelta(days=4)

    bar_fmt = bar_formats[i % len(bar_formats)]

    for j, d in enumerate(days):
        # その週の営業日だけ色を塗る
        if week_start <= d <= week_end and d.weekday() < 5:
            col = col_offset + j
            ws.write_blank(row, col, None, bar_fmt)

workbook.close()

print(f"ガントチャートを作成しました → {OUT_PATH}")
