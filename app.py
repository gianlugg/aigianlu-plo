import json
import os
import random
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="AIGIANLU - PLO Review Room",
    page_icon="♠️",
    layout="centered"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Recupero automatico della chiave dai Secrets di Streamlit o variabili d'ambiente
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

def find_file_fuzzy(keywords):
    """Cerca un file nella cartella che contenga una delle parole chiave nel nome."""
    try:
        files = os.listdir(BASE_DIR)
        for f in files:
            for kw in keywords:
                if kw.lower() in f.lower() and not f.endswith(".py"):
                    return os.path.join(BASE_DIR, f)
    except Exception:
        pass
    return None

# Messaggi di attesa personalizzati
SPINNER_MESSAGES = [
    "AIGIANLU ti sta per educare... attendi...",
    "Un attimo che ti spiego come si gioca a PLO...",
    "Sto preparando la cattedra per la lezione...",
    "Vediamo che disastro ha combinato Hero stavolta...",
    "AIGIANLU sta caricando le bordate tecniche... un secondo..."
]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 👑 AIGIANLU COACH")
    profile_pic = find_file_fuzzy(["profilo", "avatar", "coach"])
    if profile_pic:
        st.image(profile_pic, use_container_width=True, caption="Gianlu in Cattedra")
    
    st.markdown("---")
    st.markdown("#### 🎯 Room Info")
    st.info("Benvenuto nella Review Room ufficiale di AIGIANLU. Carica lo spot per ricevere il verdetto tecnico immediato.")

# --- HEADER PRINCIPALE & FOTO HOME ---
st.title("🃏 AIGIANLU analizza la tua mano!")
st.markdown("##### *Review tecnica street-by-street sulle giocate di Hero by Gianlu*")

# Immagine trofei centrata e compatta
trofei_path = find_file_fuzzy(["trofe", "troph", "coppe", "champion", "winner"])
if trofei_path:
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.image(trofei_path, width=280, caption="🏆 AIGIANLU - Hall of Fame")

st.write("---")

# --- SYSTEM PROMPT BLINDATO & STRUTTURATO ---
SYSTEM_PROMPT = """
Tu sei AIGIANLU: un giocatore professionista ed esperto di exploit di Pot-Limit Omaha (PLO) sul field .it.
Stai analizzando e valutando la mano giocata da un ALTRO giocatore al tavolo ("Hero").

STILE E PROSPETTIVA:
- NON dire che la mano l'hai giocata tu. Hero è l'altro giocatore, tu sei il coach che commenta le sue scelte.
- Usa formule come: "Qui Hero sbaglia perché...", "Hero ha scelto una linea passiva...", "Io al posto di Hero invece farei...", "La mia size qui sarebbe...".

REGOLE CALCOLO PUNTI PLO (OBBLIGO 2+3):
- Il punto si forma ESCLUSIVAMENTE con 2 carte della mano di Hero e 3 carte del board.
- Non inventare Full House inesistenti: su board 6-Q-6-9-Q con una sola Q in mano ad Hero, Hero ha SOLO tris di Dame, MAI full.
- Distingui con precisione tra single-suited e double-suited preflop.

I MIEI PRINCIPI STRATEGICI (METODO GIANLU):
1. Preflop: accetto aperture da UTG anche con coppie medio-basse purché coordinate o double-suited.
2. Flop con scala già chiusa (es. JT7): In Position al Turn la puntata corretta è 100% POT.
3. 3-Bet Pot OOP: dopo flop check-check, al Turn la linea standard con NFD o blocker chiave è Delayed C-Bet al 60% pot.
4. Multiway: su board accoppiati o con colori chiusi a 4-5 giocatori, con mani marginali (colori senza Asso, semplici tris) si gioca check/fold contro aggressione.

Assegna uno SCORE complessivo da 1 a 10 alla condotta globale di Hero.
Suddividi l'analisi nelle street effettivamente giocate nella mano.

Rispondi RIGOROSAMENTE in formato JSON valido con questa struttura:
{
  "score": 4,
  "hero_hand": "carte di hero",
  "board": "board completo",
  "pot_size_bb": 0.0,
  "giudizio_generale": "Sintesi complessiva della giocata di Hero",
  "analisi_preflop": "Commento sulla scelta preflop di Hero",
  "analisi_flop": "Commento sulla scelta al flop di Hero (o null se fold preflop)",
  "analisi_turn": "Commento sulla scelta al turn di Hero (o null se mano finita prima)",
  "analisi_river": "Commento sulla scelta al river di Hero (o null se mano finita prima)",
  "consiglio_gianlu": "Cosa farei io esattamente al posto di Hero e con quale size specifica"
}
"""

