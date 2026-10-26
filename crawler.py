import httpx
from bs4 import BeautifulSoup
import mysql.connector
import json
import os
import hashlib
from datetime import datetime
import re
import time
from urllib.robotparser import RobotFileParser

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abcd1234",
    database="theater_crawler"
)
cursor = db.cursor(dictionary=True)

url_baza = "https://www.teatrulmic.ro"
folder_afise = "static/posters"
os.makedirs(folder_afise, exist_ok=True)

headere_browser = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

def permite_robots(url):
    try:
        url_robots = f"{url_baza}/robots.txt"
        raspuns = httpx.get(url_robots, headers=headere_browser, timeout=10.0)
        if raspuns.status_code != 200:
            return True
        rp = RobotFileParser()
        rp.parse(raspuns.text.splitlines())
        return rp.can_fetch(headere_browser["User-Agent"], url)
    except Exception:
        return True

def descarca_afis(url_imagine):
    if not url_imagine:
        return None, None
        
    try:
        if not url_imagine.startswith("http"):
            url_imagine = url_baza + url_imagine
            
        raspuns = httpx.get(url_imagine, headers=headere_browser, timeout=10.0)
        raspuns.raise_for_status()
        
        date_imagine = raspuns.content
        hash_imagine = hashlib.sha256(date_imagine).hexdigest()
        cale_fisier = os.path.join(folder_afise, f"{hash_imagine}.jpg")
        
        if not os.path.exists(cale_fisier):
            with open(cale_fisier, "wb") as f:
                f.write(date_imagine)
            
        return cale_fisier, hash_imagine
    except Exception as e:
        print(f"⚠️ Eroare descărcare afiș: {e}")
        return None, None

def extrage_metadate_spectacol(soup, echipa):
    autor = None
    regizor = None
    durata_text = None
    durata_min = None
    varsta = None
    limba = "Română"

    tag_by = soup.find(class_=re.compile(r"\bby\b", re.I))
    if tag_by:
        text_autor = tag_by.get_text(strip=True)
        autor = re.sub(r"^de\s*[:\-]?\s*", "", text_autor, flags=re.IGNORECASE).strip()

    if not autor:
        subtitlu = soup.find(class_=re.compile(r"subtit|author|subtitle", re.I))
        if subtitlu:
            text_sub = subtitlu.get_text(strip=True)
            autor = re.sub(r"^de\s*[:\-]?\s*", "", text_sub, flags=re.IGNORECASE).strip()

    for membru in echipa:
        rol = membru.get("role", "").lower()
        if "regie" in rol or "regizor" in rol:
            if not regizor:
                regizor = membru.get("name")
        elif "autor" in rol or "text" in rol or "dramaturgie" in rol:
            if not autor:
                autor = membru.get("name")

    text_complet = soup.get_text(" ", strip=True)

    m_durata = re.search(r'(?:durat[aă]|durată)\s*[:\-]?\s*([0-9]+\s*(?:h|ore?|min[a-z]*)\s*(?:[0-9]+\s*min[a-z]*)?)', text_complet, re.IGNORECASE)
    if not m_durata:
        m_durata = re.search(r'(\b[0-9]{1,2}\s*h(?:\s*[0-9]{1,2}\s*min)?|\b[0-9]{2,3}\s*min(?:ute)?)\b', text_complet, re.IGNORECASE)

    if m_durata:
        durata_text = m_durata.group(1).strip()
        ore_match = re.search(r'(\d+)\s*(?:h|ore?)', durata_text, re.I)
        min_match = re.search(r'(\d+)\s*min', durata_text, re.I)
        total = 0
        if ore_match:
            total += int(ore_match.group(1)) * 60
        if min_match:
            total += int(min_match.group(1))
        elif not ore_match and re.search(r'^\d+$', durata_text):
            total = int(durata_text)
        durata_min = total if total > 0 else None

    m_varsta = re.search(r'(\b\d{1,2}\s*\+|\+\s*\d{2}|\b(?:peste|recomandat|vârsta|varsta)\s*\d{1,2}\s*ani|\b\d{1,2}\s*ani\b)', text_complet, re.IGNORECASE)
    if m_varsta:
        gasit = m_varsta.group(1).strip()
        if gasit not in ["+1", "1+"]:
            varsta = gasit
        else:
            m_varsta_alt = re.search(r'(1[2468]\+|1[2468]\s*ani|\+1[2468])', text_complet)
            if m_varsta_alt:
                varsta = m_varsta_alt.group(1)

    return autor, regizor, durata_text, durata_min, varsta, limba

