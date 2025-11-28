from pathlib import Path
import pandas as pd


EXCEL_PATH = Path("out/サプライヤー別ファイル/パーツ精工.xlsx")
BASE_DIR   = Path(r"\\fujifilm0.sharepoint.com@ssl\DavWWWRoot\sites\jp-dms-hcm1\08\DocLib3\材料証明証確認\単部品（図面_成績書）\パーツ精工")

df = pd.read_excel(EXCEL_PATH, sheet_name="data", dtype={"品目": str})
品目_list = df["品目"].dropna().unique().tolist()

code_to_dir: dict[str, Path] = {}

for pdf_stem in BASE_DIR.rglob("*.pdf"):
    file_stem = pdf_stem.stem

    hit_code = None
    for code in 品目_list:
        if code in file_stem:
            hit_code = code
            break

    if hit_code is None:
        print(f"未登録品目コード: {file_stem}")
        continue

    if hit_code in code_to_dir:
        dest_dir = code_to_dir[hit_code]
    else:
        dest_dir = BASE_DIR / hit_code
        dest_dir.mkdir(parents=True, exist_ok=True)
        code_to_dir[hit_code] = dest_dir

    dest_path = dest_dir / pdf_stem.name
    print("移動予定:")
    print("  元:", pdf_stem)
    print("  新:", dest_path)
    if dest_path.exists():
        print("  → 既に存在するためスキップ")
        continue
    pdf_stem.rename(dest_path)
    print("  → 移動完了")
