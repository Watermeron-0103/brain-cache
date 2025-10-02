# brain-cache

# Brain Cache

このリポジトリは、日々の学び・実験コード・小さなユーティリティを記録しておく「脳のキャッシュ置き場」です。  
業務効率化スクリプトや、Python の備忘録、実験的なコードをまとめています。

---

## ディレクトリ構成


brain-cache/
├─ python/            # Python 備忘録・スクリプト置き場
│  ├─ meeting-minutes/  # 自動議事録生成ツール（faster-whisper 使用）
│  └─ ...              # その他の Python ツールやメモを追加予定
├─ docs/              # ドキュメントや学習メモ
└─ ...                # 他言語や試験的コードも追加可


---

## 主要プロジェクト

### 🎙 meeting-minutes
- 録音した mp3/wav を自動で文字起こし
- 要点・決定事項・ToDo を抽出して Markdown 議事録を生成
- 詳細な使い方は [python/meeting-minutes/README.md](python/meeting-minutes/README.md) を参照

---

## 開発環境

- Python 3.10+
- pip または uv などのパッケージ管理ツール
- 必要パッケージは各プロジェクト内の `requirements.txt` を参照

---

## 利用ポリシー
- 個人の学習・業務効率化用のスニペット集です  
- 再利用は自由ですが、動作保証はありません  
- 改善案や追加はプルリク歓迎 🚀

---

## TODO
- Python のメモ・小ツールの追加
- ディレクトリ構造の拡張（Rust, JS, Shell など）
- 実験コードや学習ノートの整理
