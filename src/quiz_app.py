"""
Mini Quiz App — CPA 智能答题系统
用轻量 OOP 结构串联：文件读题 / LLM 出题 / 答题判分 / 保存成绩
"""

import json
from datetime import datetime
from pathlib import Path

from llm_test import ask_cpa_question, parse_questions_json

BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
LOG_FILE = BASE_DIR / "quiz_log.txt"


class QuestionFileError(Exception):
    """题库文件加载失败"""


class Question:
    """一道 CPA 题目"""

    def __init__(self, title: str, options: list[str], answer: str, explanation: str = ""):
        self.title = title
        self.options = options
        self.answer = answer.strip().upper()
        self.explanation = explanation

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            title=data["title"],
            options=data["options"],
            answer=data["answer"],
            explanation=data.get("explanation", ""),
        )

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "options": self.options,
            "answer": self.answer,
            "explanation": self.explanation,
        }

    def check(self, user_input: str) -> bool:
        return user_input.strip().upper() == self.answer

    def valid_options(self) -> list[str]:
        return [opt[0].upper() for opt in self.options]


class QuestionService:
    """题库来源：文件 or LLM"""

    def __init__(self, questions_file: Path):
        self.questions_file = questions_file

    def load_from_file(self) -> list[Question]:
        try:
            data = json.loads(self.questions_file.read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            raise QuestionFileError(f"题库文件不存在：{self.questions_file}") from e
        except json.JSONDecodeError as e:
            raise QuestionFileError(f"题库 JSON 格式错误：{self.questions_file}") from e
        return [Question.from_dict(item) for item in data]

    def save_questions(self, questions: list[Question]):
        data = [question.to_dict() for question in questions]
        self.questions_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def generate_by_llm(self, count: int) -> list[Question]:
        print(f"🤖 正在让 DeepSeek 出 {count} 道题...")
        response = ask_cpa_question(count)
        raw = response.choices[0].message.content
        questions = [Question.from_dict(item) for item in parse_questions_json(raw)]
        self.save_questions(questions)
        print(f"💾 题目已保存到 {self.questions_file}")
        usage = response.usage
        print(f"📊 Token：输入 {usage.prompt_tokens} | 输出 {usage.completion_tokens}")
        return questions


class QuizEngine:
    """负责答题流程和成绩记录"""

    def __init__(self, questions: list[Question], log_file: Path):
        self.questions = questions
        self.log_file = log_file
        self.score = 0
        self.records: list[dict] = []

    def validate_choice(self, prompt: str, valid_options: list[str]) -> str:
        while True:
            raw = input(prompt).strip().upper()
            if raw in [opt.upper() for opt in valid_options]:
                return raw
            print(f"⚠️ 请输入 {'/'.join(valid_options)}")

    def run(self) -> tuple[int, list[dict]]:
        self.score = 0
        self.records = []

        for i, question in enumerate(self.questions, 1):
            print(f"\n{'=' * 50}")
            print(f"第 {i}/{len(self.questions)} 题：{question.title}")
            for option in question.options:
                print(f"    {option}")

            valid = question.valid_options()
            user_input = self.validate_choice(f"你的答案（{'/'.join(valid)}）：", valid)

            if question.check(user_input):
                print("    ✅ 正确！")
                self.score += 1
            else:
                print(f"    ❌ 错误！正确答案是 {question.answer}")
                if question.explanation:
                    print(f"    💡 {question.explanation}")

            self.records.append(
                {
                    "question": question.title,
                    "your_answer": user_input,
                    "correct_answer": question.answer,
                    "correct": question.check(user_input),
                }
            )

        return self.score, self.records

    def save_result(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(f"\n{'=' * 40}\n")
            file.write(f"📅 {now}  得分：{self.score}/{len(self.questions)}\n")
            for record in self.records:
                mark = "✅" if record["correct"] else "❌"
                file.write(f"  {mark} {record['question']} → {record['your_answer']}\n")
        print(f"\n📝 成绩已保存到 {self.log_file}")


def choose_questions(service: QuestionService) -> list[Question]:
    print("=" * 50)
    print("📚 CPA 智能答题系统")
    print("=" * 50)
    print("1. 从文件加载题库")
    print("2. 让 AI 出新题")
    print()

    choice = input("请选择（1 或 2）：").strip()
    while choice not in ("1", "2"):
        choice = input("请输入 1 或 2：").strip()

    if choice == "1":
        try:
            questions = service.load_from_file()
        except QuestionFileError as error:
            print(f"⚠️ {error}")
            print("题库不可用，自动切换到 AI 出题...")
            questions = service.generate_by_llm(5)
        if not questions:
            print("题库为空，自动切换到 AI 出题...")
            questions = service.generate_by_llm(5)
        return questions

    try:
        count = int(input("出几道题？（默认 5）：").strip() or "5")
    except ValueError:
        count = 5
    return service.generate_by_llm(count)


def main():
    service = QuestionService(QUESTIONS_FILE)
    questions = choose_questions(service)
    quiz = QuizEngine(questions, LOG_FILE)
    score, _ = quiz.run()
    print(f"\n{'=' * 50}")
    print(f"🏆 最终得分：{score}/{len(questions)}")
    quiz.save_result()


if __name__ == "__main__":
    main()
