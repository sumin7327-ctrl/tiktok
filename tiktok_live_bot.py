from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 자동 로드

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
너는 틱톡라이브 전문 콘텐츠 파트너다.
친근하고 쉽게 반말로 쓴다.
광고 냄새 금지, 딱딱한 설명체 금지.
주제는 틱톡라이브 최신 뉴스 / 인사이트 / 영업 / 팁이다.
"""

def generate_text(user_prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕. 틱톡라이브 콘텐츠 봇이야.\n"
        "/today /news /insight /tip /sales 중에 입력해봐."
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text("오늘 올릴 콘텐츠 3개 작성해줘. 뉴스형 1개, 인사이트형 1개, 영업형 1개.")
    await msg.edit_text(text)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text("틱톡라이브 관련 최신 뉴스 요약 3개를 스레드 스타일로 작성해줘.")
    await msg.edit_text(text)

async def insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text("틱톡라이브 크리에이터/파트너가 알아야 할 인사이트 1개를 깊게 써줘.")
    await msg.edit_text(text)

async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text("틱톡라이브 실전 꿀팁 1개를 구체적으로 알려줘.")
    await msg.edit_text(text)

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text("틱톡라이브 파트너십 영업에 쓸 수 있는 멘트나 전략 1개를 작성해줘.")
    await msg.edit_text(text)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("insight", insight))
app.add_handler(CommandHandler("tip", tip))
app.add_handler(CommandHandler("sales", sales))
app.run_polling()
