"""
Mini Quiz App — CPA 智能答题系统
串联 Day 1-3 全部技能：文件读题 / LLM 出题 / 答题判分 / 保存成绩
"""

import json
import os
from datetime import datetime

# 从同目录的 llm_test 模块导入出题相关函数
from llm_test import ask_cpa_question, parse_questions_json

# 题库文件路径（同目录下的 questions.json）
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "questions.json")
# 成绩记录文件
LOG_FILE = os.path.join(os.path.dirname(__file__), "quiz_log.txt")


# ============================================================
# Section 1：题库加载（Day 3.3 文件读写）
# ============================================================

def load_from_file(path: str) -> list:
    """从 JSON 文件加载题库"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  题库文件不存在：{path}")
        return []


def generate_by_llm(count: int) -> list:
    """让 DeepSeek 出新题（Day 3.4 API 调用）"""
    print(f"🤖 正在让 DeepSeek 出 {count} 道题...")
    response = ask_cpa_question(count)
    raw = response.choices[0].message.content
    questions = parse_questions_json(raw)

    # 顺便存到文件，以后可以直接加载
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"💾 题目已保存到 {QUESTIONS_FILE}")

    # 打印 token 用量
    usage = response.usage
    print(f"📊 Token：输入 {usage.prompt_tokens} | 输出 {usage.completion_tokens}")

    return questions


# ============================================================
# Section 2：答题引擎（Day 2 循环+判断，Day 3.2 模块化）
# ============================================================

def check_answer(question: dict, user_input: str) -> bool:
    """判断答对没有"""
    return user_input.strip().upper() == question["answer"]


def run_quiz(questions: list) -> tuple:
    """逐题答题，返回 (得分, 作答记录)"""
    score = 0
    records = []  # 存每条作答记录

    for i, q in enumerate(questions, 1):
        print(f"\n{'=' * 50}")
        print(f"第 {i}/{len(questions)} 题：{q['title']}")
        for opt in q["options"]:
            print(f"    {opt}")

        # 获取用户输入
        user_input = input("你的答案（A/B/C/D）：").strip()
        while user_input.upper() not in ("A", "B", "C", "D"):
            user_input = input("请输入 A/B/C/D：").strip()

        if check_answer(q, user_input):
            print("    ✅ 正确！")
            score += 1
        else:
            print(f"    ❌ 错误！正确答案是 {q['answer']}")
            if "explanation" in q:
                print(f"    💡 {q['explanation']}")

        records.append({
            "question": q["title"],
            "your_answer": user_input.upper(),
            "correct_answer": q["answer"],
            "correct": user_input.upper() == q["answer"],
        })

    return score, records


# ============================================================
# Section 3：保存成绩（Day 3.3 文件写入）
# ============================================================

def save_result(score: int, total: int, records: list):
    """把成绩追加写入日志文件"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 40}\n")
        f.write(f"📅 {now}  得分：{score}/{total}\n")
        for r in records:
            mark = "✅" if r["correct"] else "❌"
            f.write(f"  {mark} {r['question']} → {r['your_answer']}\n")

    print(f"\n📝 成绩已保存到 {LOG_FILE}")


# ============================================================
# Section 4：主程序
# ============================================================

def main():
    print("=" * 50)
    print("📚 CPA 智能答题系统")
    print("=" * 50)
    print("1. 从文件加载题库")
    print("2. 让 AI 出新题")
    print()

    choice = input("请选择（1 或 2）：").strip()
    while choice not in ("1", "2"):
        choice = input("请输入 1 或 2：").strip()

    # 获取题目
    if choice == "1":
        questions = load_from_file(QUESTIONS_FILE)
        if not questions:
            print("题库为空，自动切换到 AI 出题...")
            questions = generate_by_llm(5)
    else:
        try:
            count = int(input("出几道题？（默认 5）：").strip() or "5")
        except ValueError:
            count = 5
        questions = generate_by_llm(count)

    # 答题
    score, records = run_quiz(questions)

    # 显示结果
    print(f"\n{'=' * 50}")
    print(f"🏆 最终得分：{score}/{len(questions)}")

    # 保存成绩
    save_result(score, len(questions), records)


# ✅ [现在懂] if __name__ == "__main__"（Day 3.2 学的）
if __name__ == "__main__":
    main()
