import streamlit as st
import mysql.connector
import json
import os

st.set_page_config(page_title="Repertoriu Teatru", layout="wide")

@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="abcd1234", 
        database="theater_crawler"
    )

conn = init_connection()

def fetch_data(query, params=None):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    return cursor.fetchall()

query_params = st.query_params
show_id = query_params.get("id")
page = query_params.get("page", "shows")

if page == "schedule":
    st.title("📅 Program Reprezentații")
    if st.button("← Înapoi la spectacole"):
        st.query_params.clear()
        st.rerun()

    st.divider()
    
    reprezentatii = fetch_data("""
        SELECT p.start_at, p.venue, s.title 
        FROM performances p 
        JOIN shows s ON p.show_id = s.id 
        ORDER BY p.start_at ASC
    """)
    
    if reprezentatii:
        for r in reprezentatii:
            r['Dată și Oră'] = r.pop('start_at').strftime("%d-%m-%Y %H:%M")
            r['Spectacol'] = r.pop('title')
            r['Sală / Locație'] = r.pop('venue')
            
        st.dataframe(reprezentatii, width="stretch", hide_index=True)
    else:
        st.info("Nu există reprezentații programate.")

elif show_id:
    if st.button("← Înapoi la listă"):
        st.query_params.clear()
        st.rerun()
        
    spectacol_data = fetch_data("SELECT * FROM shows WHERE id = %s", (show_id,))
    
    if spectacol_data:
        s = spectacol_data[0]
        st.title(s['title'])
        
        if s.get('source_url'):
            st.markdown(f"🔗 **Pagină oficială teatru:** [{s['source_url']}]({s['source_url']})")
            st.write("")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if s['poster_path'] and os.path.exists(s['poster_path']):
                st.image(s['poster_path'], width="stretch")
            else:
                st.info("Afiș indisponibil")
                
        with col2:
            if s.get('author'): st.write(f"**Autor:** {s['author']}")
            if s.get('director'): st.write(f"**Regizor:** {s['director']}")
            
            if s.get('duration_text'): 
                st.write(f"**Durată:** {s['duration_text']}")
            elif s.get('duration_minutes'): 
                st.write(f"**Durată:** {s['duration_minutes']} min")
                
            if s.get('age_recommendation'): st.write(f"**Recomandare de vârstă:** {s['age_recommendation']}")
            if s.get('genre'): st.write(f"**Gen:** {s['genre']}")
            if s.get('language'): st.write(f"**Limbă:** {s['language']}")
            
            st.markdown("### Descriere")
            st.write(s['description'] if s['description'] else "Nicio descriere disponibilă.")
        
        st.divider()
        
        col_cast, col_team = st.columns(2)
        
        with col_cast:
            st.subheader("🎭 Distribuție")
            cast = json.loads(s['cast_json']) if s['cast_json'] else []
            if cast:
                for actor in cast:
                    nume = actor.get('name', 'Necunoscut')
                    personaj = actor.get('character', '')
                    if personaj:
                        st.markdown(f"- **{nume}** (ca *{personaj}*)")
                    else:
                        st.markdown(f"- {nume}")
            else:
                st.write("Distribuție nepublicată.")
                
        with col_team:
            st.subheader("🎬 Echipă Artistică")
            team = json.loads(s['team_json']) if s['team_json'] else []
            if team:
                for membru in team:
                    rol = membru.get('role', 'Membru')
                    nume = membru.get('name', 'Necunoscut')
                    st.markdown(f"- **{rol}:** {nume}")
            else:
                st.write("Echipă nepublicată.")
                
        st.divider()
        
        st.subheader("🎟️ Reprezentații viitoare")
        viitoare = fetch_data("SELECT start_at, venue, source_url FROM performances WHERE show_id = %s AND start_at >= NOW() ORDER BY start_at ASC", (show_id,))
        if viitoare:
            for rep in viitoare:
                data_ora = rep['start_at'].strftime('%d %B %Y, %H:%M')
                locatie = rep['venue'] or 'Teatrul Mic'
                url_bilet = rep.get('source_url')
                
                if url_bilet and url_bilet.startswith("http"):
                    st.markdown(f"- 📅 **{data_ora}** | {locatie} ➡️ [🎟️ Cumpără Bilet / Detalii Eveniment]({url_bilet})")
                else:
                    st.markdown(f"- 📅 **{data_ora}** | {locatie}")
        else:
            st.write("Nu există reprezentații viitoare programate pentru acest spectacol.")
    else:
        st.error("Spectacolul nu a fost găsit în baza de date.")

else:
    st.title("🎭 Repertoriu Teatru")
    
    col_btn, col_search = st.columns([1, 2])
    with col_btn:
        if st.button("📅 Vezi Programul Complet"):
            st.query_params["page"] = "schedule"
            st.rerun()
            
    with col_search:
        search_query = st.text_input("🔍 Caută spectacol după titlu...", "").strip()
        
    st.divider()
    
    if search_query:
        spectacole = fetch_data("SELECT id, title, author, director, poster_path, duration_text FROM shows WHERE title LIKE %s", (f"%{search_query}%",))
    else:
        spectacole = fetch_data("SELECT id, title, author, director, poster_path, duration_text FROM shows")
    
    if not spectacole:
        st.warning("Nu a fost găsit niciun spectacol conform căutării.")
    else:
        cols_per_row = 3
        rows = [spectacole[i:i + cols_per_row] for i in range(0, len(spectacole), cols_per_row)]
        
        for row in rows:
            cols = st.columns(len(row))
            for idx, s in enumerate(row):
                with cols[idx]:
                    with st.container(border=True):
                        st.subheader(s['title'])
                        
                        if s['poster_path'] and os.path.exists(s['poster_path']):
                            st.image(s['poster_path'], width="stretch")
                        else:
                            st.info("Afiș indisponibil")
                            
                        if s.get('author'): st.caption(f"**Autor:** {s['author']}")
                        if s.get('director'): st.caption(f"**Regie:** {s['director']}")
                        if s.get('duration_text'): st.caption(f"⏱️ **Durată:** {s['duration_text']}")
                        
                        next_perf = fetch_data("SELECT start_at FROM performances WHERE show_id = %s AND start_at >= NOW() ORDER BY start_at ASC LIMIT 1", (s['id'],))
                        if next_perf:
                            st.success(f"🔜 {next_perf[0]['start_at'].strftime('%d-%m-%Y %H:%M')}")
                        else:
                            st.caption("🔜 Nicio reprezentație programată")
                            
                        if st.button("Vezi detalii", key=f"btn_{s['id']}", width="stretch"):
                            st.query_params["id"] = s['id']
                            st.rerun()