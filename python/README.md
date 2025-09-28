# 自動議事録生成ツール (Python + faster-whisper)

## 概要
- mp3/wav 録音を読み込み
- faster-whisper で文字起こし
- 要点・決定事項・ToDo を抽出した Markdown 議事録を生成
- タイムスタンプ付き VTT も同時出力

## セットアップ
```bash
git clone https://github.com/yourname/auto-minutes.git
cd auto-minutes

# 仮想環境を推奨
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # macOS/Linux

pip install -r requirements.txt
