# 🎭 Sistem Automatizat de Colectare a Datelor și Aplicație Web pentru Repertoriul Teatral


Proiect dezvoltat pentru disciplina **Tehnologii Web** (Universitatea POLITEHNICA din București, FETTI). 

Aplicația oferă o soluție completă (end-to-end) pentru achiziția automată a datelor despre spectacolele și reprezentațiile teatrale (de pe platforma Teatrului Mic), stocarea lor persistentă și structurată într-o bază de date relațională și afișarea printr-o interfață web dinamică și interactivă.

---

## 📌 Obiective principale

- **Automated Web Scraping & Crawling:** Extragere automată de date (titlu, sinopsis, autor, regizor, distribuție, echipă tehnică, afiș, calendar) cu toleranță la erori și evazivitate anti-bot (`headers spoofing`, `rate limiting`, verificare `robots.txt`).
- **Persistență și Idempotență (MySQL):** Structurare relațională cu suport nativ JSON (`utf8mb4_unicode_ci`) și prevenirea duplicatelor prin mecanismul de **Upsert** (`ON DUPLICATE KEY UPDATE`).
- **Interfață Web Modernă (Streamlit):** Arhitectură Single Page Application (SPA) cu simulare de rutare prin URL (`st.query_params`), căutare dinamică în timp real și optimizare prin caching de conexiuni (`@st.cache_resource`).

---

## 📐 Arhitectura Sistemului

```text
       ┌───────────────────────────┐
       │   Site Sursă (HTML/CSS)   │
       └─────────────┬─────────────┘
                     │  HTTPX (Header Spoofing & Rate Limit)
                     ▼
       ┌───────────────────────────┐
       │     Crawler / Scraper     │
       │ (BeautifulSoup4 + Regex)  │
       └─────────────┬─────────────┘
                     │  UPSERT (ON DUPLICATE KEY UPDATE)
                     ▼
       ┌───────────────────────────┐
       │    Bază de Date MySQL     │
       │    (shows + performances) │
       └─────────────┬─────────────┘
                     │  @st.cache_resource
                     ▼
       ┌───────────────────────────┐
       │   Streamlit Frontend SPA  │
       │  (Catalog, Detalii, Orar) │
       └───────────────────────────┘
```

---

## 🛠️ Tehnologii și Medii de Dezvoltare

- **Limbaj:** Python 3.11+
- **Backend & Scraping:** `httpx`, `beautifulsoup4`, `re` (Regex), `urllib.robotparser`, `hashlib`
- **Bază de date:** MySQL 8.0 (Connector Native Driver Python)
- **Frontend / UI:** Streamlit
- **Securitate & Storage:** Descărcare locală a afișelor bazată pe verificarea SHA-256 a imaginilor.

---

## 🗄️ Structura Bazei de Date

Schema cuprinde două tabele principale legate relațional cu constrângeri de integritate referențială:

- **`shows`**: reține producțiile teatrale, metadatele tehnice (durată, vârstă, autor, regizor) și structurile complexe stocate nativ în format JSON (`cast_json`, `team_json`).
- **`performances`**: modelează instanțele calendaristice ale spectacolelor (programul efectiv) și oferă legături directe către achiziția biletelor.

---

## 👥 Autori & Coordonare

- **Studenți:** Vasile Adina - Ioana, Rusu Ioana - Sorina (Grupa 443B)
- **Coordonator Științific:** Prof. Dr. Bogdan Florea
- **Instituție:** Universitatea POLITEHNICA din București — Facultatea de Electronică, Telecomunicații și Tehnologia Informației