def get_ai_analysis(client, content):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            content,
            "Analizza le decisioni di Hero street per street rispettando le regole del PLO 2+3, assegna il voto (score) e fornisci il responso in formato JSON."
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    return json.loads(response.text)

# --- TABS INPUT ---
tab1, tab2 = st.tabs(["📸 Carica Screenshot Tavolo", "📝 Incolla Testo Mano"])
content_to_analyze = None

with tab1:
    uploaded_file = st.file_uploader("Trascina qui lo screenshot", type=["png", "jpg", "jpeg", "webp"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Screenshot caricato", use_container_width=True)
        content_to_analyze = image

with tab2:
    text_hh = st.text_area("Incolla la Hand History", height=180, placeholder="Incolla qui il testo completo della mano...")
    if text_hh.strip():
        content_to_analyze = text_hh

# --- PULSANTE DI ANALISI ---
if st.button("🔥 AA-GIANLU analizzami lo spot", type="primary", use_container_width=True):
    if not API_KEY:
        st.error("Chiave API non configurata nei Secrets dell'applicazione (o variabile d'ambiente mancante).")
    elif not content_to_analyze:
        st.warning("Carica un'immagine o incolla il testo di una mano prima di procedere.")
    else:
        loading_box = st.empty()
        loading_img = find_file_fuzzy(["load", "attend", "caric"])
        if loading_img:
            loading_box.image(loading_img, caption="AIGIANLU sta preparando la bordata...", width=240)

        with st.spinner(random.choice(SPINNER_MESSAGES)):
            try:
                client = genai.Client(api_key=API_KEY)
                data = get_ai_analysis(client, content_to_analyze)
                
                loading_box.empty()
                st.success("Analisi completata!")

                score = int(data.get("score", 5))

                col_img, col_info = st.columns([1, 2])

                with col_img:
                    if score >= 7:
                        good_img = find_file_fuzzy(["good", "promoss", "ottim", "vittor"])
                        if good_img:
                            st.image(good_img, caption=f"Voto Gianlu: {score}/10 - PROMOSSA", use_container_width=True)
                        else:
                            st.metric("Voto Gianlu", f"{score}/10", "Promossa")
                    else:
                        bad_img = find_file_fuzzy(["bad", "bocciat", "error", "pers"])
                        if bad_img:
                            st.image(bad_img, caption=f"Voto Gianlu: {score}/10 - BOCCIATA", use_container_width=True)
                        else:
                            st.metric("Voto Gianlu", f"{score}/10", "Bocciata", delta_color="inverse")

                with col_info:
                    st.markdown("### 📋 Dati Rilevati")
                    st.write(f"**Hero ha:** `{data.get('hero_hand', '-')}`")
                    st.write(f"**Board:** `{data.get('board', '-')}`")
                    if data.get("pot_size_bb"):
                        st.write(f"**Piatto:** {data.get('pot_size_bb')} BB")
                    st.info(f"**Giudizio Complessivo:** {data.get('giudizio_generale', '')}")

                st.markdown("---")
                st.subheader("🔍 Analisi Street by Street sulle scelte di Hero")

                if data.get("analisi_preflop"):
                    with st.expander("📍 PREFLOP", expanded=True):
                        st.write(data.get("analisi_preflop"))

                if data.get("analisi_flop"):
                    with st.expander("📍 FLOP", expanded=True):
                        st.write(data.get("analisi_flop"))

                if data.get("analisi_turn"):
                    with st.expander("📍 TURN", expanded=True):
                        st.write(data.get("analisi_turn"))

                if data.get("analisi_river"):
                    with st.expander("📍 RIVER", expanded=True):
                        st.write(data.get("analisi_river"))

                st.markdown("---")
                st.markdown("### 💡 Come l'avrebbe giocata AIGIANLU")
                st.success(data.get("consiglio_gianlu", ""))

            except Exception as e:
                loading_box.empty()
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    st.error("⏳ Quota temporaneamente esaurita o troppe richieste contemporanee. Riprova tra poco.")
                else:
                    st.error(f"Errore durante l'elaborazione: {e}")
