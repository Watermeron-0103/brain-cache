from flask import Flask, render_template, request, redirect, url_for
import random

app = Flask(__name__)

# Define the question bank for the quiz. Each entry contains a question, the correct answer,
# and an explanation that will be shown if the answer is incorrect.
QUESTIONS = [
    {
        "question": "ベクトル図形は、どれだけ拡大してもギザギザにならない。 (y/n)",
        "answer": "y",
        "explain": "ベクトルは数式で形を表現しているので、拡大しても滑らかに表示できるよ。",
    },
    {
        "question": "ラスター図形は、主に写真や画像データのようなピクセルの集まりで表現される。 (y/n)",
        "answer": "y",
        "explain": "ラスター＝ピクセルのマス目。拡大するとモザイクっぽくなるやつ。",
    },
    {
        "question": "レイヤ（画層）は、図形を種類ごとに分けて管理しやすくするための機能である。 (y/n)",
        "answer": "y",
        "explain": "レイヤを分けることで、表示/非表示や印刷のON/OFFを切り替えやすくなる。",
    },
]


@app.route("/", methods=["GET", "POST"])
def quiz():
    """
    Handle the quiz logic. On GET requests a new question is selected at random and displayed.
    On POST requests the user's answer is validated and the result is shown along with the explanation.
    Invalid indices or missing answers redirect back to the start to avoid errors from stale pages.
    """
    if request.method == "POST":
        # Retrieve the question index from the hidden form field. If it's not numeric, redirect to start.
        q_index_str = request.form.get("q_index", "")
        if not q_index_str.isdigit():
            return redirect(url_for("quiz"))

        q_index = int(q_index_str)
        # If the index is out of range, redirect to start (handles stale pages after question bank changes).
        if not (0 <= q_index < len(QUESTIONS)):
            return redirect(url_for("quiz"))

        # Get the user's answer and the corresponding question data.
        user_answer = request.form.get("answer", "").strip().lower()
        question = QUESTIONS[q_index]
        correct = (user_answer == question["answer"])

        return render_template(
            "quiz.html",
            question=question,
            q_index=q_index,
            result=correct,
            user_answer=user_answer,
        )

    # For GET requests, select a question at random and render it.
    q_index = random.randrange(len(QUESTIONS))
    question = QUESTIONS[q_index]
    return render_template(
        "quiz.html",
        question=question,
        q_index=q_index,
        result=None,
        user_answer=None,
    )


if __name__ == "__main__":
    # Enable debug mode for development; should be set to False in production
    app.run(debug=True)