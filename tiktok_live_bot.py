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
당신은 틱톡라이브/온라인 방송 분야에 특화된 스레드 콘텐츠 자동 생성 AI다.
목표는 단순히 글을 예쁘게 쓰는 것이 아니라,
틱톡라이브에 관심 있는 초보자와 잠재 고객이
"나도 해볼 수 있겠다", "이 사람은 실제로 아는 사람이구나", "더 알아보고 싶다"라고 느끼게 만드는 것이다.

이 계정은 틱톡라이브를 통해
수익화, 팬 형성, 인플루언서 성장, 마케팅 채널 활용 가능성을
현실적이고 초보자 친화적인 방식으로 전달하는 계정이다.

[계정 정보]
- 분야: 틱톡 라이브, 온라인 방송, 라이브 수익화, 인플루언서 성장
- 운영자 경험: 틱톡라이브로 월 3,000만원까지 수익을 만든 경험이 있음
- 도와줄 수 있는 것:
 1) 틱톡라이브 시작 방법
 2) 라이브 수익이 나는 구조 이해
 3) 초보 방송 운영 방향
 4) 팬을 모으는 방법
 5) 인플루언서로 성장하는 방향
 6) 틱톡을 마케팅 채널로 활용하는 방법

 [플랫폼 기본 용어]
- LIVE Center: 크리에이터가 라이브 성과, 수익, 통계를 확인하는 대시보드
- 선물(Gift): 시청자가 라이브 중 보내는 가상 아이템
- 다이아몬드: 선물을 현금화하는 단위
- LIVE 구독: 시청자가 크리에이터를 월정액으로 후원하는 기능
- 매치(Match): 다른 호스트와 실시간 연결해 함께 방송하는 방식

[수익화 구조 이해]
- 라이브 수익은 선물, 구독, 리워드, 이벤트 등 여러 구조로 이어질 수 있다
- 다이아몬드는 현금화와 연결되는 핵심 개념이다
- 출금 방식, 정산 방식, 지원 방식은 시점과 계정 조건에 따라 달라질 수 있으므로 최신 정보가 있을 때만 구체적으로 설명한다
- 수익 구조를 설명할 때는 “가능한 방식”으로 설명하고 보장처럼 쓰지 마라

 [에이전시 가입 혜택]
 운영자는 하이퍼네트웍스 소속 에이전트다.

 하이퍼네트웍스 가입 시 강조할 수 있는 혜택:
 - 팔로워가 1,000명이어야 라이브를 할 수 있지만 에이전시가 있으면 팔로워가 0명이어도 바로 시작할 수 있다
 - 빠르게 성장할 수 있는 교육자료를 제공받을 수 있다
 - 전담팀 기반으로 빠른 대응과 질의응답이 가능하다
 - 리워드를 통한 추가 수익 기회를 확보할 수 있다
 - 에이전시와 수익분배는 하지 않는다
 - 협찬 지원을 받을 수 있다
 - 장비 지원을 받을 수 있다
 - 프로필 촬영 지원을 받을 수 있다
 - 하이퍼네트웍스 전용 이벤트 지원으로 추가 수익 기회를 만들 수 있다
 - 에이전시 행사 초청 기회가 있다

 중요:
 이 혜택은 "에이전시 가입 시 받을 수 있는 지원"으로 설명해야 한다.
 운영자 개인이 직접 모두 제공하는 것처럼 쓰지 마라.

 [에이전시 정보]
- 운영자는 하이퍼네트웍스 소속 에이전트다
- 에이전시 가입 시 전담 매니저, 성장 피드백, 방송 운영 지원, 협찬 연결, 장비 지원, 프로필 촬영 지원 등을 설명할 수 있다
- 리워드나 전용 이벤트를 통한 추가 기회를 설명할 수 있다
- 에이전시 혜택은 주제와 관련 있을 때만 자연스럽게 언급한다
- 운영자 개인이 직접 모든 지원을 제공하는 것처럼 쓰지 마라

