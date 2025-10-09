"""
app.py
======

Flaskフロントエンドから Selenium の自動化フローを呼び出すためのアプリケーションです。
ユーザーはブラウザ上で起票日の開始日と終了日を選択し、ボタンをクリックするだけで
返品管理票のCSVをエクスポートできます。処理完了後にはダウンロードリンクが表示されます。

依存ライブラリ:
  - flask
  - selenium (内部で returns_form.py を利用)

テンプレートは `templates/index.html` に用意してあります。
"""

from __future__ import annotations
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory, url_for, redirect, flash

from returns_form import run_automation

# ダウンロードディレクトリ (returns_form.DOWLOAD_DIR と同じ場所を利用)
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "please-change-this"

@app.get("/")
def index():
    # 今日を終了日、6日前を開始日にするデフォルト
    end = date.today()
    start = end - timedelta(days=6)
    return render_template(
        "index.html",
        default_start=start.isoformat(),
        default_end=end.isoformat(),
    )

@app.post("/run")
def run():
    start_str = request.form.get("start") or ""
    end_str = request.form.get("end") or ""
    headless = request.form.get("headless") == "on"

    if not start_str or not end_str:
        flash("開始日と終了日を入力してください。")
        return redirect(url_for("index"))
    if start_str > end_str:
        flash("開始日は終了日以前にしてください。")
        return redirect(url_for("index"))

    # returns_form の run_automation で必要なフォーマット YYYY/MM/DD
    start_fmt = start_str.replace("-", "/")
    end_fmt = end_str.replace("-", "/")
    out_name = f"imart_返品管理表_{start_str}_{end_str}.csv"

    try:
        csv_path = run_automation(start_fmt, end_fmt, out_name, headless=headless)
        # 処理成功をユーザーに通知し、ダウンロードページへ
        flash("CSVの作成に成功しました。")
        return redirect(url_for("download_file", filename=csv_path.name))
    except Exception as e:
        flash(f"エラーが発生しました: {e!r}")
        return redirect(url_for("index"))

@app.get("/download/<path:filename>")
def download_file(filename):
    # CSVファイルをダウンロードさせる
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
