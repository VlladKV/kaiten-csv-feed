#!/usr/bin/env python3
# generate_csv.py – формирует CSV с кратким TextRank-резюме и кладёт файл в корень репо
import os, csv, io, requests, pathlib
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

# --- Конфигурация передаётся из Secrets GitHub Actions ---
KAITEN_TOKEN = os.environ["KAITEN_TOKEN"]      # Api-Key ... (секрет)
BOARD_ID     = os.environ["BOARD_ID"]          # 123456

CSV_PATH  = pathlib.Path("kaiten_cards.csv")
API_URL   = f"https://app.kaiten.ru/api/v1/boards/{BOARD_ID}/cards"

def text_rank_summary(text: str) -> str:
    """Возвращает одну фразу-конспект (≤25 слов) на русском."""
    parser = PlaintextParser.from_string(text, Tokenizer("russian"))
    summarizer = TextRankSummarizer()
    sentences = summarizer(parser.document, 1)  # 1 предложение
    return str(next(iter(sentences))) if sentences else text[:120]

# --- Тянем карточки ---
cards = requests.get(
    API_URL,
    headers={"Authorization": f"Api-Key {KAITEN_TOKEN}"},
    timeout=30
).json()

# --- Пишем CSV в память ---
buf = io.StringIO()
w   = csv.writer(buf)
w.writerow(["Date", "Title", "Manager", "Summary", "AISummary", "Link"])

for c in cards:
    date     = c["updated"][:10]
    title    = c["name"]
    manager  = c.get("responsible", {}).get("name", "")
    summary  = (c.get("description") or "").replace("\n", " ").strip()
    ai_sum   = text_rank_summary(f"{title}. {summary}")
    link     = f"https://app.kaiten.ru/space/board/{BOARD_ID}/card/{c['id']}"
    w.writerow([date, title, manager, summary, ai_sum, link])

CSV_PATH.write_text(buf.getvalue(), encoding="utf-8")
print("✔ CSV создан: kaiten_cards.csv")
