from datetime import date
from pathlib import Path

import pandas as pd


# ===== パラメータ（ここだけいじれば別案件にも使える） =====
OUT_PATH = Path("out/mile_stone_plug.xlsx")
SHEET_NAME = "スケジュール"
# =======================================================

# マイルストーン一覧（ここを書き換えれば他案件にも使える）
milestones = [
    {
        "No": "0-1",
        "やること": "改訂スケジュールExcel作成",
        "期限": date(2025, 12, 6),   # もう完了してるならこの日付
        "状態": "✅ 完了",
    },
    {
        "No": "0-2",
        "やること": "不要column削除したリストを作成",
        "期限": date(2025, 12, 9),
        "状態": "☐ 未着手",         # 後でExcel上で書き換える
    },
    {
        "No": "0-3",
        "やること": "plug list 作成",
        "期限": date(2025, 12, 13),
        "状態": "☐ 未着手",
    }
]

df = pd.DataFrame(milestones)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with pd.ExcelWriter(OUT_PATH, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    workbook = writer.book
    ws = writer.sheets[SHEET_NAME]

    # 列幅ちょい調整（見やすさ用）
    ws.set_column("A:A", 8)
    ws.set_column("B:B", 40)
    ws.set_column("C:C", 15)
    ws.set_column("D:D", 12)

print(f"マイルストーン表を作ったよ → {OUT_PATH}")
