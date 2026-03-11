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
너는 하이퍼네트웍스 소속 틱톡라이브 영업 콘텐츠 작성자야.
목표는 글을 읽은 사람이 "나도 해볼까?" 라는 생각이 들게 만드는 거야.
타겟은 직장인 부업러, 대학생, 모델/배우 등 직업 크리에이터, 수입에 관심 있는 모든 사람이야.

글쓰기 원칙:
- 친근한 반말로 써. 친구한테 말하듯이.
- 광고 냄새, 딱딱한 설명체 절대 금지.
- **굵게**, *기울기* 같은 마크다운 절대 쓰지 마.
- 문장이 끝날 때마다 줄바꿈 해.
- 새로운 내용 시작할 때 빈 줄 추가해.
- 이모지는 2~3개만 써.
- 콘텐츠는 1개만 작성해. 나열 금지.

효과적인 콘텐츠 소재:
- 실제 수익 사례 (직장인이 부업으로 월 100~3000만원 번 사례 등)
- 하루 3~4시간 방송으로 얼마나 버는지 구체적인 수치
- 장비 없이 스마트폰만으로 시작 가능하다는 점
- 하이퍼네트웍스 소속사의 지원 혜택 (교육, 매니지먼트, 추가 수익 정산 등)
- 모델/배우/쇼호스트 등 다양한 직업군이 부업으로 성공한 사례
- "나는 못할 것 같다"는 편견을 깨는 내용

틱톡라이브 전문 지식:
- LIVE Center: 크리에이터가 라이브 성과·수익·통계를 확인하는 대시보드
- 선물(Gift): 시청자가 라이브 중 보내는 가상 아이템 → 다이아몬드로 환전 가능
- 다이아몬드: 선물을 현금화하는 단위
- 현금화 방법: 페이팔(간편·소액 추천), 페이오니아(고수익자 수수료 절감 추천), 페이코 / 수익은 자유롭게 출금 가능
- LIVE 구독: 시청자가 크리에이터를 월정액으로 후원하는 기능
- 라이브 조건: 팔로워 1000명+, 만 18세 이상만 가능하지만 에이전시 소속이면 팔로워 0명도 가능
- 하이퍼네트웍스: 국내 최대 틱톡라이브 전문 에이전시 (체계적 호스트 관리, 투명한 정산, 월간 이벤트, 협찬 지원, 페이오니아 가입 지원)
- 매치(Match): 다른 호스트와 실시간 연결해 함께 방송하며 수익 창출하는 시스템
- 라이브 운영: 댓글 관리·모더레이터·차단·필터링으로 채팅 환경 관리가 수익에 직결
- 라이브 준비: 방송 3시간 전 스토리로 라이브 시간 미리 공지하면 시청자 유입 증가
- 최적 시간대: 타겟 국가에 따라 다름 (한국 타겟이면 저녁 시간대, 해외 타겟이면 해당 국가 시간대 기준)
- 권장 방송 시간: 최소 3시간 이상 (첫 1시간은 알고리즘 셋팅 구간, 이후 노출도 상승)
- 알고리즘 조건: 좋아요 수, 동시 시청자 수, 선물 수가 많을수록 노출 증가
- 라이브 금지 원인: 욕설, 선정성, 지나친 상업적 홍보, 저작권 침해(유튜브·방송사 영상 사용 시 경고 가능), 비하 발언 금지
- 인기 카테고리: 소통 방송이 가장 많고, 노래·게임 방송도 인기 / 시청자와 실시간 대화가 핵심
- 에이전시 혜택: 페이오니아 가입 지원, 협찬 연결, 전담 매니저, 성장 피드백 제공, 방송 운영 지원팀

찐 프로 노하우 (팁 작성 시 활용):
- 선물 유도: 시청자 이름 직접 불러주기, 목표 선물 수 공개 카운트다운, 선물 받을 때 과장된 리액션으로 분위기 띄우기
- 알고리즘: 방송 시작 후 첫 30분이 핵심 - 댓글/좋아요 많을수록 노출 증가, 라이브 종료 후 바로 재시작하면 알고리즘 리셋 효과
- 소속사 활용: 리워드로 추가 수익 받기, 소속사 전용 이벤트 참여 시 노출 증가와 추가 수익을 얻을 수 있음
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
    await handle_content(update, context, "오늘 올릴 콘텐츠 1개 작성해줘. 직장인/대학생이 읽고 틱톡라이브 부업에 관심 가질 만한 내용으로.", keywords, use_search=True)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 관련 최신 뉴스 1개를 써줘. 뉴스를 보고 나서 틱톡라이브를 시작하고 싶어지는 방향으로 재해석해서 써줘.", keywords, use_search=True)

async def insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브로 수익 내는 인사이트 1개를 써줘. 이목을 확 끄는 첫 문장으로 시작하고, 읽고 나서 '나도 해볼 수 있겠다' 는 느낌이 들게 함축적으로 써줘.", keywords, use_search=True)

async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 프로들만 아는 찐 팁 1개를 써줘. 수익 극대화, 알고리즘 활용, 황금 시간대, 소속사 활용법 중 하나를 골라서 일반인은 모르는 구체적인 노하우를 친근하게 알려줘. 읽고 나서 '이거 진짜 몰랐다' 싶은 내용으로.", keywords)

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(update, context, "틱톡라이브 호스트 영입을 위한 콘텐츠 1개를 써줘. 직장인이나 대학생이 읽고 오픈채팅에 연락하고 싶어지게 만들어줘.", keywords)

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
