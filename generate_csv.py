import os, csv, io, pathlib, sys, requests
from datetime import datetime as dt

# ---- TextRank (sumy) -------------------------------------------------------
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

def text_rank_summary(text: str) -> str:
    """Вернуть одно предложение-резюме (≤25 слов)."""
    parser = PlaintextParser.from_string(text, Tokenizer("russian"))
    summarizer = TextRankSummarizer()
    sentences = summarizer(parser.document, 1)  # хотим одну фразу
    return str(next(iter(sentences))) if sentences else text[:120]


# ---- Конфигурация из секретов GitHub Actions -------------------------------
try:
    KAITEN_TOKEN = os.environ["KAITEN_TOKEN"]          # Api-Key <…>
    BOARD_ID     = os.environ["BOARD_ID"]              # 123456
except KeyError as e:
    sys.exit(f"❌ Отсутствует переменная окружения: {e.args[0]}")

API_URL  = f"https://app.kaiten.ru/api/v1/boards/{BOARD_ID}/cards"
CSV_PATH = pathlib.Path("kaiten_cards.csv")

# ---- Запрашиваем Kaiten -----------------------------------------------------
resp = requests.get(API_URL,
                    headers={"Authorization": f"Api-Key {KAITEN_TOKEN}"},
                    timeout=30)

if resp.status_code != 200:
    print(f"✖ Kaiten API error: HTTP {resp.status_code}")
    print("----- ответ сервера (первые 500 символов) -----")
    print(resp.text[:500])
    sys.exit(1)

try:
    cards = resp.json()
except ValueError:
    print("✖ Не удалось разобрать ответ как JSON.")
    print(resp.text[:500])
    sys.exit(1)

print(f"✔ Получено {len(cards)} карточек")

# ---- Формируем CSV в памяти -------------------------------------------------
buf = io.StringIO()
w   = csv.writer(buf)
w.writerow(["Date", "Title", "Manager", "Summary", "AISummary", "Link"])

for c in cards:
    date    = (c.get("updated") or c.get("created", ""))[:10]
    title   = c.get("name", "")
    manager = c.get("responsible", {}).get("name", "")
    summary = (c.get("description") or "").replace("\n", " ").strip()

    # краткое
