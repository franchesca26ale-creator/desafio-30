"""
🎰 EL DESAFÍO DEL 30 — Casino Privado
Un juego de mesa multijugador en la nube con salas por código.
construido con Streamlit + CSS inyectado + Firebase.
"""

import random
import string
from datetime import datetime
from typing import Any

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# =========================================================
# CONEXIÓN A FIREBASE PARA LA NUBE (GITHUB + STREAMLIT CLOUD)
# =========================================================
if not firebase_admin._apps:
    # 🌟 MAGIA DE SEGURIDAD: Leemos las credenciales desde los secretos de Streamlit
    # en lugar de buscar un archivo físico en tu computador.
    firebase_credentials = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_credentials)
    
    # ⚠️ ASEGÚRATE DE QUE ESTE SEA TU ENLACE REAL
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://bola30-64b83-default-rtdb.firebaseio.com/'
    })

# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="El Desafío del 30 · Casino Privado",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CONSTANTES DEL JUEGO
# =========================================================
NUMERO_OBJETIVO = 30
TOMBOLA_MIN, TOMBOLA_MAX = 1, 60
CAMBIOS_MAXIMOS = 2

# =========================================================
# ESTILOS — CSS INYECTADO
# =========================================================
CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700;800&family=Manrope:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');

:root {
    --bg-black: #06070b;
    --glass: rgba(16, 20, 28, 0.55);
    --glass-border: rgba(212, 175, 55, 0.22);
    --gold: #d4af37;
    --gold-bright: #f6e27a;
    --ruby: #e6394f;
    --emerald: #1fae7a;
    --ink: #f5f1e6;
    --muted: #9aa4b8;
}

