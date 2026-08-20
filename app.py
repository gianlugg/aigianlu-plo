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

# Recupero sicuro della chiave (Secrets di Streamlit o variabile d'ambiente)
API_KEY = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = os.environ.get("GEMINI_API_KEY")

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
    
    if not API_KEY:
        st.markdown("#### 🔑 Chiave Gemini API")
        user_key = st.text_input("Inserisci API Key per test locale", type="password")
        if user_key:
            API_KEY = user_key
        st.markdown("[Ottieni API Key](https://aistudio.google.com/)")
    else:
        st.markdown("#### 🎯 Room Info")
        st.success("✅ Modalità Cloud attiva")

# --- HEADER PRINCIPALE & FOTO HOME ---
st.title("🃏 AIGIANLU analizza la tua mano!")
st.markdown("##### *Review tecnica e verdetto sulle giocate di Hero by Gianlu*")

trofei_path = find_file_fuzzy(["trofe", "troph", "coppe", "champion", "winner"])
if trofei_path:
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.image(trofei_path, width=280, caption="🏆 AIGIANLU - Hall of Fame")

st.write("---")

# --- SYSTEM PROMPT SNELLITO ---
SYSTEM_PROMPT = """
Tu sei AIGIANLU: un giocatore professionista ed esperto di exploit di Pot-Limit Omaha (PLO) sul field .it.
Stai analizzando e valutando la mano giocata da un ALTRO giocatore al tavolo ("Hero").

STILE E PROSPETTIVA:
- NON dire che la mano l'hai giocata tu. Hero è l'altro giocatore, tu sei il coach che commenta le sue scelte.
- Usa il tuo tono diretto, tecnico ed autorevole ("Hero qui regala chips", "La linea corretta qui è...").

REGOLE CALCOLO PUNTI PLO (OBBLIGO 2+3):
- Il punto si forma ESCLUSIVAMENTE con 2 carte della mano di Hero e 3 carte del board.
- Non inventare combinazioni inesistenti (es. vietato contare colori o full non validi secondo la regola 2+3).

I MIEI PRINCIPI STRATEGICI (METODO GIANLU):
1. Preflop: accettare aperture UTG con carte coordinate/double-suited; selezione rigorosa del suitedness.
2. Flop con scala già chiusa: in Position al Turn la puntata standard è 100% POT.
3. 3-Bet Pot OOP: dopo flop check-check, Delayed C-Bet al 60% pot con draw forti/blocker.
4. Multiway: evitare spew con mani marginali (colori bassi, tris deboli) su board coordinati o accoppiati.

Assegna uno SCORE complessivo da 1 a 10 alla condotta globale di Hero.

Rispondi RIGOROSAMENTE in formato JSON valido con questa struttura essenziale:
{
  "score": 4,
  "hero_hand": "carte di hero (es. As Ks Jh 9d)",
  "board": "board completo (es. Ts 8s 2c / 4d / Kd)",
  "pot_size_bb": 0.0,
  "giudizio_generale": "Sintesi chiara, tagliente e tecnica sulla condotta generale di Hero nello spot.",
  "consiglio_gianlu": "Cosa farei io esattamente al posto di Hero, quale linea scegliere e con quali size precise."
}
"""

def get_ai_analysis(client, content):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            content,
            "Analizza la mano rispettando le regole PLO 2+3, assegna il voto (score), fornisci il giudizio generale e la linea di Gianlu in formato JSON."
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
        st.error("Inserisci la chiave API nella barra laterale a sinistra per continuare.")
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

                st.markdown("---")
                st.subheader("⚖️ Giudizio Complessivo su Hero")
                st.info(data.get("giudizio_generale", ""))

                st.markdown("---")
                st.subheader("💡 Come l'avrebbe giocata AIGIANLU")
                st.success(data.get("consiglio_gianlu", ""))

            except Exception as e:
                loading_box.empty()
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    st.error("⏳ Quota temporaneamente esaurita o troppe richieste contemporanee. Riprova tra poco.")
                else:
                    st.error(f"Errore durante l'elaborazione: {e}")
