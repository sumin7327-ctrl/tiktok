from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
import requests
import os

load_dotenv("tiktok_bot.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

SYSTEM_PROMPT = """
너는 틱톡라이브 전문 콘텐츠 파트너다.
친근하고 쉽게 반말로 쓴다.
광고 냄새 금지, 딱딱한 설명체 금지.
주제는 틱톡라이브 최신 뉴스 / 인사이트 / 영업 / 팁이다.
콘텐츠는 항상 1개만 작성해. 여러 개 나열하지 마.

틱톡라이브 전문 지식:
- LIVE Center: 크리에이터가 라이브 성과, 수익, 통계를 확인하는 대시보드
- 선물(Gift): 시청자가 라이브 중 크리에이터에게 보내는 가상 아이템 → 다이아몬드로 환전 가능
- 다이아몬드: 선물을 현금화하는 단위 (약 50% 수수료 적용)
- LIVE 구독: 시청자가 크리에이터를 월정액으로 후원하는 기능
- 에이전시/파트너: 크리에이터를 관리하고 수익을 분배하는 MCN 역할
- 팔로워 1000명 이상, 만 18세 이상이어야 라이브 가능
- 경쟁사: 유튜브 라이브, 인스타 라이브, 아프리카TV, 치지직
"""

FOOTER = """

---
요즘 핫한 틱톡 라이브 궁금한 사람?

우리 소속사엔 직장인들부터 모델, 배우, 쇼호스트 등
다양한 직업을 가진 분들이 많아.

부업으로 시작하면서 꾸준히 하루 3~4시간만 방송해도
월 100만 원 ~ 3천만 원 이상의 수익을 낼 수 있다고 !

궁금하면 오픈채팅 줘
https://open.kakao.com/o/sKMhVUUh"""

def search_web(query: str) -> str:
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
            },
            timeout=10,
        )
        results = response.json().get("results", [])
        if not results:
            return ""
        summary = "\n".join([f"- {r['title']}: {r['content'][:200]}" for r in results])
        return f"\n\n[최신 검색 결과]\n{summary}"
    except Exception:
        return ""

def get_keywords(context) -> str:
    if context.args:
        return " ".join(context.args)
    return ""

def generate_text(user_prompt: str, keywords: str = "", use_search: bool = False) -> str:
    keyword_str = f"\n\n⚠️ 반드시 '{keywords}' 키워드를 중심으로 작성해. 다른 주제로 빠지면 안 돼." if keywords else ""
    search_str = search_web(f"틱톡라이브 {keywords}") if use_search and keywords else ""
    full_prompt = user_prompt + keyword_str + search_str

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt},
        ],
    )
    return response.choices[0].message.content + FOOTER

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕. 틱톡라이브 콘텐츠 봇이야.\n\n"
        "📌 명령어 목록:\n"
        "/today [키워드] - 오늘의 콘텐츠\n"
        "/news [키워드] - 최신 뉴스\n"
        "/insight [키워드] - 인사이트\n"
        "/tip [키워드] - 실전 꿀팁\n"
        "/sales [키워드] - 영업 전략\n\n"
        "💡 예시: /today 수익화  /tip 선물"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(
        "오늘 올릴 콘텐츠 1개 작성해줘.",
        keywords, use_search=True
    )
    await msg.edit_text(text)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(
        "틱톡라이브 관련 최신 뉴스 1개를 스레드 스타일로 작성해줘.",
        keywords, use_search=True
    )
    await msg.edit_text(text)

async def insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(
        "틱톡라이브 크리에이터/파트너가 알아야 할 인사이트 1개를 깊게 써줘.",
        keywords, use_search=True
    )
    await msg.edit_text(text)

async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(
        "틱톡라이브 실전 꿀팁 1개를 구체적으로 알려줘.",
        keywords
    )
    await msg.edit_text(text)

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(
        "틱톡라이브 파트너십 영업에 쓸 수 있는 멘트나 전략 1개를 작성해줘.",
        keywords
    )
    await msg.edit_text(text)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("insight", insight))
app.add_handler(CommandHandler("tip", tip))
app.add_handler(CommandHandler("sales", sales))
app.run_polling()
