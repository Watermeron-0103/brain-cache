# スケジュールパターン解説【1日版と日単位版】

このドキュメントでは、ガントチャートを作成する際に使う 2 種類のスケジュールデータ形式を備忘録として整理します。

## パターンA（一日集中タイムテーブル）

- 1日の中で複数のタスクの開始時刻と終了時刻を粗まく記録します。
- CSVファイルには以下の列を含めます。

| 列名 | 説明 |
|-----|-----|
| Task | タスク名 |
| StartDate | 日付（YYYY-MM-DD） |
| StartTime | 開始時刻（HH:MM） |
| EndTime | 終了時刻（HH:MM） |
| Owner | 担当者や参加者 |
| Notes | 補足説明（任意） |

### CSV例

```csv
Task,StartDate,StartTime,EndTime,Owner,Notes
キックオフ,2025-10-06,09:00,09:30,井上,目的共有
デモ測定A,2025-10-06,09:30,10:30,赤坂,操作の流れ確認
デモ測宝B,2025-10-06,10:40,11:40,山口,設定確認
個別練習,2025-10-06,13:00,14:30,小倉・今野,保存・エクスポート
Q&A,2025-10-06,14:40,15:30,全員,質問対応と小テスト
```

## パターンB（日単位スケジュール）

- 複数日にまたがる作業や計画を記述する形式です。
- タスクの開始日と続結日数（DurationDays）を指定します。
- CSVファイルには以下の列を含めます。

| 列名 | 説明 |
|-----|-----|
| Task | タスク名 |
| Start | 開始日（YYYY-MM-DD） |
| DurationDays | 期間（日数，小数で半日を表現可） |
| Owner | 担当者や参加者 |
| Notes | 補足説明（任意） |

### CSV例

```csv
Task,Start,DurationDays,Owner,Notes
キックオフ,2025-10-03,0.5,井上,目的共有
デモ測宝(\u30b0ループA),2025-10-04,1.0,赤坂・山口,一連の操作確認
デモ測宝(\u30b0ループB),2025-10-05,1.0,小倉・今野,臨時対応者含む
個別操作練習,2025-10-06,1.0,全員,設定変更〜保存確認
フォローQ&A,2025-10-07,0.5,全員,不明点吸い上げ
確認テスト,2025-10-08,0.5,各自/\u78ba認:\u4e95上,合格で習熟完了
```

## パターンAとBの使い分け

| 項目 | パターンA | パターンB |
|-----|-----|-----|
| 想定用途 | 1日内の詳細な時間割 | 日単体の計画 |
| 期間 | 同一日 | 複数日 |
| 主要列 | StartDate, StartTime, EndTime | Start, DurationDays |
| 続結表現 | 時間単位 | 日数単位 |
| メリット | 時間単位での粗い調整が可能 | 長期計画を簡潔に記述できる |
| ファイル例 | `schedule_day.csv` | `schedule.csv` |


## Python コード例・ガントチャート生成

本リポジトリには、上記データ形式からガントチャートを生成する Python スクリプト [`generate_gantt.py`](./generate_gantt.py) が含まれています。  
このスクリプトには以下の関数が実装されています。

- **draw_single_day_gantt(csv_path, output_path)** – パターンA用。1日集中スケジュールに対応します。
  `schedule_day.csv`などの CSV から 1日版ガントチャートを PNG 出力します。
- **draw_multi_day_gantt(csv_path, output_path)** – パターンB用、日単位スケジュールに対応します。
  `schedule.csv`などの CSV から複数日ガントチャートを PNG 出力します。

### 使用例

```python
from generate_gantt import draw_single_day_gantt, draw_multi_day_gantt

# 1日版ガントチャートを作成
draw_single_day_gantt("schedule_day.csv", "single_day_gantt.png")

# 日単位版ガントチャートを作成
draw_multi_day_gantt("schedule.csv", "multi_day_gantt.png")
```

詳細なコードは [`generate_gantt.py`](./generate_gantt.py) を参照してください。
この解説を参考に、用途に応じて適切なパターンを選んでガントチャートを作成してください。
