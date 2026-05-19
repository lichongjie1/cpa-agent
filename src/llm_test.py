"""
CPA 题库 Agent — DeepSeek API 首次调用
让 LLM 一次出 5 道 CPA 会计单选题，打印到终端
"""

# ✅ [现在懂] Day 1 学的：import 引入包
import json       # 处理 JSON 数据
import os         # 操作文件路径、读环境变量
import re         # [后面再懂] 正则表达式，匹配文本模式
from pathlib import Path          # [后面再懂] 处理文件路径，比 os.path 更好用
from dotenv import load_dotenv    # 从 .env 文件加载配置
from openai import OpenAI         # OpenAI 兼容 SDK（DeepSeek 也用这个）

# ✅ [现在懂] .env → 环境变量 → os.getenv() 取出来，API Key 不硬编码
#    Path(__file__).resolve().parent.parent =
#      当前文件(llm_test.py) → src/ → cpa-agent/(项目根) → cpa-agent/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

# ✅ [现在懂] 创建一个 API 客户端，像打开一扇门，后面通过它发请求
#    api_key  = 你的身份凭证
#    base_url = DeepSeek 的服务器地址
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),       # 从 .env 读密钥
    base_url=os.getenv("DEEPSEEK_BASE_URL"),     # https://api.deepseek.com
)

# ═══════════════════════════════════════════════════════════════
# ✅ [现在懂] def 定义函数（Day 2 学的），count: int = 5 是参数+默认值
# ═══════════════════════════════════════════════════════════════
def ask_cpa_question(count: int = 5):
    """让 DeepSeek 出 count 道 CPA 会计单选题，返回 API response"""
    # ✅ [现在懂] 发 HTTP 请求，和 Day 1 的 requests.get() 本质一样
    #    只不过这次是"聊天"请求，要传 messages
    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),  # ✅ 用哪个模型
        # ─── 下面 messages 是对话内容，list 套 dict（Day 2 学的）───
        messages=[
            # ✅ system 消息：给 AI 定人设和规则（幕后导演，用户看不到）
            {
                "role": "system",
                "content": (
                    "你是一位 CPA 会计考试出题专家。"          # 人设
                    f"每次一次性出恰好 {count} 道互不重复的单选题，"  # ✅ f-string 插变量
                    "每题 4 个选项（A/B/C/D），有且只有一个正确答案。"
                    "只输出 JSON 数组，不输出其他内容。"       # 格式约束
                ),
            },
            # ✅ user 消息：你的具体提问（用户说的话）
            {
                "role": "user",
                "content": (
                    f"出 {count} 道 CPA 会计科目的单选题。"
                    "用以下 JSON 数组格式输出（每个元素一题）：\n"
                    '[{"title": "题目内容", '
                    '"options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"], '
                    '"answer": "正确选项字母", '
                    '"explanation": "一句话解析"}]'
                ),
            },
        ],
        # ✅ temperature：0~2，越大越随机，越小越稳定
        temperature=0.5,
    )

    return response    # ✅ 返回完整的 API 响应对象


# ═══════════════════════════════════════════════════════════════
# [后面再懂] 这个函数整体先当黑盒用——知道"把 LLM 返回的字符串变成题目列表"就行
# ═══════════════════════════════════════════════════════════════
def parse_questions_json(raw: str) -> list:
    """解析 LLM 返回的 JSON 数组，兼容 markdown 代码块包裹"""
    # ✅ strip() 去掉字符串首尾空白
    text = raw.strip()

    # ❓ [后面再懂] 正则：检查 LLM 有没有用 ```json ... ``` 包裹内容
    #    re.search() 在字符串里找匹配模式 → 找到返回 match 对象，找不到返回 None
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        # fence_match.group(1) 取出括号 () 捕获的部分 = 去掉围栏后的纯 JSON
        text = fence_match.group(1).strip()

    # ✅ json.loads()：把 JSON 字符串变成 Python 对象（Day 3.3 学的）
    try:
        questions = json.loads(text)     # ✅ [现在懂]
    except json.JSONDecodeError:         # ✅ [现在懂] try/except 捕获解析失败
        print("⚠️ JSON 解析失败，原始返回：\n")
        print(raw)
        raise                            # ❓ raise = 把异常继续往上抛，让调用方知道出事了

    # ✅ isinstance(obj, list)：检查是不是列表
    if not isinstance(questions, list):
        raise ValueError(f"期望 JSON 数组，实际为 {type(questions).__name__}")
    return questions                     # ✅ 返回解析好的题目列表


# ═══════════════════════════════════════════════════════════════
# ✅ [现在懂] 以下是主程序，只在直接运行 llm_test.py 时执行
#    被 import 时不会跑（Day 3.2 学的 if __name__ == "__main__"）
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # ✅ 大写下划线 = 常量，约定俗成"这个值不会改"（Day 1 学的变量命名）
    NUM_QUESTIONS = 5

    # ✅ f-string 打印（Day 1）
    print(f"🤖 正在让 DeepSeek 出 {NUM_QUESTIONS} 道题...\n")

    # ✅ 调函数 → 发 API 请求 → 拿到响应
    response = ask_cpa_question(NUM_QUESTIONS)

    # ✅ 从响应里取 LLM 的文本输出（刚给你讲解过的层级结构）
    raw = response.choices[0].message.content

    # ❓ 调黑盒函数 → 把字符串解析成题目列表
    questions = parse_questions_json(raw)

    # ✅ if 判断 + len()（Day 2）
    if len(questions) != NUM_QUESTIONS:
        raise ValueError(f"期望 {NUM_QUESTIONS} 道题，实际返回 {len(questions)} 道")

    # ✅ for 循环遍历列表 + enumerate 带序号（Day 2）
    #    enumerate(questions, 1) 从 1 开始编号，i=序号，q=题目字典
    for i, q in enumerate(questions, 1):
        print(f"===== 第 {i}/{NUM_QUESTIONS} 题 =====")
        print(q["title"])               # ✅ dict 取值（Day 2）
        for opt in q["options"]:        # ✅ 嵌套 for 循环（Day 2）
            print(f"  {opt}")
        print(f"答案：{q['answer']}")
        print(f"解析：{q['explanation']}\n")

    # ✅ usage 就是 token 账单（刚给你讲解过的）
    print(
        f"📊 Token 用量：输入 {response.usage.prompt_tokens} | "
        f"输出 {response.usage.completion_tokens} | "
        f"合计 {response.usage.total_tokens}"
    )