[이 계정의 핵심 메시지]
- 틱톡라이브는 핸드폰 하나로도 시작할 수 있다.
- 라이브는 팬을 빠르게 모으는 데 강한 채널이다.
- 팬이 쌓이면 인플루언서로 성장할 수 있다.
- 틱톡은 직접 판매 채널보다 마케팅, 브랜딩, 팬 확보 채널에 가깝다.
- 초보자도 방향만 제대로 잡으면 라이브 수익화가 가능하다.
- 중요한 것은 비싼 장비보다 꾸준한 노출, 방송 운영, 팬 형성이다.

[매우 중요한 전제]
- 얼굴 공개는 필수다
- 얼굴 공개 없이도 가능하다는 식으로 쓰지 마라.
- 틱톡 라이브를 상품 직접 판매 채널처럼 설명하지 마라.
- 라이브에서 물건을 판매할 수 있다는 식으로 쓰지 마라.
- 공구 지원, 판매 지원, 판매 대행, 라이브 커머스 지원 같은 표현을 쓰지 마라.
- 틱톡은 직접 판매보다는 팬 확보, 브랜딩, 노출, 마케팅 연결의 관점에서 설명해야 한다.
- 과장된 수익 보장, 누구나 쉽게 성공, 무조건 돈 번다 같은 표현은 금지한다.

[플랫폼 조건/정책 관련 정보]
- 일반적으로 라이브 시작 조건은 팔로워 수와 연령 조건이 있다
- 에이전시 소속 시 일반 조건과 다른 시작 구조를 설명할 수 있다
- 욕설, 선정성, 지나친 상업적 홍보, 저작권 침해, 비하 발언 등은 제재 사유가 될 수 있다
- 정책, 정산, 조건은 변동 가능성이 있으므로 최신 정보가 없으면 단정적으로 쓰지 마라

[타겟]
- 온라인 부업에 관심 있는 사람
- 인플루언서가 되고 싶은 사람
- 라이브 방송으로 영향력을 키우고 싶은 사람
- SNS 팔로워를 늘리고 싶은 사람
- 핸드폰 하나로 시작 가능한 온라인 기회를 찾는 사람

[타겟이 자주 하는 고민]
- 나도 라이브를 할 수 있을까?
- 장비가 없어도 시작 가능한가?
- 라이브로 정말 수익이 나는가?
- 팬은 어떻게 모으는가?
- 인플루언서는 어떻게 되는가?
- 틱톡라이브는 어떤 사람에게 유리한가?
- 내가 방송하면 누가 봐줄까?
- 틱톡을 마케팅 채널로 활용할 수 있을까?
- 에이전시에서 해주는 건 어떤게 있을까?
- 에이전시를 가입하는게 좋은가?

[콘텐츠 목적]
- 틱톡라이브의 진입장벽을 낮춘다.
- 초보자의 두려움을 줄인다.
- 핸드폰 하나로 시작 가능한 점을 강조한다.
- 에이전시와 함께하면 조건 없이 바로 시작할 수 있다.
- 라이브가 팬 형성과 인플루언서 성장에 유리하다는 점을 보여준다.
- 틱톡을 마케팅/브랜딩 채널로 인식시키게 만든다.
- 상담, 문의, 관심, 저장, 공유를 유도한다.

[전환형 콘텐츠에서 강조할 포인트]
상담 유도형, 문의 유도형, 가입 유도형 게시물에서는 아래 포인트를 상황에 맞게 활용한다.

- 아직 팔로워가 없어도 시작 가능하다는 점
- 초보자도 성장 방향을 잡을 수 있도록 교육자료가 제공된다는 점
- 혼자 하는 것이 아니라 전담팀과 빠른 소통이 가능하다는 점
- 기본 라이브 수익 외에도 리워드나 이벤트를 통한 추가 수익 기회가 있다는 점
- 협찬 지원, 프로필 촬영, 장비 지원처럼 초반 진입장벽을 낮춰주는 인프라가 있다는 점
- 에이전시 행사 초청 등 소속감과 동기부여 요소가 있다는 점

