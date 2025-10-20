# 部品No. 正規化メモ（ユニーク判定用）
**更新日:** 2025-10-20 (JST)

このメモは、部品番号（部品No.）のユニーク判定を安定させるための**正規化ルール**と**実装例**をまとめた備忘録です。  
本プロジェクトの現仕様では、**空白は意味を持たないため同一扱い（削除）**とします。また、**各種ダッシュは ASCII ハイフン `-` に統一**します。

---

## 1. 正規化の目的
- 入力元や運用ごとの差異（全角/半角、紛らわしいダッシュ、不可視文字、大小の違い等）を吸収し、**同一なものは同一キー**に揃える。
- これにより、`duplicated` などの重複検出・ユニーク判定が**仕様通り**に働く。

---

## 2. 正規化ルール（現在の採用方針）
1. **Unicode 正規化 NFKC**  
   半角/全角の差を吸収。例: `Ａ１２３` → `A123`
2. **前後の空白除去** + **全角空白→半角**  
   例: `\u3000` を半角空白に置換してから `strip()`。
3. **不可視スペースの削除**  
   `NO-BREAK SPACE (\u00A0)`, `ZERO WIDTH SPACE (\u200B)`, `ZERO WIDTH JOINER/NON-JOINER (\u200C-\u200D)`, `BOM (\uFEFF)` などを除去。
4. **ダッシュ類の統一**（**同一扱い**）  
   `− (U+2212)`, `– (U+2013)`, `— (U+2014)`, `ー`, `‐`, `FF0D` などを **`-`** に統一。
5. **空白の扱い**（**同一扱い**）  
   連続・種別問わず **すべて削除**（例: `AB  123` → `AB123`）。
6. **大文字化**（**upper**）  
   例: `ab-01` → `AB-01`

### 原則として保持するもの
- **先頭ゼロ**：`00123` と `123` は **別物**（保持）。
- **区切り記号の種別**：`-` と `/` は意味が異なる可能性が高いため **区別**する（`/` の統一はしない）。
- **アンダースコア `_`、ドット `.`**：意味を持つ可能性があるため **そのまま**。

> 変更が必要になったら、このメモで方針を更新し、実装の該当行も合わせて修正すること。

---

## 3. 実装（Python）
### 3.1 正規化関数
```python
import re, unicodedata

def normalize_part_code(s, drop_spaces=True, unify_dash=True, case="upper"):
    """部品No.の揺れ吸収キーを作る。
    現仕様: 空白は削除、ダッシュは '-' に統一、NFKC、upper。
    """
    if s is None:
        return ""
    x = unicodedata.normalize("NFKC", str(s))
    # 全角空白→半角、前後スペース除去
    x = x.replace("\u3000", " ").strip()
    # NBSP/ゼロ幅系を削除
    x = re.sub(r"[\u00A0\u200B-\u200D\uFEFF]", "", x)
    # ダッシュ類を ASCII ハイフンへ
    if unify_dash:
        x = re.sub(r"[\u2212\u2010-\u2015\u2500\uFF0D]", "-", x)
    # 空白処理：本仕様では全削除
    x = re.sub(r"\s+", "" if drop_spaces else " ", x)
    # 大文字/小文字
    if case == "upper":
        x = x.upper()
    elif case == "lower":
        x = x.lower()
    return x
```

### 3.2 ユニークフラグ付与（シート内 / シート横断）
```python
import pandas as pd

def mark_unique_flags(df: pd.DataFrame, col: str, seen_global: set | None = None):
    key = df[col].map(normalize_part_code)
    df = df.copy()
    # シート内でのユニーク（最初の1件のみ True）
    df["ユニーク_シート内"] = ~key.duplicated(keep="first")
    # ファイル全体（シート横断）でのユニーク
    if seen_global is None:
        seen_global = set()
    flags = []
    for k in key:
        if not k:                  # 空欄はユニーク扱いしない（必要なら pd.NA に変更可）
            flags.append(False)
        elif k in seen_global:
            flags.append(False)
        else:
            seen_global.add(k)
            flags.append(True)
    df["ユニーク_全体"] = flags
    # デバッグ支援として正規化キーを残す（不要なら drop 可）
    df["正規化キー"] = key
    return df, seen_global
```

---

## 4. 例（Before → After）
| 入力 | 正規化後 |
|---|---|
| `ＡＢ １２３` | `AB123` |
| `AB−12—3` | `AB-12-3` |
| `ab-01` | `AB-01` |
| `AB\u00A0123` (NBSP) | `AB123` |
| `A\u200BB-01` (ZERO WIDTH SPACE) | `AB-01` |

---

## 5. よくある論点と判断基準
- **先頭ゼロの扱い**：部品規格上意味があることが多い → **保持**。
- **`-` と `/` の統一**：意味が異なる設計が多い → **統一しない**（別物判定）。
- **空白の有無**：**同一扱い**（本仕様では削除）。
- **大小の違い**：**同一扱い**（upper に統一）。

---

## 6. 変更履歴
- **2025-10-20**: 初版作成。空白=同一扱い（削除）、ダッシュ同一化、upper、NFKC 採用。
