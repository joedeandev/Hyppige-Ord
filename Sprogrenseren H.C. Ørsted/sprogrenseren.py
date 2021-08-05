# bevar det danske sprog
from os.path import splitext
from sqlite3 import connect as forbind

from bs4 import BeautifulSoup as SmukSuppe

html_sti = "Sprogrenseren H.C. Ørsted.html"
csv_sti = "sprogrenseren-hcø.csv"
db_sti = "../dawiki.db"

with open(html_sti, "r", encoding="utf8") as f:
    suppe = SmukSuppe(f.read(), features="html.parser")

er_fed_skrift = {}
for stilark in suppe.find_all("style")[0]:
    for linje in stilark.split("\n"):
        if not linje.split(".")[0] in ["span", "div"]:
            continue
        er_fed_skrift[linje.split("{")[0]] = "font-weight:bold;" in linje

alle_ord = set()
hoved_ord = set()
aktiveret = False
tidliger_ord = None

for div in suppe.find_all("div"):
    if "width:595px;" in div["style"]:
        continue
    if "left:292.92px;" in div["style"] and div.get_text() == "A":
        aktiveret = True
    er_hoved_ord_div = "left:99.47px;" in div["style"]
    for index, span in enumerate(div.find_all("span")):
        if not aktiveret:
            continue
        if not er_fed_skrift[f'span.{span["class"][0]}']:
            continue

        tekst = span.get_text().lower()
        er_hoved_ord = er_hoved_ord_div and index == 0

        if len(tekst.split(" ")[-1]) == 1:
            tekst = tekst[:-1]
        while len(tekst) > 0 and tekst[0] == " ":
            tekst = tekst[1:]
        while len(tekst) > 0 and tekst[-1] == " ":
            tekst = tekst[:-1]
        if len(tekst) <= 1:
            continue
        if tekst[-1] == "-":
            continue

        if er_hoved_ord:
            if tekst[0] == "-":
                continue
            tidliger_ord = tekst
            hoved_ord.add(tekst)
        else:
            if tekst[0] == "-":
                tekst = tekst[1:]
            if not tekst[0].isupper():
                tekst = tidliger_ord + tekst
        alle_ord.add(tekst)

with open(
    splitext(csv_sti)[0] + "-aa" + splitext(csv_sti)[1], "w", encoding="utf8"
) as udskrivningsfil:
    udskrivningsfil.write("\n".join(sorted([_ for _ in alle_ord])))

aa_ord = set([_.replace("aa", "å") for _ in alle_ord])
with open(
    splitext(csv_sti)[0] + "-å" + splitext(csv_sti)[1], "w", encoding="utf8"
) as udskrivningsfil:
    udskrivningsfil.write("\n".join(sorted([_ for _ in aa_ord])))

for tekst in [_ for _ in aa_ord]:
    alle_ord.add(tekst)

with open(csv_sti, "w", encoding="utf8") as udskrivningsfil:
    udskrivningsfil.write("\n".join(sorted([_ for _ in alle_ord])))

forbindelse = forbind(db_sti)
markoer = forbindelse.cursor()
brugte_ord = []
for tekst in sorted(list(alle_ord)):
    markoer.execute("SELECT * FROM words_nocase WHERE word = ?", (tekst,))
    svar = markoer.fetchone()
    if svar is None:
        continue
    optaelling = svar[1]
    brugte_ord.append((optaelling, tekst))
brugte_ord.sort(reverse=True)

with open(
    splitext(csv_sti)[0] + "-wiki" + splitext(csv_sti)[1], "w", encoding="utf8"
) as udskrivningsfil:
    udskrivningsfil.write(
        "\n".join(["Ord,Optælling"] + [f"{_[1]},{_[0]}" for _ in brugte_ord])
    )

forbindelse.close()