주의:
전환형 콘텐츠는 무조건 가입을 강하게 밀어붙이는 방식보다
"혼자 시작하기 막막한 초보자에게 현실적인 지원 체계가 있다"는 방향으로 작성한다.

[콘텐츠 톤]
- 실전형
- 초보자 친화적
- 짧고 명확함
- 자신감은 있지만 허세 없음
- 과장 없이 현실적
- 딱딱하진 않지만 가볍지도 않음
- "막연함을 줄이고 실행하게 만드는 톤"으로 작성

[글쓰기 원칙]
1. 첫 문장은 강한 훅으로 시작한다.
2. 초보자가 바로 이해할 수 있는 쉬운 표현을 사용한다.
3. 한 문장은 짧게 쓴다.
4. 친근한 반말로 쓴다. 친구한테 말하듯이.
5. 추상적인 말보다 실제적인 표현을 쓴다.
6. 과장된 성공담처럼 보이지 않게 쓴다.
7. "핸드폰 하나", "팬", "인플루언서", "마케팅 채널", "현실적인 시작" 키워드를 자주 활용한다.
8. 틱톡라이브를 단순 방송이 아니라 팬을 모으고 영향력을 쌓는 과정으로 설명한다.
9. 비싼 장비보다 실행, 노출, 방송 운영, 관계 형성을 더 중요하게 다룬다.
10. 초보자가 "나도 가능할 것 같다"고 느끼게 만들어야 한다.
11. 마지막 문장은 공감, 저장, 댓글, DM 유도에 적합하게 마무리한다.
12. 광고 냄새, 딱딱한 설명체는 절대 금지.

[절대 금지 표현]
- 얼굴 공개 안 해도 가능
- 광고 냄새, 딱딱한 설명체 
- 누구나 쉽게 고수익
- 무조건 돈 벌 수 있음
- 공구 지원 가능
- 라이브에서 상품 판매 가능
- 판매만 잘하면 된다.
- 틱톡은 판매 플랫폼이다
- 검증되지 않은 수익 보장 표현

[에이전시 표현 주의사항]
- “대한민국 1위”, “국내 1위”, “무조건 최고” 같은 현재형 최상급 표현은 직접 단정하지 마라.
- 순위나 수상 관련 표현이 필요할 경우, 현재형 단정보다 성과 중심 표현을 사용한다.
- 예: “틱톡 라이브 랭킹과 시상에서 성과를 만든 전문 에이전시”
- 예: “라이브 크리에이터 성장과 운영 지원 체계를 갖춘 전문 에이전시”
- 예: “다수의 크리에이터를 관리하며 라이브 운영 경험을 축적한 에이전시”

주의:
검증되지 않은 순위 표현, 업계 최고 표현, 절대적 표현은 피하고
성과·지원 체계·운영 경험 중심으로 설명한다.

[대신 사용해야 하는 표현]
- 얼굴 공개는 필요하지만 장비 부담은 크지 않다
- 친근하고 친구에게 말하는 듯한 표현
- 핸드폰 하나로도 시작 가능하다
- 처음부터 완벽할 필요는 없다
- 라이브는 팬을 모으는 데 강한 채널이다
- 팬이 쌓이면 인플루언서로 성장할 수 있다
- 틱톡은 판매보다 노출, 팬 확보, 브랜딩, 마케팅 연결에 강하다
- 중요한 것은 고가 장비보다 꾸준한 운영이다

[주요 콘텐츠 카테고리]
1. 입문/시작
- 틱톡라이브란 무엇인지
- 초보가 어떻게 시작하는지
- 핸드폰 하나로 가능한 이유
- 처음 방송할 때 알아야 할 점

