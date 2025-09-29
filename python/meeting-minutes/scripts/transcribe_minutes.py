#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
import datetime as dt
from pathlib import Path
from typing import List, Tuple

from rich.console import Console
from rich.progress import track
from pydub import AudioSegment
import numpy as np

# 文字起こし：ローカル実行（要インターネット不要）
from faster_whisper import WhisperModel

console = Console()

# ---------- ユーザ調整パラメータ ----------
MODEL_SIZE = "medium"  # small / medium / large-v3 など（日本語は medium以上推奨）
BEAM_SIZE = 5
LANG = "ja"            # 日本語固定（混在音声でも基本OK）
MAX_LINE_CHARS = 80    # VTTの1行幅（見やすさ用）
# ---------------------------------------


def load_audio_to_wav(input_path: Path) -> Path:
    """mp3等をwavへ一時変換（Whisperは直接でもOKだが、念のため正規化）"""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    tmp_wav = input_path.with_suffix(".tmp.wav")
    audio.export(tmp_wav, format="wav")
    return tmp_wav


def timestamp(seconds: float) -> str:
    """秒→VTT風タイムスタンプ 00:00:00.000"""
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def wrap_text(text: str, width: int) -> str:
    lines = []
    cur = ""
    for ch in text:
        cur += ch
        if len(cur) >= width and ch in "、。.!?！？　 ":
            lines.append(cur.strip())
            cur = ""
    if cur:
        lines.append(cur.strip())
    return "\n".join(lines)


def transcribe(audio_path: Path) -> List[dict]:
    """
    faster-whisperで文字起こし。
    戻り値: [{"start": float, "end": float, "text": str}, ...]
    """
    console.log(f"[bold]Loading model:[/bold] {MODEL_SIZE}")
    model = WhisperModel(
        MODEL_SIZE,
        compute_type="int8" if os.getenv("FW_INT8", "1") == "1" else "float16",
    )

    console.log(f"[bold]Transcribing:[/bold] {audio_path.name}")
    segments, info = model.transcribe(
        str(audio_path),
        language=LANG,
        beam_size=BEAM_SIZE,
        vad_filter=True,     # 無音で区切る
        condition_on_previous_text=True
    )
    out = []
    for seg in segments:
        out.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    console.log(f"Duration: {info.duration:.1f}s, Language: {info.language}")
    return out


def simple_minute_maker(segments: List[dict]) -> Tuple[List[str], List[str], List[str]]:
    """
    超シンプル抽出器：
    - 要点: 文長がそこそこ & キーワードを含むものを優先
    - 決定事項: 「決定/了承/採用/進める/対応する」などを含む
    - ToDo: 「〜お願いします/〜する/対応/宿題/期限/まで」等を含む文を抽出

    ※ 完璧主義ではなく、まずは“そこそこ使える”出力を狙う。
    """
    text = "。".join([s["text"] for s in segments])
    sentences = [s.strip() for s in re.split(r"[。！？\n]", text) if s.strip()]

    key_words = ["方針", "検討", "課題", "原因", "対策", "目的", "影響", "スケジュール", "コスト", "品質", "検査", "計画", "要件", "仕様"]
    decide_words = ["決定", "了承", "合意", "採用", "進める", "確定", "OKとする"]
    todo_words = ["お願いします", "対応する", "対応お願いします", "実施する", "宿題", "やる", "作成する", "提出", "確認する", "まで", "期限", "担当"]

    points = []
    decisions = []
    todos = []

    def has_any(wlist, s): return any(w in s for w in wlist)

    for s in sentences:
        if len(s) >= 18 and (has_any(key_words, s) or "重要" in s):
            points.append(s + "。")
        if has_any(decide_words, s):
            decisions.append(s + "。")
        if has_any(todo_words, s):
            todos.append(s + "。")

    # 冗長さ軽減：重複近文を削る
    def dedupe_keep_order(lst):
        seen = set()
        out = []
        for x in lst:
            k = re.sub(r"\s+", "", x)
            if k not in seen:
                out.append(x)
                seen.add(k)
        return out

    return dedupe_keep_order(points[:12]), dedupe_keep_order(decisions[:12]), dedupe_keep_order(todos[:20])


def save_vtt(segments: List[dict], vtt_path: Path):
    with vtt_path.open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n{timestamp(seg['start'])} --> {timestamp(seg['end'])}\n")
            f.write(wrap_text(seg["text"], MAX_LINE_CHARS) + "\n\n")


def make_minutes_md(
    src_file: str,
    segments: List[dict],
    points: List[str],
    decisions: List[str],
    todos: List[str],
    out_md: Path
):
    date_str = dt.datetime.now().strftime("%Y-%m-%d")
    total_min = (segments[-1]["end"] - segments[0]["start"]) / 60 if segments else 0.0

    def bullets(lines):
        return "\n".join([f"- {l}" for l in lines]) if lines else "- （抽出なし）"

    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"# 議事録（自動生成）\n")
        f.write(f"- 収録ファイル: `{src_file}`\n")
        f.write(f"- 作成日: {date_str}\n")
        f.write(f"- 収録時間: 約 {total_min:.1f} 分\n")
        f.write("\n---\n\n")
        f.write("## 概要\n")
        f.write("本議事録は自動生成です。重要事項は必ず人手で確認してください。\n\n")
        f.write("## 要点\n")
        f.write(bullets(points) + "\n\n")
        f.write("## 決定事項\n")
        f.write(bullets(decisions) + "\n\n")
        f.write("## ToDo（担当/期限は追記してください）\n")
        f.write(bullets(todos) + "\n\n")
        f.write("## タイムスタンプ付きトランスクリプト\n")
        f.write("WebVTTファイル（同フォルダ）を参照してください。\n")


def main():
    parser = argparse.ArgumentParser(description="MP3→文字起こし→議事録Markdown自動生成")
    parser.add_argument("audio", type=str, help="入力音声ファイル（mp3/wav等）")
    parser.add_argument("--model", type=str, default=MODEL_SIZE, help="faster-whisperモデルサイズ")
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    assert audio_path.exists(), f"音声ファイルが見つかりません: {audio_path}"

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    # 一時wavへ
    tmp_wav = load_audio_to_wav(audio_path)

    # 文字起こし
    segs = transcribe(tmp_wav)

    # 抽出
    points, decisions, todos = simple_minute_maker(segs)

    # 保存
    stem = audio_path.stem
    date_tag = dt.datetime.now().strftime("%Y-%m-%d")
    vtt_path = out_dir / f"{date_tag}_トランスクリプト_{stem}.vtt"
    md_path  = out_dir / f"{date_tag}_議事録_{stem}.md"

    save_vtt(segs, vtt_path)
    make_minutes_md(audio_path.name, segs, points, decisions, todos, md_path)

    # 後始末
    try:
        tmp_wav.unlink(missing_ok=True)
    except Exception:
        pass

    console.print(f"[bold green]完了！[/bold green] 議事録: {md_path}\nVTT: {vtt_path}")


if __name__ == "__main__":
    main()
