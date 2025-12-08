from datetime import date, timedelta
import math
from pathlib import Path

import pandas as pd


# ===== パラメータ（ここだけいじれば別案件にも使える） =====
TOTAL_ITEMS = 77                 # 改訂対象の件数（モンスター総数）
PER_WEEK = 10                    # 1週間でさばく件数（討伐数）
START_DATE = date(2025, 12, 8)   # 着手開始の月曜日

OUT_PATH = Path("out/先端キャップ_改訂スケジュール.xlsx")
SHEET_NAME = "スケジュール"
# =======================================================


# --- 週ごとの予定表をつくる（看板テキスト生成パート） ---
weeks = math.ceil(TOTAL_ITEMS / PER_WEEK)
remain = TOTAL_ITEMS

rows = []

for i in range(weeks):
    week_no = i + 1
    ws = START_DATE + timedelta(weeks=i)   # 週開始（月）
    we = ws + timedelta(days=4)           # 週終了（金）

    # この週の予定件数
    count = PER_WEEK if remain > PER_WEEK else remain
    remain -= count
    done = TOTAL_ITEMS - remain

    rows.append({
        "Week": week_no,
        "開始日": ws,
        "終了日": we,
        "週内予定件数": count,
        "累計予定件数": done,
    })

df = pd.DataFrame(rows)


# --- Excelに書き出し＋そのままグラフも作成（地図職人パート） ---
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(OUT_PATH, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
    # 表を書き込み
    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    workbook  = writer.book
    worksheet = writer.sheets[SHEET_NAME]

    # 見やすいように列幅ちょっと調整（お好みで）
    worksheet.set_column("A:A", 6)   # Week
    worksheet.set_column("B:C", 12)  # 日付
    worksheet.set_column("D:E", 14)  # 件数

    # グラフ（棒グラフ）作成
    chart = workbook.add_chart({"type": "column"})

    # データ範囲の最終行（ヘッダ行が1行あるので +1）
    max_row = len(df) + 1

    # シリーズ1: 週内予定件数（棒）
    chart.add_series({
        "name":       "週内予定件数",
        "categories": f"={SHEET_NAME}!$A$2:$A${max_row}",  # Week
        "values":     f"={SHEET_NAME}!$D$2:$D${max_row}",  # 週内予定件数
    })

    # シリーズ2: 累計予定件数（折れ線） → 進捗ののぼり坂イメージ
    chart.add_series({
        "name":       "累計予定件数",
        "categories": f"={SHEET_NAME}!$A$2:$A${max_row}",
        "values":     f"={SHEET_NAME}!$E$2:$E${max_row}",  # 累計予定件数
        "type":       "line",
        "y2_axis":    False,  # 必要なら第2軸にしてもOK
    })

    # タイトルとか軸ラベル（看板の文字）
    chart.set_title({"name": "先端キャップ改訂 週ごとの予定件数"})
    chart.set_x_axis({"name": "Week"})
    chart.set_y_axis({"name": "件数"})

    # シート上のどこに貼るか（G2あたりに配置）
    worksheet.insert_chart("G2", chart)

print(f"Excelを作ったよ → {OUT_PATH}")
