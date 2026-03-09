from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
import requests
import os
import json

load_dotenv("tiktok_bot.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")

SYSTEM_PROMPT = """
너는 틱톡라이브 전문 콘텐츠 파트너다.
친근하고 쉽게 반말로 쓴다.
광고 냄새 금지, 딱딱한 설명체 금지.
주제는 틱톡라이브 최신 뉴스 / 인사이트 / 영업 / 팁이다.
콘텐츠는 항상 1개만 작성해. 여러 개 나열하지 마.

글쓰기 형식 규칙:
- 내용의 양은 줄이지 마. 그대로 유지해.
- 문장이 끝날 때마다 줄바꿈 해.
- 새로운 내용이 시작될 때 빈 줄 하나 추가해.
- 쉼표가 많은 긴 문장은 마침표로 끊어서 여러 줄로 나눠.
- **굵게**, *기울기* 같은 마크다운 절대 쓰지 마.
- 이모지는 2~3개만 써.

틱톡라이브 전문 지식:
- LIVE Center: 크리에이터가 라이브 성과, 수익, 통계를 확인하는 대시보드
- 선물(Gift): 시청자가 라이브 중 크리에이터에게 보내는 가상 아이템 → 다이아몬드로 환전 가능
- 다이아몬드: 선물을 현금화하는 단위
- 현금화 방법 : 페이코, 페이팔, 페이오니아가 있다. 페이팔이 가장 쉽고 간편하지만 일정 금액 이상 수입이 발생했을 땐 수수료 절감을 위해 페이오니아 가입을 추천. 하이퍼네트웍스에서는 페이오니아 가입을 위한 프로세스도 준비.
- LIVE 구독: 시청자가 크리에이터를 월정액으로 후원하는 기능
- 에이전시/파트너: 크리에이터 관리
- 팔로워 1000명 이상, 만 18세 이상이어야 라이브가 가능하지만 에이전시가 있으면 팔로워가 0명이라도 가능하다.
- 하이퍼네트웍스 : 틱톡라이브 전문 에이전시로 국내에서 가장 유명한 에이전시
- 하이퍼네트웍스가 유명한 이유 : 체계적인 호스트 관리, 투명한 정산, 월마다 진행되는 에이전시 이벤트, 협찬 지원 등
- 틱톡라이브는 방송만이 아니라 운영도 중요 : 댓글 관리, 모더레이터, 차단, 필터링 같은 기능을 활용해 소통에 좋은 채팅 관리가 중요하다
- 라이브 준비 : 라이브 켜기 3시간 전 스토리로 라이브 시간을 미리 공지하는 것이 좋다.
- 매치 : 틱톡라이브에는 매치라는 시스템을 통해 다른 호스트들과 소통하면서 수익을 낼 수 있다.
"""