def porneste_crawler():
    url_spectacole = f"{url_baza}/spectacole/"
    if not permite_robots(url_spectacole):
        print("❌ Accesul este interzis prin robots.txt!")
        return

    print("Accesez pagina principală de spectacole...")
    try:
        pagina_principala = httpx.get(url_spectacole, headers=headere_browser, follow_redirects=True, timeout=15.0)
        pagina_principala.raise_for_status()
        soup = BeautifulSoup(pagina_principala.text, "html.parser")
    except Exception as e:
        print(f"❌ Eroare la accesarea paginii principale: {e}")
        return

    toate_tagurile_a = soup.find_all("a", href=True)
    linkuri_spectacole = []
    for tag in toate_tagurile_a:
        href = tag.get("href")
        if "/spectacol/" in href and href not in linkuri_spectacole:
            linkuri_spectacole.append(href)

    print(f"Am găsit {len(linkuri_spectacole)} linkuri unice de spectacole!")

    luni = {
        "ian": 1, "ianuarie": 1, "feb": 2, "februarie": 2, "mar": 3, "martie": 3,
        "apr": 4, "aprilie": 4, "mai": 5, "iun": 6, "iunie": 6, "iul": 7, "iulie": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "septembrie": 9, 
        "oct": 10, "octombrie": 10, "noi": 11, "noiembrie": 11, "dec": 12, "decembrie": 12
    }

    for link in linkuri_spectacole:
        time.sleep(1.0)

        if not permite_robots(link):
            print(f"Omis conform robots.txt: {link}")
            continue

        try:
            pagina_spectacol = httpx.get(link, headers=headere_browser, follow_redirects=True, timeout=15.0)
            pagina_spectacol.raise_for_status()
            soup_spect = BeautifulSoup(pagina_spectacol.text, "html.parser")

            titlu_tag = soup_spect.find("h1", class_="title")
            titlu = titlu_tag.text.strip() if titlu_tag else "Fără titlu"

            desc_tag = soup_spect.find("div", class_="content-info")
            descriere = desc_tag.text.strip() if desc_tag else ""

            afis_tag = soup_spect.find("div", class_="header-show")
            url_afis = None
            if afis_tag and afis_tag.get("style"):
                potrivire_url = re.search(r"url\(['\"]?(.*?)['\"]?\)", afis_tag.get("style"))
                if potrivire_url:
                    url_afis = potrivire_url.group(1)

            cale_afis, hash_afis = descarca_afis(url_afis)

            container_distributie = soup_spect.find("div", class_="distributie")
            distributie = []
            echipa_artistica = []

            if container_distributie:
                linii = [l.strip() for l in container_distributie.get_text(separator="\n").split("\n") if len(l.strip()) > 1]
                suntem_la_actori = False
                i = 0
                while i < len(linii) - 1:
                    stanga = linii[i]
                    dreapta = linii[i+1]
                    if "distributie" in stanga.lower() or "distribuție" in stanga.lower():
                        suntem_la_actori = True
                        i += 1
                        continue
                    if suntem_la_actori:
                        distributie.append({"character": stanga, "name": dreapta})
                    else:
                        echipa_artistica.append({"role": stanga, "name": dreapta})
                    i += 2

            json_distributie = json.dumps(distributie if distributie else [{"name": "Nu a fost publicată"}], ensure_ascii=False)
            json_echipa = json.dumps(echipa_artistica if echipa_artistica else [{"role": "Informație", "name": "Nepublicată"}], ensure_ascii=False)

            autor, regizor, durata_text, durata_min, varsta, limba = extrage_metadate_spectacol(soup_spect, echipa_artistica)

            sql_show = """
                INSERT INTO shows 
                (title, author, director, description, duration_minutes, duration_text, age_recommendation, language, 
                 cast_json, team_json, poster_storage, poster_path, poster_source_url, poster_hash, source_url, last_seen_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'file', %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                    title=VALUES(title),
                    author=VALUES(author),
                    director=VALUES(director),
                    description=VALUES(description),
                    duration_minutes=VALUES(duration_minutes),
                    duration_text=VALUES(duration_text),
                    age_recommendation=VALUES(age_recommendation),
                    language=VALUES(language),
                    cast_json=VALUES(cast_json),
                    team_json=VALUES(team_json),
                    poster_path=VALUES(poster_path),
                    poster_hash=VALUES(poster_hash),
                    last_seen_at=NOW()
            """
            cursor.execute(sql_show, (
                titlu, autor, regizor, descriere, durata_min, durata_text, varsta, limba,
                json_distributie, json_echipa, cale_afis, url_afis, hash_afis, link
            ))
            db.commit()

            cursor.execute("SELECT id FROM shows WHERE source_url = %s", (link,))
            id_spectacol = cursor.fetchone()["id"]

            elemente_calendar = soup_spect.find_all("div", class_="left")
            for element in elemente_calendar:
                date_tag = element.find("span", class_="date")
                time_tag = element.find("span", class_="time")

                rand_eveniment = element.find_parent("div", class_=re.compile(r"item|row|program", re.I))
                if not rand_eveniment:
                    rand_eveniment = element.parent

                url_bilet = None
                if rand_eveniment:
                    tag_bilet = rand_eveniment.find("a", href=re.compile(r"ticketsys|bilet|ticket|event", re.I))
                    if not tag_bilet:
                        tag_bilet = rand_eveniment.find("a", href=True)
                    
                    if tag_bilet and tag_bilet.get("href"):
                        href_curat = tag_bilet["href"].strip()
                        if href_curat.startswith("http"):
                            url_bilet = href_curat
                        elif href_curat.startswith("/"):
                            url_bilet = f"{url_baza}{href_curat}"

                url_final_reprezentatie = url_bilet if url_bilet else link

                if date_tag and time_tag:
                    text_ora = time_tag.text.strip()
                    zi, luna, an = None, None, None

                    if url_bilet:
                        m_url = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', url_bilet)
                        if m_url:
                            zi = int(m_url.group(1))
                            luna = int(m_url.group(2))
                            an = int(m_url.group(3))

                    if not (zi and luna and an):
                        text_complet_rand = rand_eveniment.get_text(" ", strip=True).lower() if rand_eveniment else date_tag.text.strip().lower()
                        
                        m_data = re.search(r'(\d{1,2})[-./](\d{1,2})[-./](\d{4})', text_complet_rand)
                        if m_data:
                            zi = int(m_data.group(1))
                            luna = int(m_data.group(2))
                            an = int(m_data.group(3))
                        else:
                            m_zi = re.search(r'\b(\d{1,2})\b', date_tag.text)
                            if m_zi:
                                zi = int(m_zi.group(1))
                                mapare_luni = {
                                    'ian': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                                    'mai': 5, 'iun': 6, 'iul': 7, 'aug': 8,
                                    'sep': 9, 'oct': 10, 'noi': 11, 'dec': 12
                                }
                                for nume_luna, nr in mapare_luni.items():
                                    if nume_luna in text_complet_rand:
                                        luna = nr
                                        break
                                an = datetime.now().year

                    if luna is not None and an is not None:
                        acum = datetime.now()
                        if acum.month >= 9 and luna < 9:
                            an = acum.year + 1

                    if zi and luna and an and ":" in text_ora:
                        ora, minut = text_ora.split(":")
                        data_finala = datetime(an, luna, zi, int(ora), int(minut))

                        sql_perf = """
                            INSERT INTO performances (show_id, start_at, venue, source_url, last_seen_at) 
                            VALUES (%s, %s, 'Teatrul Mic', %s, NOW())
                            ON DUPLICATE KEY UPDATE 
                                venue=VALUES(venue),
                                source_url=VALUES(source_url),
                                last_seen_at=NOW()
                        """
                        cursor.execute(sql_perf, (id_spectacol, data_finala, url_final_reprezentatie))
                        db.commit()
                        
            print(f"✔️ Salvat: {titlu} (Vârstă: {varsta or '-'}, Durată: {durata_text or '-'})")

        except Exception as e:
            print(f"❌ Eroare la procesarea {link}: {e}")

if __name__ == "__main__":
    try:
        porneste_crawler()
    finally:
        cursor.close()
        db.close()
