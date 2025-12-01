from flask import Flask, render_template, request, redirect, url_for
import random

app = Flask(__name__)  # 勇者が冒険する世界を起動。Flask がゲームエンジンです。

# 冒険中に出会うモンスターを登録。1体につき「名前」「正解コマンド」「倒した後の解説」を設定。
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
    村の入り口にあるクイズ屋さんのような場所。GET で訪れると、新しいモンスターがランダムに現れる。
    POST で答えを送ると、勇者の攻撃が当たったかどうかを判定し、結果を教えてくれる。
    おかしなリクエスト（無効なインデックス）があれば自動的に村に戻される。
    """
    if request.method == "POST":
        # プレイヤーが倒そうとしているモンスター番号を取得。数字でなければ村に帰還。
        q_index_str = request.form.get("q_index", "")
        if not q_index_str.isdigit():
            return redirect(url_for("quiz"))

        q_index = int(q_index_str)
        # 登録されていないモンスター番号なら村に帰還。
        if not (0 <= q_index < len(QUESTIONS)):
            return redirect(url_for("quiz"))

        # 勇者が入力したコマンドを取得して、正しいかどうか判定。
        user_answer = request.form.get("answer", "").strip().lower()
        question = QUESTIONS[q_index]
        correct = (user_answer == question["answer"])

        # 結果画面を表示。正解なら「討伐成功」、不正解なら「残念…」と解説付き。
        return render_template(
            "quiz.html",
            question=question,
            q_index=q_index,
            result=correct,
            user_answer=user_answer,
        )

    # GET の場合：新しいモンスターと遭遇。ランダムで 1 体選ばれる。
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
    # デバッグモードで勇者の冒険をスタート。製品運用時は debug=False で起動しましょう。
    app.run(debug=True)