FOOTER = """요즘 핫한 틱톡 라이브 궁금한 사람?

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
            json={"api_key": TAVILY_API_KEY, "query": query, "search_depth": "basic", "max_results": 3},
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

def split_into_chunks(text: str, max_len: int = 480) -> list:
    """텍스트를 500자 이내 청크로 분할 (최대 3개)"""
    chunks = []
    while len(text) > max_len and len(chunks) < 2:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    chunks.append(text[:max_len].strip())
    return chunks[:3]

def post_to_threads(text: str) -> str:
    """Threads에 본문 + 댓글 체인으로 발행"""
    try:
        chunks = split_into_chunks(text)

        # 1. 본문 게시
        res = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
            params={"text": chunks[0], "media_type": "TEXT", "access_token": THREADS_ACCESS_TOKEN}
        ).json()
        container_id = res.get("id")
        if not container_id:
            return f"❌ 본문 생성 실패: {res}"

        pub = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
            params={"creation_id": container_id, "access_token": THREADS_ACCESS_TOKEN}
        ).json()
        post_id = pub.get("id")
        if not post_id:
            return f"❌ 본문 발행 실패: {pub}"

        # 2. 이어지는 댓글들
        reply_to = post_id
        for chunk in chunks[1:]:
            res = requests.post(
                f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
                params={"text": chunk, "media_type": "TEXT", "reply_to_id": reply_to, "access_token": THREADS_ACCESS_TOKEN}
            ).json()
            cid = res.get("id")
            if not cid:
                break
            pub = requests.post(
                f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
                params={"creation_id": cid, "access_token": THREADS_ACCESS_TOKEN}
            ).json()
            reply_to = pub.get("id", reply_to)

        # 3. 고정 하단 문구 댓글
        res = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
            params={"text": FOOTER, "media_type": "TEXT", "reply_to_id": reply_to, "access_token": THREADS_ACCESS_TOKEN}
        ).json()
        cid = res.get("id")
        if cid:
            requests.post(
                f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
                params={"creation_id": cid, "access_token": THREADS_ACCESS_TOKEN}
            )

        return "✅ 스레드 발행 완료!"
    except Exception as e:
        return f"❌ 오류: {str(e)}"

def generate_text(user_prompt: str, keywords: str = "", use_search: bool = False) -> str:
    keyword_str = f"\n\n⚠️ 반드시 '{keywords}' 키워드를 중심으로 작성해. 다른 주제로 빠지면 안 돼." if keywords else ""
    search_str = search_web(f"틱톡라이브 {keywords}" if keywords else "틱톡라이브 최신 뉴스") if use_search else ""
    full_prompt = user_prompt + keyword_str + search_str

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt},
        ],
    )
    return response.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕. 틱톡라이브 콘텐츠 봇이야.\n\n"
        "📌 명령어 목록:\n"
        "/today [키워드] - 오늘의 콘텐츠\n"
        "/news [키워드] - 최신 뉴스\n"
        "/insight [키워드] - 인사이트\n"
        "/tip [키워드] - 실전 꿀팁\n"
        "/sales [키워드] - 영업 전략\n\n"
        "💡 생성 후 아래 버튼으로 스레드 바로 발행 가능!"
    )

async def handle_content(update, context, prompt, keywords, use_search=False):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(prompt, keywords, use_search)

    # 텔레그램에 미리보기 표시
    preview = text[:300] + ("..." if len(text) > 300 else "")
    await msg.edit_text(
        f"{preview}\n\n"
        f"---\n스레드에 발행할까요?\n"
        f"/publish 입력하면 바로 발행돼요!"
    )
    # 발행용 전체 텍스트 임시 저장
    context.user_data["pending_post"] = text

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "오늘 올릴 콘텐츠 1개 작성해줘.", keywords, use_search=True)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 관련 최신 뉴스 1개를 스레드 스타일로 작성해줘.", keywords, use_search=True)

async def insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 인사이트 1개를 써줘. 사람들의 이목을 확 끄는 첫 문장으로 시작해. 내용은 함축적으로 핵심만, 너무 길지 않게. 읽고 나서 '오 몰랐다' 또는 '나도 해봐야겠다' 는 느낌이 들게 써.", keywords, use_search=True)

async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 실전 꿀팁 1개를 구체적으로 알려줘.", keywords)

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 파트너십 영업에 쓸 수 있는 멘트나 전략 1개를 작성해줘.", keywords)

async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get("pending_post")
    if not text:
        await update.message.reply_text("❌ 발행할 콘텐츠가 없어요. 먼저 /today 같은 명령어로 콘텐츠를 생성해줘!")
        return
    msg = await update.message.reply_text("스레드 발행 중...")
    result = post_to_threads(text)
    await msg.edit_text(result)
    context.user_data["pending_post"] = None

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("insight", insight))
app.add_handler(CommandHandler("tip", tip))
app.add_handler(CommandHandler("sales", sales))
app.add_handler(CommandHandler("publish", publish))
app.run_polling()