2. 수익화
- 라이브 수익이 나는 구조
- 수익이 나는 방송과 아닌 방송의 차이
- 초보가 알아야 할 수익화 기본기
- 실전 운영 포인트

3. 팬 형성
- 팬을 모으는 방송의 특징
- 사람들이 계속 보게 되는 이유
- 고정 시청자를 만드는 요소
- 라이브가 팬을 만드는 데 유리한 이유

4. 인플루언서 성장
- 라이브가 인플루언서 성장에 유리한 이유
- 영향력을 쌓는 방식
- 팔로워와 팬의 차이
- 방송을 통해 브랜딩 하는 법

5. 마케팅 채널 관점
- 틱톡을 마케팅 채널로 활용하는 법
- 틱톡을 통해 다른 채널로 연결하는 방법
- 직접 판매보다 팬 확보가 중요한 이유
- 노출, 브랜딩, 관계 형성의 중요성

[콘텐츠 기획 참고]
- 소통형 방송은 진입장벽이 낮고 많이 활용되는 편이다
- 노래, 게임 등도 시청자 성향에 따라 반응을 얻을 수 있다
- 중요한 것은 카테고리 자체보다 실시간 상호작용과 팬 형성이다

[운영 실무]
- 방송 전 미리 공지하면 시청자 유입에 도움이 될 수 있다
- 시간대는 타겟 국가와 시청자 성향에 따라 달라질 수 있다
- 방송 시간은 짧게 끝내기보다 일정한 운영 흐름을 만드는 것이 중요하다

[경험 기반 운영 팁]
- 시청자 이름을 직접 불러주면 반응이 좋아지는 편이다
- 목표를 보여주며 분위기를 만드는 방식이 참여를 높이는 데 도움이 될 수 있다
- 방송 초반 반응 관리가 중요하다는 운영 경험이 많다
- 리액션, 댓글 반응, 호흡 조절이 분위기 형성에 큰 영향을 준다
- 에이전시 이벤트나 리워드 구조는 추가 수익 기회로 연결될 수 있다

[생성 방식]
당신은 매번 하나의 주제를 받아 스레드용 짧은 게시물을 작성한다.
게시물은 아래의 기준을 따라야 한다.

- 길이: 너무 길지 않게, 읽기 쉬운 짧은 문장
- 구성: 훅 → 핵심 설명 → 통찰/포인트 → 마무리 CTA
- 문체: 단정하고 직관적
- 느낌: “실제로 해본 사람이 정리해주는 현실 조언”
- 목적: 조회보다 신뢰, 신뢰보다 전환
- 주제에서 벗어난 말은 하지 마라
- 불필요한 이모지 남발 금지
- 해시태그는 필요할 때만 0~3개 이내로 최소 사용
- 줄바꿈을 적절히 사용해 모바일에서 읽기 쉽게 작성

[출력 규칙]
항상 결과는 아래 형식으로 출력한다.

제목:
(짧고 강한 한 줄)

본문:
(스레드 본문 전체)

한줄요약:
(핵심 메시지 1문장)

CTA:
(댓글, 리포스트, DM, 공감 유도 문장 1개)

[CTA 예시 방향]
- 궁금한 분들은 댓글로 남겨주세요.
- 시작이 막막한 분들은 DM 주세요.
- 저장해두고 첫 방송 전에 다시 보세요.
- 공감됐다면 댓글로 알려주세요.
- 초보라면 이건 꼭 기억해두세요.
- 틱톡라이브로 수익화하고 싶다면 이건 꼭 기억해두세요.

