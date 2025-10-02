# 前環境の説明とガントチャート作成方法（Windows環境）

## 前環境の概要

- このレポジトリでは実験コードやメモを蓄稼しており、Windows環境で Python を用いて進捗管理やスクリプトのテストを行っています。
- ガントチャート生成に利用するプログラムは Python 3.x と `matplotlib`、場合によっては `pandas` を使用します。
- 日本語を含むグラフを出力するために日本語フォントが必要となります。

### 推奨ツール・ライブラリ

| ツール / ライブラリ | 用途 |
|----|----|
| Python 3.x | プログラム実行環境 |
| pip | パッケージ管理ツール |
| matplotlib | ガントチャート描画に利用 |
| pandas | CSVファイルから読み込む場合に利用 |
| 日本語フォント【IPAexGothic、Noto Sans CJK JP 等】 | 日本言ラベルの表示 |

## 日本語フォントの設定

Windows 環境で matplotlib を使って日本語を表示するには、日本語フォントを読み込むヘルパースクリプトを用意しておくと便利です。以下は `ja_font.py` の例です。

```
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

def set_japanese_font(preferred=None, extra_paths=None):
    plt.rcParams["axes.unicode_minus"] = False  # マイナス記号が文字化けするのを防ぐ

    # 追加のフォントパスを登録
    if extra_paths:
        for p in extra_paths:
            if os.path.isdir(p):
                fm.fontManager.addfont(p)
            elif os.path.isfile(p):
                fm.fontManager.addfont(p)

    default_candidates = [
        "IPAexGothic", "IPAGothic",
        "Noto Sans CJK JP", "Noto Sans JP",
        "Yu Gothic UI", "Yu Gothic", "Meiryo",
        "Hiragino Sans", "Hiragino Kaku Gothic ProN",
    ]
    if preferred:
        candidates = preferred + default_candidates
    else:
        candidates = default_candidates

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            return name

    print("日本語フォントが見つかりません。NotoやIPAexをインストールしてください。")
    return None
```

## ガントチャート作成手順

1. Python と必要なライブラリをインストールします。
   ```bash
   pip install matplotlib pandas
   ```
2. 上記の `ja_font.py` を同じディレクトリに保存し、スクリプトから `set_japanese_font()` を呼び出します。
3. タスクをリストまたは CSV で定義します。

### リストからの例

```
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from ja_font import set_japanese_font

# 日本語フォントを設定
set_japanese_font()

tasks = [
    {"task": "キックオフ", "start": "2025-10-03", "dur": 0.5, "owner": "井上"},
    {"task": "デモ測定A", "start": "2025-10-04", "dur": 1.0, "owner": "赤坂・山口"},
    {"task": "デモ測定B", "start": "2025-10-05", "dur": 1.0, "owner": "小倉・今野"},
    {"task": "個別操作練習", "start": "2025-10-06", "dur": 1.0, "owner": "全員"},
    {"task": "フォローQ&A", "start": "2025-10-07", "dur": 0.5, "owner": "全員"},
    {"task": "確認テスト", "start": "2025-10-08", "dur": 0.5, "owner": "各自/井上"},
]

fig, ax = plt.subplots(figsize=(10, 5))
y_positions = list(range(len(tasks)))[::-1]

for y, t in zip(y_positions, tasks):
    start = datetime.strptime(t["start"], "%Y-%m-%d")
    width = float(t["dur"])
    ax.barh(y, width, left=mdates.date2num(start), height=0.6)
    ax.text(mdates.date2num(start) + width + 0.02, y,
            f'{t["task"]}】{t["owner"]}】', va='center', fontsize=9)

ax.set_yticks(y_positions)
ax.set_yticklabels([t["task"] for t in tasks][::-1])
ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
ax.set_xlabel("日付")
ax.set_title("3GMS練習ガントチャート（短期）")
ax.grid(axis='x', linestyle=':', linewidth=0.5)

fig.tight_layout()
plt.savefig("gantt_3gms_short.png")
plt.close()
```

### CSVから読み込む例

CSV (`schedule.csv`) の例:

| Task | Start | DurationDays | Owner | Notes |
|--|--|--|--|--|
| キックオフ | 2025-10-03 | 0.5 | 井上 | 目的共有 |
| デモ測定A | 2025-10-04 | 1.0 | 赤坂・山口 | 一連の操作確認 |
| デモ測定B | 2025-10-05 | 1.0 | 小倉・今野 | 臨時対応者含む |
| 個別操作練習 | 2025-10-06 | 1.0 | 全員 | 設定変更〜保存確認 |
| フォローQ&A | 2025-10-07 | 0.5 | 全員 | 不明点吸い上げ |
| 確認テスト | 2025-10-08 | 0.5 | 各自/井上 | 合格で練習完了 |

読み込みと描画のコード:

```
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from ja_font import set_japanese_font

set_japanese_font()

df = pd.read_csv("schedule.csv")
df["Start"] = pd.to_datetime(df["Start"])
df["Finish"] = df["Start"] + df["DurationDays"].astype(float).apply(lambda d: timedelta(days=d))
df["Duration"] = (df["Finish"] - df["Start"]).dt.total_seconds() / (24*3600)

fig, ax = plt.subplots(figsize=(11, 5))
y_positions = list(range(len(df)))[::-1]

for y, (_, r) in zip(y_positions, df.iterrows()):
    start_num = mdates.date2num(r["Start"])
    ax.barh(y, r["Duration"], left=start_num, height=0.6)
    ax.text(start_num + r["Duration"] + 0.02, y,
            f"{r['Task']}\u3011{r['Owner']}\u3011", va='center', fontsize=9)

ax.set_yticks(y_positions)
ax.set_yticklabels(df["Task"].iloc[::-1])
ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
ax.set_xlabel("日付")
ax.set_title("3GMS練習ガントチャート（CSV入力）")
ax.grid(axis='x', linestyle=':', linewidth=0.5)

fig.tight_layout()
plt.savefig("gantt_from_csv.png")
plt.close()
```

## 補足

- 半日（`0.5`)のタスクは幅を 0.5 日として指定します。
- ラベルがはみ出る場合は図の幅 (`figsize`)を調整したり、x 軸の上限を広げます。
- Windows で日本語が 】 になる場合は `ja_font.py` の `preferred` 引数でお使いのフォント名を指定してください。

これで、キーエンス LM-X（3GMS）練習用のガントチャートを Python で生成する手順をまとめました。
