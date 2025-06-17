#!/usr/bin/env python3
# generate_csv.py – формирует CSV с AI-резюме и кладёт его в корень репо
import os, csv, io, requests, pathlib
from openai import OpenAI

KAITEN_TOKEN = os.environ["KAITEN_TOKEN"]          # Api-Key … (секрет GitHub)
BOARD_ID     = os.environ["BOARD_ID"]              # 123456
OPENAI_KEY   = os.environ["OPENAI_API_KEY"]        # секр. GitHub

CSV_PATH     = pathlib.Path("kaiten_cards.csv")
API_URL      = f"https://app.kaiten.ru/api/v1/boards/{BOARD_ID}/cards"

cards = requests.get(API_URL,
                     headers={"Authorization":f"Api-Key {KAITEN_TOKEN}"},
                     timeout=30).json()

ai = OpenAI(api_key=OPENAI_KEY)

buf = io.StringIO()
w   = csv.writer(buf)
w.writerow(["Date","Title","Manager","Summary","AISummary","Link"])

for c in cards:
    date     = c["updated"][:10]
    title    = c["name"]
    manager  = c.get("responsible",{}).get("name","")
    summary  = (c.get("description") or "").replace("\n"," ").strip()

    prompt   = f"Одним предложением (≤25 слов) переформулируй: {title}. {summary}"
    ai_ans   = ai.chat.completions.create(
                  model="gpt-4o-mini",
                  messages=[{"role":"user","content":prompt}]
               ).choices[0].message.content.strip()

    link = f"https://app.kaiten.ru/space/board/{BOARD_ID}/card/{c['id']}"
    w.writerow([date,title,manager,summary,ai_ans,link])

CSV_PATH.write_text(buf.getvalue(), encoding="utf-8")
print("✔ CSV создан: kaiten_cards.csv")
