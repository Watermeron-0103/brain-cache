from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

CSV_PATH = Path(__file__).with_name("questions.csv")  # 運用時は questions.csv にリネームして使う

def load_questions_csv(path: Path) -> list[dict[str, Any]]:
    """CSV列: question, answer, explain, category, level
    - answer は y/n（小文字）を想定
    - category は '製図' 'PC' '図形' など自由
    - level は整数（任意）
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} が見つかりません。questions_template.csv をコピーして questions.csv を作ってね。"
        )

    questions: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = {
                "question": (row.get("question") or "").strip(),
                "answer": (row.get("answer") or "").strip().lower(),
                "explain": (row.get("explain") or "").strip(),
                "category": (row.get("category") or "").strip() or "未分類",
            }
            level = (row.get("level") or "").strip()
            if level.isdigit():
                q["level"] = int(level)

            if q["question"] and q["answer"] in ("y", "n"):
                questions.append(q)

    if not questions:
        raise ValueError("CSVから有効な問題を読み込めませんでした。question と answer(y/n) を確認してね。")
    return questions

ALL_QUESTIONS = load_questions_csv(CSV_PATH)
CATEGORIES = sorted({q["category"] for q in ALL_QUESTIONS})

def pick_question(category: str | None = None) -> tuple[int, dict[str, Any]]:
    if category:
        candidates = [(i, q) for i, q in enumerate(ALL_QUESTIONS) if q["category"] == category]
        if not candidates:
            return pick_question(None)
        return random.choice(candidates)
    i = random.randrange(len(ALL_QUESTIONS))
    return i, ALL_QUESTIONS[i]

@app.route("/", methods=["GET", "POST"])
def lobby():
    return quiz(category=None)

@app.route("/c/<category>", methods=["GET", "POST"])
def area(category: str):
    if category not in CATEGORIES:
        return redirect(url_for("lobby"))
    return quiz(category=category)

def quiz(category: str | None):
    if request.method == "POST":
        q_index_str = request.form.get("q_index", "")
        if not q_index_str.isdigit():
            return redirect(url_for("area", category=category) if category else url_for("lobby"))

        q_index = int(q_index_str)
        if not (0 <= q_index < len(ALL_QUESTIONS)):
            return redirect(url_for("area", category=category) if category else url_for("lobby"))

        user_answer = request.form.get("answer", "").strip().lower()
        question = ALL_QUESTIONS[q_index]
        correct = (user_answer == question["answer"])

        return render_template(
            "quiz.html",
            question=question,
            q_index=q_index,
            result=correct,
            user_answer=user_answer,
            category=category,
            categories=CATEGORIES,
        )

    q_index, question = pick_question(category)
    return render_template(
        "quiz_csv.html",
        question=question,
        q_index=q_index,
        result=None,
        user_answer=None,
        category=category,
        categories=CATEGORIES,
    )

if __name__ == "__main__":
    app.run(debug=True)