html, body, .stApp {
    background:
        radial-gradient(1000px 600px at 12% 0%, rgba(212,175,55,0.07), transparent 60%),
        radial-gradient(1000px 700px at 88% 100%, rgba(31,174,122,0.10), transparent 60%),
        linear-gradient(180deg, #06070b 0%, #0a0d14 50%, #070907 100%);
    color: var(--ink);
    font-family: 'Manrope', sans-serif;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container {
    max-width: 980px;
    padding: clamp(14px,4vw,32px) clamp(12px,5vw,40px) 100px !important;
    margin: auto;
}
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb { background: rgba(212,175,55,0.35); border-radius: 8px; }
:focus-visible { outline: 2px solid var(--gold-bright); outline-offset: 2px; }

.hero-title {
    font-family: 'Cinzel', serif; font-weight: 800; font-size: clamp(26px, 5vw, 46px);
    text-align: center; letter-spacing: 2px;
    background: linear-gradient(90deg, var(--gold) 0%, var(--gold-bright) 25%, #fff8dc 50%, var(--gold-bright) 75%, var(--gold) 100%);
    background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
    color: transparent; animation: shimmerText 6s linear infinite; margin-bottom: 2px;
}
.hero-tagline { text-align: center; font-style: italic; color: var(--muted); font-size: 14px; letter-spacing: .5px; margin-bottom: 16px; }
.divider-gold { width: 120px; height: 2px; margin: 8px auto 24px; background: linear-gradient(90deg, transparent, var(--gold), transparent); }

.glass-card {
    background: var(--glass); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
    border: 1px solid var(--glass-border); border-radius: 18px; padding: 26px 28px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
    margin-bottom: 18px; animation: fadeUp .5s ease both;
}
.plaque-eyebrow { font-family: 'Cinzel'; font-weight: 700; letter-spacing: 1.5px; color: var(--gold-bright); font-size: 15px; text-transform: uppercase; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.plaque-eyebrow::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, var(--glass-border), transparent); }

.rules-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 16px; }
.rules-list li { display: flex; gap: 12px; align-items: flex-start; font-size: 14.5px; line-height: 1.55; }
.rule-emoji { font-size: 20px; filter: drop-shadow(0 0 6px rgba(212,175,55,.5)); }
.rules-list li strong { color: var(--gold-bright); }

.hero-ball-center { display: flex; justify-content: center; margin: 4px 0 28px; }
.ball-orbit-wrap { position: relative; width: min(calc(var(--ball-size) * 1.7), 82vw); height: min(calc(var(--ball-size) * 1.7), 82vw); display: flex; align-items: center; justify-content: center; }
.ball-ring { position: absolute; inset: 0; border-radius: 50%; border: 2px dashed rgba(212,175,55,.4); animation: spinRing 14s linear infinite; }
.ball-ring.ring-2 { inset: 12%; border-color: rgba(230,57,79,.35); border-style: dotted; animation: spinRing 9s linear infinite reverse; }
.ball-sphere { position: relative; z-index: 2; width: min(var(--ball-size), 58vw); height: min(var(--ball-size), 58vw); border-radius: 50%; background: radial-gradient(circle at 32% 28%, #fff6d0, var(--gold-bright) 30%, var(--gold) 60%, #6e4f10 100%); box-shadow: inset -14px -14px 30px rgba(0,0,0,.45), inset 10px 10px 24px rgba(255,255,255,.35), 0 0 50px rgba(212,175,55,.45); display: flex; flex-direction: column; align-items: center; justify-content: center; animation: floatY 4.6s ease-in-out infinite; }
.ball-sphere.pop-in { animation: popIn .55s cubic-bezier(.34,1.56,.64,1) both, floatY 4.6s ease-in-out infinite .55s; }
.ball-number { font-family: 'Orbitron'; font-weight: 800; font-size: calc(min(var(--ball-size), 58vw) * 0.34); color: #241a04; text-shadow: 0 1px 0 rgba(255,255,255,.35); }
.ball-caption { font-family: 'Manrope'; font-weight: 700; font-size: 11px; letter-spacing: 2.5px; text-transform: uppercase; color: #3a2c08; margin-top: 2px; }

.stButton > button { background: linear-gradient(135deg, var(--gold-bright), var(--gold) 55%, #a3781f); color: #1a1206 !important; font-family: 'Manrope'; font-weight: 800; letter-spacing: .3px; border: 1px solid rgba(255,255,255,.25); border-radius: 12px; padding: 10px 18px; box-shadow: 0 6px 18px rgba(212,175,55,.28); transition: transform .18s ease, box-shadow .18s ease, filter .18s ease; }
.stButton > button:hover:not(:disabled) { transform: translateY(-2px) scale(1.015); box-shadow: 0 10px 26px rgba(212,175,55,.42); filter: brightness(1.05); }
.stButton > button:active:not(:disabled) { transform: translateY(0) scale(.98); }
.stButton > button:disabled { opacity: .4; filter: grayscale(.4); box-shadow: none; }
.stTextInput input, .stNumberInput input { background: rgba(255,255,255,.05) !important; border: 1px solid var(--glass-border) !important; border-radius: 10px !important; color: var(--ink) !important; font-size: 18px !important;}
.stTextInput input:focus, .stNumberInput input:focus { border-color: var(--gold) !important; box-shadow: 0 0 0 3px rgba(212,175,55,.2) !important; }

.room-code-display { text-align: center; font-size: 28px; font-family: 'Orbitron'; font-weight: 800; color: var(--gold-bright); letter-spacing: 6px; margin: 10px 0 20px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 12px; border: 1px dashed var(--gold); }
.roster-wrap { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 4px; }
.player-tag { padding: 6px 14px; border-radius: 999px; font-size: 13px; font-weight: 700; border: 1px solid var(--glass-border); background: rgba(255,255,255,.04); }
.tag-host { color: var(--gold-bright); border-color: rgba(212,175,55,.5); }
.tag-player { color: #cfe9dd; border-color: rgba(31,174,122,.4); }

.mesa-estado { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 14px 0 22px; }
.status-pill { padding: 6px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 700; border: 1px solid var(--glass-border); }
.pill-done { color: #8ee7b8; border-color: rgba(31,174,122,.5); background: rgba(31,174,122,.08); }
.pill-active { color: var(--gold-bright); border-color: rgba(212,175,55,.6); background: rgba(212,175,55,.1); animation: pulseGlow 1.8s ease-in-out infinite; }
.pill-wait { color: var(--muted); }

.handoff-card { text-align: center; padding: 40px 24px; }
.handoff-icon { font-size: 44px; animation: floatY 2.6s ease-in-out infinite; margin-bottom: 6px; }

.pips-wrap { text-align: center; margin: 4px 0 14px; color: var(--muted); font-size: 13px; }
.pip-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-left: 6px; background: rgba(255,255,255,.15); border: 1px solid var(--glass-border); vertical-align: middle; }
.pip-filled { background: var(--gold); box-shadow: 0 0 8px rgba(212,175,55,.6); }

.ticker-bar { position: fixed; left: 0; right: 0; bottom: 0; height: 44px; background: rgba(5,6,10,.85); backdrop-filter: blur(10px); border-top: 1px solid var(--glass-border); overflow: hidden; z-index: 999; display: flex; align-items: center; }
.ticker-track { display: flex; white-space: nowrap; animation: tickerScroll 24s linear infinite; }
.ticker-item { font-family: 'Orbitron'; font-size: 12px; color: var(--gold-bright); padding: 0 18px; }
.ticker-dot { color: var(--ruby); }

.results-banner { text-align: center; font-family: 'Cinzel'; font-size: 20px; color: var(--gold-bright); padding: 16px; margin-bottom: 20px; border: 1px solid var(--glass-border); border-radius: 14px; background: rgba(212,175,55,.06); animation: pulseGlow 2.4s ease-in-out infinite; }
.tie-banner { color: #8ee7b8; background: rgba(31,174,122,.08); }
.reveal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 16px; margin-bottom: 22px; }
.reveal-card { position: relative; text-align: center; padding: 22px 12px; border-radius: 16px; border: 1px solid var(--glass-border); background: var(--glass); animation: cardReveal .6s ease both; overflow: hidden; }
.reveal-card.winner { border-color: var(--gold); box-shadow: 0 0 34px rgba(212,175,55,.5); animation: cardReveal .6s ease both, pulseGlow 2.2s ease-in-out infinite .6s; }
.reveal-card.tie { border-color: var(--emerald); box-shadow: 0 0 22px rgba(31,174,122,.35); }
.reveal-card.lost { opacity: .7; filter: saturate(.7); }
.reveal-name { font-weight: 800; margin-bottom: 6px; }
.reveal-number { font-family: 'Orbitron'; font-size: 34px; font-weight: 800; color: var(--gold-bright); }
.reveal-distance { font-size: 12px; color: var(--muted); margin: 6px 0; }
.reveal-badge { font-size: 12px; font-weight: 700; }
.confetti-wrap { position: relative; height: 0; }
.confetti-piece { position: absolute; top: -20px; width: 8px; height: 14px; animation: confettiFall 2.6s ease-in forwards; border-radius: 2px; }
.payout-card .payout-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed var(--glass-border); font-size: 14px; }
.payout-amount { font-family: 'Orbitron'; color: var(--gold-bright); }

@keyframes floatY { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }
@keyframes spinRing { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes popIn { 0% { transform: scale(.4); opacity: 0; } 70% { transform: scale(1.08); } 100% { transform: scale(1); opacity: 1; } }
@keyframes pulseGlow { 0%,100% { box-shadow: 0 0 14px rgba(212,175,55,.3); } 50% { box-shadow: 0 0 30px rgba(212,175,55,.6); } }
@keyframes shimmerText { 0% { background-position: 0% 50%; } 100% { background-position: 200% 50%; } }
@keyframes tickerScroll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
@keyframes fadeUp { 0% { opacity: 0; transform: translateY(16px); } 100% { opacity: 1; transform: translateY(0); } }
@keyframes cardReveal { 0% { transform: rotateY(90deg) scale(.85); opacity: 0; } 100% { transform: rotateY(0) scale(1); opacity: 1; } }
@keyframes confettiFall { 0% { transform: translateY(-40px) rotate(0deg); opacity: 1; } 100% { transform: translateY(340px) rotate(540deg); opacity: 0; } }
"""

def inject_css():
    st.markdown("<style>" + CSS_STYLES + "</style>", unsafe_allow_html=True)


# =========================================================
# ESTADO LOCAL Y SINCRONIZACIÓN FIREBASE
# =========================================================
def init_state():
    defaults = {
        "room_code": None,
        "current_user": None,  # {"name": "...", "is_host": True/False}
        "phase": "lobby",
        "players": {},
        "turn_order": [],
        "turn_index": 0,
        "tombola": [],
        "bet_amount": 100,
        "activity_log": [],
        "turn_revealed": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def get_sala_ref():
    if not st.session_state.room_code:
        return None
    return db.reference(f"salas/{st.session_state.room_code}")

def log_event(msg: str, icon: str = "🎰"):
    ts = datetime.now().strftime("%H:%M")
    st.session_state.activity_log.insert(0, f"{icon} {msg} · {ts}")
    st.session_state.activity_log = st.session_state.activity_log[:20]

def sincronizar_datos():
    ref = get_sala_ref()
    if not ref: return
    datos = ref.get()
    
    if datos:
        st.session_state.phase = datos.get('fase', 'lobby')
        st.session_state.bet_amount = datos.get('apuesta', 100)
        st.session_state.players = datos.get('jugadores', {})
        st.session_state.turn_order = datos.get('orden_turnos', [])
        st.session_state.turn_index = datos.get('turno_actual_index', 0)
        tombola_fb = datos.get('tombola', [])
        # Limpiamos la tómbola por si Firebase la mandó como diccionario o con nulos
        if isinstance(tombola_fb, dict):
            st.session_state.tombola = [v for v in tombola_fb.values() if v is not None]
        elif isinstance(tombola_fb, list):
            st.session_state.tombola = [b for b in tombola_fb if b is not None]
        else:
            st.session_state.tombola = []

def sacar_bolita() -> Any | None:
    ref = get_sala_ref().child('tombola')
    bolitas = ref.get()
    
    if isinstance(bolitas, dict):
        bolitas = [v for v in bolitas.values() if v is not None]
    elif isinstance(bolitas, list):
        bolitas = [b for b in bolitas if b is not None]
    else:
        bolitas = []
        
    if bolitas and len(bolitas) > 0:
        bola_sacada = bolitas.pop()
        ref.set(bolitas)
        return bola_sacada
    return None

def iniciar_ronda():
    # Solo el host ejecuta esto
    jugadores = list(st.session_state.players.keys())
    random.shuffle(jugadores)
    
    bolitas = list(range(TOMBOLA_MIN, TOMBOLA_MAX + 1))
    random.shuffle(bolitas)
    
    ref = get_sala_ref()
    
    # Reseteamos el estado de los jugadores para la nueva ronda
    for nombre in jugadores:
        ref.child(f'jugadores/{nombre}').update({
            'status': 'pendiente',
            'current_ball': None,
            'changes_left': CAMBIOS_MAXIMOS,
            'final_number': None
        })
        
    # Actualizamos la sala
    ref.update({
        'fase': 'playing',
        'orden_turnos': jugadores,
        'turno_actual_index': 0,
        'tombola': bolitas
    })
    
    st.session_state.turn_revealed = False
    log_event(f"¡La ronda comienza! Apuesta fijada en 🪙 {st.session_state.bet_amount}.", icon="🎬")

def guardar_estado_jugador(nombre, datos_a_actualizar):
    ref = get_sala_ref().child(f'jugadores/{nombre}')
    ref.update(datos_a_actualizar)


# =========================================================
# COMPONENTES VISUALES REUTILIZABLES
# =========================================================
def ball_widget(number=None, subtitle=None, size=190, animate=False):
    display = number if number is not None else NUMERO_OBJETIVO
    ghost_class = "ball-idle" if number is None else "ball-active"
    pop_class = "pop-in" if animate else ""
    caption = subtitle if subtitle else ("META" if number is None else "TU BOLITA")
    return f"""
    <div class='ball-orbit-wrap' style='--ball-size:{size}px;'>
        <div class='ball-ring'></div>
        <div class='ball-ring ring-2'></div>
        <div class='ball-sphere {ghost_class} {pop_class}'>
            <span class='ball-number'>{display}</span>
            <span class='ball-caption'>{caption}</span>
        </div>
    </div>
    """

def render_header(subtitle=None):
    st.markdown(
        f"""
        <div class='header-wrap'>
            <div class='hero-title'>🎰 EL DESAFÍO DEL 30</div>
            <div class='hero-tagline'>{subtitle or "El arte de acercarse a la perfección"}</div>
            <div class='divider-gold'></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_roster():
    chips = ""
    for nombre, datos in st.session_state.players.items():
        if datos.get("is_host"):
            chips += f"<span class='player-tag tag-host'>👑 {nombre} (Anfitrión)</span>"
        else:
            chips += f"<span class='player-tag tag-player'>🎮 {nombre}</span>"
            
    if not chips:
        chips = "<span class='empty-hint'>La mesa está vacía.</span>"
    st.markdown(f"<div class='roster-wrap'>{chips}</div>", unsafe_allow_html=True)

def render_ticker():
    log = st.session_state.activity_log[:10] or ["🎲 La mesa está lista. ¡Que comience la suerte! · --:--"]
    items = "".join(f"<span class='ticker-item'>{msg}</span><span class='ticker-dot'>◆</span>" for msg in log)
    st.markdown(f"<div class='ticker-bar'><div class='ticker-track'>{items}{items}</div></div>", unsafe_allow_html=True)

def render_confetti():
    colores = ["var(--gold)", "var(--gold-bright)", "var(--ruby)", "var(--emerald)"]
    piezas = ""
    for _ in range(28):
        izquierda = random.randint(0, 100)
        retraso = round(random.uniform(0, 1.2), 2)
        color = random.choice(colores)
        rotacion = random.randint(0, 360)
        piezas += f"<span class='confetti-piece' style='left:{izquierda}%; animation-delay:{retraso}s; background:{color}; transform:rotate({rotacion}deg);'></span>"
    st.markdown(f"<div class='confetti-wrap'>{piezas}</div>", unsafe_allow_html=True)


# =========================================================
# FASE 1 · LOGIN Y LOBBY DE SALAS
# =========================================================
def render_login():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='plaque-eyebrow'>🚪 Entrada al Casino</div>", unsafe_allow_html=True)
    
    opcion = st.radio("¿Qué deseas hacer?", ["🪄 Crear una nueva sala", "🔑 Unirse a una sala existente"])
    st.divider()
    
    nombre = st.text_input("Tu nombre en el juego", placeholder="Ej. Fran", max_chars=15)
    
    if opcion == "🪄 Crear una nueva sala":
        apuesta = st.number_input("Fijar apuesta inicial (fichas por jugador)", min_value=50, step=50, value=100)
        if st.button("Crear Sala y Entrar", use_container_width=True):
            if not nombre:
                st.error("Por favor ingresa tu nombre.")
                return
            
            # Generar código aleatorio
            codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            
            # Crear estructura en Firebase
            ref = db.reference(f'salas/{codigo}')
            ref.set({
                'fase': 'lobby',
                'apuesta': apuesta,
                'jugadores': {
                    nombre: {
                        'is_host': True,
                        'status': 'pendiente',
                        'current_ball': None,
                        'changes_left': CAMBIOS_MAXIMOS,
                        'final_number': None
                    }
                }
            })
            
            st.session_state.room_code = codigo
            st.session_state.current_user = {"name": nombre, "is_host": True}
            st.rerun()
            
    else:
        codigo_ingresado = st.text_input("Código de la sala", placeholder="Ej. A7X2").upper()
        if st.button("Verificar y Entrar", use_container_width=True):
            if not nombre or not codigo_ingresado:
                st.error("Faltan datos.")
                return
            
            ref = db.reference(f'salas/{codigo_ingresado}')
            sala_data = ref.get()
            
            if not sala_data:
                st.error("La sala no existe. Revisa el código.")
            elif nombre in sala_data.get('jugadores', {}):
                st.error("Ese nombre ya está en uso en esta sala.")
            elif sala_data.get('fase') != 'lobby':
                st.error("La partida en esta sala ya comenzó. No puedes entrar ahora.")
            else:
                # Agregar jugador a la sala existente
                ref.child(f'jugadores/{nombre}').set({
                    'is_host': False,
                    'status': 'pendiente',
                    'current_ball': None,
                    'changes_left': CAMBIOS_MAXIMOS,
                    'final_number': None
                })
                
                st.session_state.room_code = codigo_ingresado
                st.session_state.current_user = {"name": nombre, "is_host": False}
                st.rerun()
                
    st.markdown("</div>", unsafe_allow_html=True)

def render_waiting_room():
    sincronizar_datos()
    usuario = st.session_state.current_user
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='plaque-eyebrow'>📍 Sala de Espera</div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='room-code-display'>CÓDIGO: {st.session_state.room_code}</div>", unsafe_allow_html=True)
    st.caption("Comparte este código con tus amigos para que entren desde sus celulares.")
    
    st.markdown("### Jugadores conectados:")
    render_roster()
    
    st.markdown(f"<div class='bet-readout'>Apuesta fijada: <strong>🪙 {st.session_state.bet_amount}</strong> fichas</div>", unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Actualizar lista", use_container_width=True):
            sincronizar_datos()
            st.rerun()
            
    with col2:
        if usuario["is_host"]:
            n_jugadores = len(st.session_state.players)
            if st.button("🚀 Iniciar Ronda", use_container_width=True, disabled=n_jugadores < 2):
                iniciar_ronda()
                st.rerun()
        else:
            st.button("⏳ Esperando al Anfitrión...", use_container_width=True, disabled=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

def render_lobby_phase():
    render_header("Conecta a todos tus amigos")
    
    if st.session_state.room_code is None:
        render_login()
    else:
        render_waiting_room()
        
    render_ticker()


# =========================================================
# FASE 2 · JUEGO (turnos sincronizados en la nube)
# =========================================================
def render_estado_mesa(nombre_actual):
    html = "<div class='mesa-estado'>"
    for nombre in st.session_state.turn_order:
        jugador = st.session_state.players.get(nombre, {})
        status = jugador.get("status", "pendiente")
        
        if status == "plantado":
            icono, clase, texto = "✅", "pill-done", "Plantado"
        elif nombre == nombre_actual:
            icono, clase, texto = "🤫", "pill-active", "En su turno"
        else:
            icono, clase, texto = "⏳", "pill-wait", "Esperando"
        html += f"<span class='status-pill {clase}'>{icono} {nombre} · {texto}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_playing_phase():
    sincronizar_datos()
    render_header("Partida en curso")

    orden = st.session_state.turn_order
    idx = st.session_state.turn_index
    
    if idx >= len(orden):
        # Si ya jugaron todos, nos aseguramos de pasar a resultados
        st.session_state.phase = "results"
        st.rerun()
        return

    nombre_actual = orden[idx]
    jugador_actual = st.session_state.players.get(nombre_actual, {})
    mi_nombre = st.session_state.current_user["name"]

    render_estado_mesa(nombre_actual)

    if mi_nombre == nombre_actual:
        # ======= ES MI TURNO =======
        if not st.session_state.turn_revealed and jugador_actual.get("current_ball") is None:
            st.markdown(
                f"""
                <div class='glass-card handoff-card'>
                    <div class='handoff-icon'>🔐</div>
                    <h2>¡Es tu turno, {mi_nombre}!</h2>
                    <p class='handoff-warning'>Asegúrate de que nadie esté mirando tu pantalla.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🔓 Sacar mi primera bolita", use_container_width=True):
                bola = sacar_bolita()
                guardar_estado_jugador(mi_nombre, {
                    'current_ball': bola,
                    'status': 'jugando'
                })
                st.session_state.turn_revealed = True
                st.rerun()
        else:
            # Ya sacó la bolita, mostramos sus opciones
            bola_actual = jugador_actual.get("current_ball")
            st.markdown(f"<div class='hero-ball-center'>{ball_widget(bola_actual, subtitle='TU BOLITA', size=180, animate=True)}</div>", unsafe_allow_html=True)

            cambios_restantes = jugador_actual.get("changes_left", 0)
            pips = "".join("<span class='pip-dot pip-filled'></span>" if i < cambios_restantes else "<span class='pip-dot'></span>" for i in range(CAMBIOS_MAXIMOS))
            st.markdown(f"<div class='pips-wrap'>🔄 Cambios disponibles: {pips}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                puede_cambiar = cambios_restantes > 0 and len(st.session_state.tombola) > 0
                if st.button(f"🔄 Cambiar ({cambios_restantes} rest.)", use_container_width=True, disabled=not puede_cambiar):
                    nueva = sacar_bolita()
                    guardar_estado_jugador(mi_nombre, {
                        'current_ball': nueva,
                        'changes_left': cambios_restantes - 1
                    })
                    st.rerun()
            with c2:
                if st.button("✅ Plantarme", use_container_width=True):
                    # Guardamos el final y avanzamos el turno para toda la sala
                    guardar_estado_jugador(mi_nombre, {
                        'final_number': bola_actual,
                        'status': 'plantado'
                    })
                    
                    nuevo_idx = st.session_state.turn_index + 1
                    ref_sala = get_sala_ref()
                    ref_sala.update({'turno_actual_index': nuevo_idx})
                    
                    if nuevo_idx >= len(orden):
                        ref_sala.update({'fase': 'results'})
                        
                    st.session_state.turn_revealed = False
                    st.rerun()
            
    else:
        # ======= ES TURNO DE OTRO =======
        st.markdown(
            f"""
            <div class='glass-card handoff-card'>
                <div class='handoff-icon'>⏳</div>
                <h2>Turno de {nombre_actual}</h2>
                <p>Esperando a que saque su bolita y tome una decisión...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        if st.button("🔄 Sincronizar", use_container_width=True):
            st.rerun()

    render_ticker()


# =========================================================
# FASE 3 · RESULTADOS
# =========================================================
def calcular_resultados():
    jugadores = {n: p for n, p in st.session_state.players.items() if p.get("final_number") is not None}
    if not jugadores:
        return {}, []
        
    distancias = {n: abs(p["final_number"] - NUMERO_OBJETIVO) for n, p in jugadores.items()}
    distancia_minima = min(distancias.values())
    ganadores = [n for n, d in distancias.items() if d == distancia_minima]

    apuesta = st.session_state.bet_amount
    resultados = {}
    for nombre in jugadores:
        if len(ganadores) == 1 and nombre == ganadores[0]:
            estado, recibe, neto = "GANADOR", apuesta * 2, apuesta
        elif len(ganadores) > 1 and nombre in ganadores:
            estado, recibe, neto = "EMPATE", apuesta, 0
        else:
            estado, recibe, neto = "PERDIÓ", 0, -apuesta
            
        resultados[nombre] = {
            "estado": estado,
            "recibe": recibe,
            "neto": neto,
            "distancia": distancias[nombre],
            "numero": jugadores[nombre]["final_number"],
        }
    return resultados, ganadores


def render_results_phase():
    sincronizar_datos()
    render_header("🏆 Resultados Finales")
    
    resultados, ganadores = calcular_resultados()
    if not resultados:
        st.warning("Esperando resultados...")
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
        return

    if len(ganadores) == 1:
        st.markdown(f"<div class='results-banner'>🏆 ¡{ganadores[0]} se lleva la mesa! 🏆</div>", unsafe_allow_html=True)
        render_confetti()
    else:
        nombres_empate = " y ".join(ganadores)
        st.markdown(f"<div class='results-banner tie-banner'>🤝 ¡Empate entre {nombres_empate}! Recuperan apuesta.</div>", unsafe_allow_html=True)

    orden = sorted(resultados.items(), key=lambda kv: kv[1]["distancia"])
    badges = {"GANADOR": "🏆 Ganador", "EMPATE": "🤝 Empate", "PERDIÓ": "❌ Pierde"}
    clases = {"GANADOR": "winner", "EMPATE": "tie", "PERDIÓ": "lost"}

    html = "<div class='reveal-grid'>"
    for i, (nombre, r) in enumerate(orden):
        html += f"""
        <div class='reveal-card {clases[r['estado']]}' style='animation-delay:{i * 0.15}s'>
            <div class='reveal-name'>{nombre}</div>
            <div class='reveal-number'>{r['numero']}</div>
            <div class='reveal-distance'>Distancia a 30 → {r['distancia']}</div>
            <div class='reveal-badge'>{badges[r['estado']]}</div>
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Actualizar Pantalla", use_container_width=True):
            st.rerun()
    with c2:
        usuario = st.session_state.current_user
        if usuario["is_host"]:
            if st.button("🔁 Jugar Nueva Ronda", use_container_width=True):
                get_sala_ref().update({'fase': 'lobby'})
                st.rerun()
        else:
            if st.button("🚪 Salir de la sala", use_container_width=True):
                st.session_state.room_code = None
                st.session_state.current_user = None
                st.rerun()

    render_ticker()

# =========================================================
# PUNTO DE ENTRADA
# =========================================================
def main():
    init_state()
    inject_css()

    fase = st.session_state.phase
    if fase == "lobby":
        render_lobby_phase()
    elif fase == "playing":
        render_playing_phase()
    elif fase == "results":
        render_results_phase()

if __name__ == "__main__":
    main()