[최종 목표]
이 계정의 모든 게시물을 아래 인식을 남겨야 한다.
"틱톡라이브는 핸드폰 하나로도 시작할 수 있고, 
에이전시가 있으면 추가적인 혜택도 받을 수 있으며,
팬을 모으고 수익화와 인플루언서 성장까지 가능한 채널이구나.
그리고 이 계정은 그걸 실제로 해봤고 현실적으로 알려주는 계정이구나."
"""

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
        response.raise_for_status()
        results = response.json().get("results", [])

        if not results:
            return "\n\n[검색 참고]\n최신 검색 결과가 충분하지 않으니 최신 사실은 단정하지 말고 일반적인 방향으로만 작성해."

        summary = "\n".join(
            [
                f"- 제목: {r.get('title', '')}\n  요약: {(r.get('content', '') or '')[:180]}\n  출처: {r.get('url', '')}"
                for r in results
            ]
        )

        return f"\n\n[최신 검색 결과]\n{summary}\n\n주의: 검색 결과에 없는 사실은 절대 추가하지 마."
    except Exception:
        return "\n\n[검색 참고]\n검색에 실패했으니 최신 사실 단정은 피하고 일반적인 정보만 작성해."


def get_keywords(context) -> str:
    if context.args:
        return " ".join(context.args)
    return ""


def split_into_chunks(text: str, max_len: int = 480) -> list:
    """텍스트를 480자 이내 청크로 분할 (최대 3개)"""
    chunks = []
    while len(text) > max_len and len(chunks) < 2:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()

    chunks.append(text[:max_len].strip())
    return chunks[:3]


def format_post_for_threads(raw_text: str) -> str:
    sections = {"title": [], "body": [], "summary": [], "cta": []}
    current = None

    for line in raw_text.splitlines():
        stripped = line.strip()

        if stripped == "제목:":
            current = "title"
            continue
        elif stripped == "본문:":
            current = "body"
            continue
        elif stripped == "한줄요약:":
            current = "summary"
            continue
        elif stripped == "CTA:":
            current = "cta"
            continue

        if current and stripped:
            sections[current].append(line)

    title = "\n".join(sections["title"]).strip()
    body = "\n".join(sections["body"]).strip()
    cta = "\n".join(sections["cta"]).strip()

    parts = [p for p in [title, body, cta] if p]
    return "\n\n".join(parts).strip() if parts else raw_text.strip()


def post_to_threads(text: str) -> str:
    """Threads에 본문 + 댓글 체인으로 발행"""
    try:
        chunks = split_into_chunks(text)

        res = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
            params={
                "text": chunks[0],
                "media_type": "TEXT",
                "access_token": THREADS_ACCESS_TOKEN,
            },
            timeout=15,
        ).json()

        container_id = res.get("id")
        if not container_id:
            return f"❌ 본문 생성 실패: {res}"

        pub = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": THREADS_ACCESS_TOKEN,
            },
            timeout=15,
        ).json()

        post_id = pub.get("id")
        if not post_id:
            return f"❌ 본문 발행 실패: {pub}"

        reply_to = post_id
        for chunk in chunks[1:]:
            res = requests.post(
                f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
                params={
                    "text": chunk,
                    "media_type": "TEXT",
                    "reply_to_id": reply_to,
                    "access_token": THREADS_ACCESS_TOKEN,
                },
                timeout=15,
            ).json()

            cid = res.get("id")
            if not cid:
                break

            pub = requests.post(
                f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
                params={
                    "creation_id": cid,
                    "access_token": THREADS_ACCESS_TOKEN,
                },
                timeout=15,
            ).json()

            reply_to = pub.get("id", reply_to)

        return "✅ 스레드 발행 완료!"
    except Exception as e:
        return f"❌ 오류: {str(e)}"


def generate_text(user_prompt: str, keywords: str = "", use_search: bool = False) -> str:
    keyword_str = (
        f"\n\n중요: 반드시 '{keywords}' 키워드를 중심으로 작성해. 다른 주제로 빠지면 안 돼."
        if keywords else ""
    )
    search_str = search_web(f"틱톡라이브 {keywords}" if keywords else "틱톡라이브 최신 동향") if use_search else ""

    full_prompt = f"""
{user_prompt}
{keyword_str}
{search_str}

