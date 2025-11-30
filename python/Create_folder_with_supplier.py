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
        if not code:
            continue
        if code in file_stem:
            hit_code = code
            break
        
    if hit_code is None:
        print(f"Not found: {file_stem}")
        continue
    
    if hit_code in code_to_dir:
        dest_dir = code_to_dir[hit_code]
    else:
        dest_dir = BASE_DIR / hit_code
        dest_dir.mkdir(parents=True, exist_ok=True)
        code_to_dir[hit_code] = dest_dir
        
    dest_path = dest_dir / pdf_stem.name
    print(f"Moving: {pdf_stem} -> {dest_path}")
    
    if dest_path.exists():
        print(f"Already exists, skipping: {dest_path}")
        continue

    pdf_stem.rename(dest_path)
    print(f"Moved: {pdf_stem} -> {dest_path}")
print("Done.")