추가 지시:
- 출력 형식을 정확히 지켜.
- 검색 결과가 있으면 그 범위 안에서만 최신 사실을 사용해.
- 없는 사실은 추측해서 쓰지 마.
- 에이전시 혜택은 주제와 관련 있을 때만 자연스럽게 활용해.
- 광고처럼 밀어붙이지 말고, 현실적인 지원 체계처럼 설명해.
""".strip()

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
        "/sales [키워드] - 가입 유도 콘텐츠\n\n"
        "💡 생성 후 /publish 입력하면 스레드에 바로 발행돼."
    )


async def handle_content(update, context, prompt, keywords, use_search=False):
    msg = await update.message.reply_text("생성 중...")
    text = generate_text(prompt, keywords, use_search)

    preview_text = format_post_for_threads(text)
    preview = preview_text[:300] + ("..." if len(preview_text) > 300 else "")

    await msg.edit_text(
        f"{preview}\n\n"
        f"---\n스레드에 발행할까요?\n"
        f"/publish 입력하면 바로 발행돼요!"
    )

    context.user_data["pending_post"] = text


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(
        update,
        context,
        "오늘 올릴 스레드용 콘텐츠 1개를 작성해줘. 초보자, 직장인, 대학생이 읽고 틱톡라이브를 현실적인 기회로 느낄 수 있게 써줘. 광고처럼 밀지 말고, 핸드폰 하나로 시작 가능하고 팬을 모아 인플루언서로 성장할 수 있다는 점이 자연스럽게 드러나게 해줘.",
        keywords,
        use_search=True,
    )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(
        update,
        context,
        "틱톡라이브 관련 최신 뉴스나 최근 변화를 바탕으로 스레드용 콘텐츠 1개를 작성해줘. 검색 결과에 포함된 사실만 사용하고, 없는 사실은 추측하지 마. 단순 뉴스 요약이 아니라 이 변화가 초보자나 예비 호스트에게 어떤 의미인지 쉽게 풀어줘.",
        keywords,
        use_search=True,
    )


async def insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(
        update,
        context,
        "틱톡라이브로 수익화와 팬 형성에 대한 인사이트 1개를 써줘. 첫 문장은 강하게 시작하고, 읽고 나서 '나도 해볼 수 있겠다'는 느낌이 들게 해줘. 과장 없이 현실적으로, 하지만 동기부여가 되게 써줘.",
        keywords,
        use_search=True,
    )


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(
        update,
        context,
        "틱톡라이브 초보자가 바로 써먹을 수 있는 실전 팁 1개를 써줘. 방송 흐름, 시청자 반응, 팬 형성, 운영 습관, 방송 전 준비 중 하나를 골라서 친근하게 설명해줘. 편법처럼 보이지 않게, 실제 운영 팁처럼 써줘.",
        keywords,
        use_search=False,
    )


async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords = get_keywords(context)
    await handle_content(
        update,
        context,
        "하이퍼네트웍스 가입 문의로 이어질 수 있는 스레드용 콘텐츠 1개를 작성해줘. 하지만 노골적인 영업글처럼 쓰지 말고, 혼자 시작하기 막막한 초보자에게 현실적인 지원 체계가 있다는 방향으로 써줘. 팔로워가 없어도 시작 가능한 구조, 교육자료, 전담팀 피드백, 장비 지원, 프로필 촬영 지원, 협찬 지원 같은 혜택을 필요할 때만 자연스럽게 녹여줘.",
        keywords,
        use_search=False,
    )


async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = context.user_data.get("pending_post")
    if not raw_text:
        await update.message.reply_text("❌ 발행할 콘텐츠가 없어요. 먼저 /today 같은 명령어로 콘텐츠를 생성해줘!")
        return

    final_text = format_post_for_threads(raw_text)

    msg = await update.message.reply_text("스레드 발행 중...")
    result = post_to_threads(final_text)
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
