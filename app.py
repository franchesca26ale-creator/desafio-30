"""
🎰 EL DESAFÍO DEL 30 — Casino Privado
Un juego de mesa multijugador en la nube con salas por código.
construido con Streamlit + CSS inyectado + Firebase.
"""

import random
import string
import time
from datetime import datetime
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, db

# =========================================================
# CONEXIÓN A FIREBASE PARA LA NUBE (GITHUB + STREAMLIT CLOUD)
# =========================================================
if not firebase_admin._apps:
    firebase_credentials = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://bola30-64b83-default-rtdb.firebaseio.com'
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
JUGADORES_REQUERIDOS = 3

# =========================================================
# ESTILOS — CSS INYECTADO
# =========================================================
CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

:root {
    --bg-deep: #13111c;
    --panel-bg: #1a1825;
    --gold: #d4af37;
    --gold-bright: #ffd700;
    --gold-glow: rgba(212, 175, 55, 0.4);
    --text-main: #e2e2e2;
    --text-muted: #8b8994;
}

html, body, .stApp {
    background-color: var(--bg-deep) !important;
    background-image: radial-gradient(circle at 50% -10%, rgba(40,35,60,0.8), var(--bg-deep) 55%) !important;
    font-family: 'Manrope', sans-serif;
    color: var(--text-main);
}

/* 🎱 La Bola 30 Flotante */
.floating-ball-wrap {
    display: flex; justify-content: center; margin-top: 10px; margin-bottom: -15px;
}
.pool-ball {
    width: 75px; height: 75px; border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #5a5a6a, #0a0a0f 80%);
    box-shadow: 0 20px 35px rgba(0,0,0,0.7), 0 0 45px var(--gold-glow);
    display: flex; align-items: center; justify-content: center;
    animation: float 4s ease-in-out infinite;
    border: 1px solid rgba(255,255,255,0.05);
}
.pool-ball-inner {
    width: 38px; height: 38px; border-radius: 50%; background: #f0f0f0;
    display: flex; align-items: center; justify-content: center;
    box-shadow: inset 0 -3px 6px rgba(0,0,0,0.4), 0 0 10px rgba(255,255,255,0.5);
}
.pool-ball-text {
    font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 22px; color: #111;
    letter-spacing: -1px;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); box-shadow: 0 30px 45px rgba(0,0,0,0.6), 0 0 65px var(--gold-glow); }
}

/* Títulos Elegantes */
.main-title {
    font-family: 'Playfair Display', serif; text-align: center; font-size: clamp(40px, 6vw, 65px); 
    letter-spacing: 3px; color: white; margin-top: 15px; margin-bottom: 5px;
}
.main-title span { color: var(--gold-bright); text-shadow: 0 0 20px var(--gold-glow); }
.sub-title {
    text-align: center; color: var(--text-muted); font-size: 15px; letter-spacing: 1.5px; 
    font-weight: 500; margin-bottom: 15px;
}
.academic-badge {
    display: table; margin: 0 auto 40px; padding: 6px 24px; border: 1px solid var(--gold);
    border-radius: 30px; font-size: 11px; color: var(--gold); letter-spacing: 2px;
    background: rgba(212,175,55,0.05); text-transform: uppercase; font-weight: 600;
}

/* Paneles Interactivos (Efecto Hover Iluminado) */
.action-panel {
    background: var(--panel-bg); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px; padding: 30px; transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 15px 35px rgba(0,0,0,0.4); height: 100%;
}
.action-panel:hover {
    border-color: var(--gold); transform: translateY(-5px);
    box-shadow: 0 20px 45px rgba(0,0,0,0.6), 0 0 30px var(--gold-glow), inset 0 0 20px rgba(212,175,55,0.05);
}
.panel-header {
    margin-top: -10px !important; /* Esto "tira" el título hacia arriba para cerrar el hueco */
    margin-bottom: 20px !important;
}

/* Reglas Visibles */
.rules-container {
    background: rgba(20, 18, 28, 0.6); border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px; padding: 25px; margin-top: 40px; border-left: 4px solid var(--gold);
}
.rules-title { font-family: 'Playfair Display', serif; color: white; font-size: 20px; margin-bottom: 15px; }
.rules-text { font-size: 14.5px; color: var(--text-muted); line-height: 1.6; }
.rules-text strong { color: var(--gold); }

/* Inputs y Botones */
div[data-testid="stTextInput"] label, div[data-testid="stNumberInput"] label {
    color: var(--text-muted) !important; font-size: 12px !important; letter-spacing: 1.5px !important; text-transform: uppercase;
}
.stTextInput input, .stNumberInput input {
    background-color: #100e16 !important; color: white !important;
    border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important;
    padding: 14px !important; transition: all 0.3s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--gold-bright) !important; box-shadow: 0 0 12px var(--gold-glow) !important;
}
.stButton button {
    background: linear-gradient(90deg, #b08d29 0%, var(--gold-bright) 100%) !important;
    color: #111 !important; font-family: 'Playfair Display', serif !important; font-weight: 800 !important; 
    letter-spacing: 2px !important; border: none !important; border-radius: 8px !important; 
    padding: 24px 15px !important; transition: all 0.3s ease !important; width: 100%; 
    box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 15px var(--gold-glow) !important; text-transform: uppercase;
}
.stButton button:hover {
    transform: scale(1.02) !important; box-shadow: 0 12px 25px rgba(0,0,0,0.6), 0 0 30px var(--gold-glow) !important;
    filter: brightness(1.1);
}

/* =====================================================
   SLOTS DE 3 JUGADORES OBLIGATORIOS (Anfitrión + 2)
   ===================================================== */
.slots-wrap {
    display: flex; gap: 18px; justify-content: center; flex-wrap: wrap; margin: 20px 0 10px;
}
.player-slot {
    width: 160px; padding: 18px 10px; border-radius: 14px; text-align: center;
    background: rgba(20,18,28,0.55); border: 1.5px dashed rgba(255,255,255,0.15);
    transition: all 0.4s ease; position: relative;
}
.player-slot .slot-icon { font-size: 26px; display: block; margin-bottom: 6px; }
.player-slot .slot-name { font-weight: 700; font-size: 14px; color: var(--text-main); }
.player-slot .slot-role { font-size: 10.5px; letter-spacing: 1px; text-transform: uppercase; color: var(--text-muted); margin-top: 3px; }
.slot-filled {
    border: 1.5px solid var(--gold); background: rgba(212,175,55,0.08);
    box-shadow: 0 0 20px var(--gold-glow), inset 0 0 15px rgba(212,175,55,0.06);
    animation: slot-pop 0.5s ease;
}
.slot-empty { opacity: 0.55; }
.slot-empty .slot-name { color: var(--text-muted); font-style: italic; font-weight: 500; }
.slot-host.slot-filled { border-color: var(--gold-bright); }
@keyframes slot-pop {
    0% { transform: scale(0.7); opacity: 0; }
    60% { transform: scale(1.08); }
    100% { transform: scale(1); opacity: 1; }
}
.progress-track {
    width: 280px; height: 10px; margin: 14px auto 4px; border-radius: 10px;
    background: rgba(255,255,255,0.08); overflow: hidden; border: 1px solid rgba(255,255,255,0.08);
}
.progress-fill {
    height: 100%; border-radius: 10px; background: linear-gradient(90deg, #b08d29, var(--gold-bright));
    transition: width 0.6s cubic-bezier(0.25,0.8,0.25,1); box-shadow: 0 0 12px var(--gold-glow);
}
.progress-caption { text-align: center; font-size: 12.5px; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 10px; }

/* =====================================================
   TÓMBOLA DECORATIVA (bolitas flotando dentro del globo)
   ===================================================== */
.tombola-decor-wrap { display: flex; justify-content: center; margin: 6px 0 22px; }
.tombola-globe {
    width: 130px; height: 130px; border-radius: 50%; position: relative;
    background: radial-gradient(circle at 35% 25%, rgba(255,255,255,0.10), rgba(20,18,30,0.35) 65%);
    border: 2px solid rgba(212,175,55,0.35);
    box-shadow: inset 0 0 25px rgba(0,0,0,0.5), 0 0 30px var(--gold-glow);
    overflow: hidden;
}
.mini-ball {
    position: absolute; width: 20px; height: 20px; border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #fff6da, var(--gold) 75%);
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    animation: float-in-globe 3.4s ease-in-out infinite;
}
.mini-ball:nth-child(1) { left: 15px; top: 20px; animation-delay: 0s; background: radial-gradient(circle at 30% 30%, #fff, #d9455a 75%); }
.mini-ball:nth-child(2) { left: 70px; top: 15px; animation-delay: 0.6s; background: radial-gradient(circle at 30% 30%, #fff, #3d8ee0 75%); }
.mini-ball:nth-child(3) { left: 40px; top: 55px; animation-delay: 1.1s; }
.mini-ball:nth-child(4) { left: 85px; top: 60px; animation-delay: 1.7s; background: radial-gradient(circle at 30% 30%, #fff, #4bbf7a 75%); }
.mini-ball:nth-child(5) { left: 20px; top: 80px; animation-delay: 2.2s; background: radial-gradient(circle at 30% 30%, #fff, #b96bd6 75%); }
@keyframes float-in-globe {
    0%, 100% { transform: translate(0,0); }
    25% { transform: translate(10px, -14px); }
    50% { transform: translate(-6px, 8px); }
    75% { transform: translate(14px, 12px); }
}
.tombola-remaining-badge {
    text-align: center; font-size: 12px; letter-spacing: 1.5px; color: var(--gold);
    text-transform: uppercase; margin-top: 8px; font-weight: 700;
}
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
    if len(jugadores) != JUGADORES_REQUERIDOS:
        st.error(f"⚠️ Se necesitan exactamente {JUGADORES_REQUERIDOS} jugadores para iniciar.")
        return
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
        """
        <div class='floating-ball-wrap'>
            <div class='pool-ball'>
                <div class='pool-ball-inner'>
                    <span class='pool-ball-text'>30</span>
                </div>
            </div>
        </div>
        <div class='main-title'>TÓMBOLA <span>30</span></div>
        <div class='sub-title'>Juego de Probabilidad · Muestreo Sin Reemplazo</div>
        <div class='academic-badge'>Proyecto Final — Modelos de Probabilidad</div>
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

def render_slots_obligatorios():
    """Muestra siempre 3 puestos fijos: Anfitrión + 2 invitados."""
    jugadores = st.session_state.players
    nombres = list(jugadores.keys())
    host_nombre = next((n for n, d in jugadores.items() if d.get("is_host")), None)
    invitados = [n for n in nombres if n != host_nombre]

    slots_html = "<div class='slots-wrap'>"

    # Slot 1: Anfitrión (siempre primero)
    if host_nombre:
        slots_html += f"""
        <div class='player-slot slot-host slot-filled'>
            <span class='slot-icon'>👑</span>
            <div class='slot-name'>{host_nombre}</div>
            <div class='slot-role'>Anfitrión</div>
        </div>"""
    else:
        slots_html += """
        <div class='player-slot slot-empty'>
            <span class='slot-icon'>👑</span>
            <div class='slot-name'>Esperando...</div>
            <div class='slot-role'>Anfitrión</div>
        </div>"""

    # Slots 2 y 3: invitados
    for i in range(JUGADORES_REQUERIDOS - 1):
        if i < len(invitados):
            slots_html += f"""
            <div class='player-slot slot-filled'>
                <span class='slot-icon'>🎮</span>
                <div class='slot-name'>{invitados[i]}</div>
                <div class='slot-role'>Invitado {i + 1}</div>
            </div>"""
        else:
            slots_html += f"""
            <div class='player-slot slot-empty'>
                <span class='slot-icon'>🎮</span>
                <div class='slot-name'>Esperando...</div>
                <div class='slot-role'>Invitado {i + 1}</div>
            </div>"""

    slots_html += "</div>"
    st.markdown(slots_html, unsafe_allow_html=True)

    n_actual = len(nombres)
    porcentaje = min(100, int((n_actual / JUGADORES_REQUERIDOS) * 100))
    st.markdown(
        f"""
        <div class='progress-track'><div class='progress-fill' style='width:{porcentaje}%;'></div></div>
        <div class='progress-caption'>{n_actual} / {JUGADORES_REQUERIDOS} jugadores en la mesa</div>
        """,
        unsafe_allow_html=True,
    )

def render_tombola_decor(restantes=None):
    """Globo decorativo con bolitas flotando, siempre animado con CSS puro."""
    badge = f"<div class='tombola-remaining-badge'>🎱 {restantes} bolitas restantes en la tómbola</div>" if restantes is not None else ""
    st.markdown(
        f"""
        <div class='tombola-decor-wrap'>
            <div class='tombola-globe'>
                <div class='mini-ball'></div>
                <div class='mini-ball'></div>
                <div class='mini-ball'></div>
                <div class='mini-ball'></div>
                <div class='mini-ball'></div>
            </div>
        </div>
        {badge}
        """,
        unsafe_allow_html=True,
    )

def render_extraccion_animada(numero_final: int, contexto: str = "draw"):
    """
    Animación tipo 'tragamonedas': la bolita sale disparada de la tómbola,
    los números giran rápidamente y finalmente se detienen en el número real,
    con una explosión de chispas doradas al asentarse.
    """
    uid = f"reveal_{contexto}_{random.randint(0, 10_000_000)}"
    html_code = f"""
    <div id="{uid}" style="width:100%;">
      <style>
        html, body {{ background: transparent !important; margin:0; padding:0; overflow:hidden; }}
        .reveal-stage {{
            display:flex; flex-direction:column; align-items:center; justify-content:center;
            font-family: 'Manrope', sans-serif; position:relative; height:260px;
        }}
        .chute {{
            width:14px; height:34px; background:linear-gradient(180deg,#3a3550,#100e16);
            border-radius:6px 6px 0 0; margin-bottom:-6px; box-shadow:0 0 10px rgba(212,175,55,0.4);
        }}
        .rolling-ball {{
            width:150px; height:150px; border-radius:50%; position:relative;
            background: radial-gradient(circle at 32% 28%, #ffffff, #f4e4b8 35%, #d4af37 78%, #b08d29 100%);
            box-shadow: 0 10px 30px rgba(0,0,0,0.55), 0 0 0px rgba(255,215,0,0);
            display:flex; align-items:center; justify-content:center;
            animation: drop-in 0.55s cubic-bezier(.34,1.56,.64,1) both, spin-roll 0.55s linear both;
        }}
        .rolling-ball.settled {{
            animation: settle-pulse 0.9s ease both;
            box-shadow: 0 10px 30px rgba(0,0,0,0.55), 0 0 55px rgba(255,215,0,0.85);
        }}
        .rolling-ball .num {{
            font-weight:800; font-size:46px; color:#161219; letter-spacing:-1px;
            text-shadow: 0 1px 0 rgba(255,255,255,0.4);
        }}
        .rolling-ball .ring {{
            position:absolute; inset:-10px; border-radius:50%;
            border:2px solid rgba(212,175,55,0.0); transition: border-color .4s ease;
        }}
        .rolling-ball.settled .ring {{ border-color: rgba(255,215,0,0.55); }}
        @keyframes drop-in {{
            0% {{ transform: translateY(-90px) scale(0.4); opacity:0; }}
            60% {{ transform: translateY(10px) scale(1.05); opacity:1; }}
            100% {{ transform: translateY(0) scale(1); opacity:1; }}
        }}
        @keyframes spin-roll {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        @keyframes settle-pulse {{
            0% {{ transform: scale(1); }}
            30% {{ transform: scale(1.18); }}
            60% {{ transform: scale(0.94); }}
            100% {{ transform: scale(1); }}
        }}
        .caption {{
            margin-top:16px; font-size:12px; letter-spacing:2px; text-transform:uppercase;
            color:#8b8994; font-weight:600;
        }}
        .spark {{
            position:absolute; width:6px; height:6px; border-radius:50%;
            background: radial-gradient(circle, #fff6da, #ffd700);
            animation: spark-fly 0.75s ease-out forwards;
            pointer-events:none;
        }}
        @keyframes spark-fly {{
            0% {{ transform: translate(-50%,-50%) translate(0,0) scale(1); opacity:1; }}
            100% {{ transform: translate(-50%,-50%) translate(var(--dx), var(--dy)) scale(0); opacity:0; }}
        }}
      </style>
      <div class="reveal-stage" id="stage-{uid}">
        <div class="chute"></div>
        <div class="rolling-ball" id="ball-{uid}">
          <div class="ring"></div>
          <span class="num" id="num-{uid}">?</span>
        </div>
        <div class="caption" id="cap-{uid}">Girando la tómbola...</div>
      </div>
      <script>
        (function() {{
          const target = {numero_final};
          const minV = {TOMBOLA_MIN};
          const maxV = {TOMBOLA_MAX};
          const numberEl = document.getElementById("num-{uid}");
          const ballEl = document.getElementById("ball-{uid}");
          const stageEl = document.getElementById("stage-{uid}");
          const capEl = document.getElementById("cap-{uid}");
          let ticks = 0;
          const totalTicks = 16;

          function spawnSparks() {{
            for (let i = 0; i < 18; i++) {{
              const s = document.createElement("div");
              s.className = "spark";
              const angle = (Math.PI * 2 * i) / 18;
              const dist = 70 + Math.random() * 50;
              s.style.setProperty("--dx", Math.cos(angle) * dist + "px");
              s.style.setProperty("--dy", Math.sin(angle) * dist + "px");
              s.style.left = "50%";
              s.style.top = "112px";
              stageEl.appendChild(s);
              setTimeout(() => s.remove(), 800);
            }}
          }}

          const spin = setInterval(function () {{
            ticks++;
            const rnd = Math.floor(Math.random() * (maxV - minV + 1)) + minV;
            numberEl.textContent = rnd;
            if (ticks >= totalTicks) {{
              clearInterval(spin);
              numberEl.textContent = target;
              ballEl.classList.add("settled");
              capEl.textContent = "¡Bolita revelada!";
              spawnSparks();
            }}
          }}, 65);
        }})();
      </script>
    </div>
    """
    components.html(html_code, height=280, scrolling=False)

##CREAR SALA
def render_login():
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("<div class='action-panel'><div class='panel-header'>🏠 CREAR SALA</div>", unsafe_allow_html=True)
        nombre_host = st.text_input("TU NOMBRE", placeholder="Ej: Fran", key="host_name")
        apuesta = st.number_input("APUESTA OBLIGATORIA", min_value=1000, step=1000, value=2000)
        
        if st.button("CREAR SALA ➔", use_container_width=True, key="btn_crear_sala"):
            if not nombre_host:
                st.error("Ingresa tu nombre.")
            else:
                codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
                ref = db.reference(f'salas/{codigo}')
                ref.set({
                    'fase': 'lobby', 'apuesta': apuesta,
                    'jugadores': {nombre_host: {'is_host': True, 'status': 'pendiente', 'current_ball': None, 'changes_left': CAMBIOS_MAXIMOS, 'final_number': None}}
                })
                st.session_state.room_code = codigo
                st.session_state.current_user = {"name": nombre_host, "is_host": True}
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='action-panel'><div class='panel-header'>🚪 UNIRSE A SALA</div>", unsafe_allow_html=True)
        nombre_jugador = st.text_input("TU NOMBRE", placeholder="Ej: María", key="player_name")
        codigo_ingresado = st.text_input("CÓDIGO DE SALA (4 LETRAS)", placeholder="A B C D").upper()
        
        if st.button("UNIRSE ➔", use_container_width=True, key="btn_unirse_sala"):
            if not nombre_jugador or not codigo_ingresado:
                st.error("Faltan datos.")
            else:
                ref = db.reference(f'salas/{codigo_ingresado}')
                sala_data = ref.get()
                if not sala_data:
                    st.error("La sala no existe.")
                elif nombre_jugador in sala_data.get('jugadores', {}):
                    st.error("Ese nombre ya está en uso.")
                elif len(sala_data.get('jugadores', {})) >= JUGADORES_REQUERIDOS:
                    st.error(f"🚫 La mesa ya está completa ({JUGADORES_REQUERIDOS} jugadores). No puedes entrar a esta sala.")
                elif sala_data.get('fase', 'lobby') != 'lobby':
                    st.error("Esta partida ya comenzó, no puedes unirte ahora.")
                else:
                    ref.child(f'jugadores/{nombre_jugador}').set({
                        'is_host': False, 'status': 'pendiente', 'current_ball': None, 'changes_left': CAMBIOS_MAXIMOS, 'final_number': None
                    })
                    st.session_state.room_code = codigo_ingresado
                    st.session_state.current_user = {"name": nombre_jugador, 'is_host': False}
                    st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='rules-container'>
        <div class='rules-title'>📜 Reglamento Oficial de la Mesa</div>
        <div class='rules-text'>
            • <strong>La Mesa:</strong> Cada partida requiere exactamente 3 jugadores — el Anfitrión + 2 invitados. No se puede iniciar con menos, ni entrar si ya está completa.<br>
            • <strong>El Objetivo:</strong> Acércate lo más posible al número 30.<br>
            • <strong>La Tómbola:</strong> Bolitas del 1 al 60 (Muestreo sin reposición).<br>
            • <strong>Tu Turno:</strong> Juega en secreto. Saca una bolita y decide: ¿te plantas o pides otra?<br>
            • <strong>Los Cambios:</strong> Puedes cambiar de bolita máximo 2 veces, pero la anterior se descarta para siempre.<br>
            • <strong>Premios:</strong> El ganador duplica su apuesta inicial. ¡Si hay empate exacto, recuperas su dinero!
        </div>
    </div>
    """, unsafe_allow_html=True)
        
def render_waiting_room():
    sincronizar_datos()
    usuario = st.session_state.current_user
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='plaque-eyebrow'>📍 Sala de Espera</div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='room-code-display'>CÓDIGO: {st.session_state.room_code}</div>", unsafe_allow_html=True)
    st.caption("Comparte este código con tus 2 invitados para que entren desde sus celulares.")
    
    st.markdown("### Mesa de juego:")
    render_slots_obligatorios()
    
    st.markdown(f"<div class='bet-readout'>Apuesta fijada: <strong>🪙 {st.session_state.bet_amount}</strong> fichas</div>", unsafe_allow_html=True)
    
    st.divider()
    
    n_jugadores = len(st.session_state.players)
    completa = n_jugadores == JUGADORES_REQUERIDOS

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Actualizar lista", use_container_width=True):
            sincronizar_datos()
            st.rerun()
            
    with col2:
        if usuario["is_host"]:
            if st.button("🚀 Iniciar Ronda", use_container_width=True, disabled=not completa):
                iniciar_ronda()
                st.rerun()
        else:
            st.button("⏳ Esperando al Anfitrión...", use_container_width=True, disabled=True)

    if not completa:
        faltan = JUGADORES_REQUERIDOS - n_jugadores
        st.info(f"🙋 Faltan **{faltan}** jugador(es) para completar la mesa. Se necesitan exactamente {JUGADORES_REQUERIDOS}.")
            
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
    render_tombola_decor(restantes=len(st.session_state.tombola))

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
                with st.spinner("🎰 Girando la tómbola..."):
                    bola = sacar_bolita()
                    time.sleep(0.9)
                guardar_estado_jugador(mi_nombre, {
                    'current_ball': bola,
                    'status': 'jugando'
                })
                st.session_state.turn_revealed = True
                st.rerun()
        else:
            # Ya sacó la bolita: mostramos la animación de la bolita saliendo con el número real
            bola_actual = jugador_actual.get("current_ball")
            render_extraccion_animada(bola_actual, contexto=f"{mi_nombre}_{jugador_actual.get('changes_left', 0)}")

            cambios_restantes = jugador_actual.get("changes_left", 0)
            pips = "".join("<span class='pip-dot pip-filled'></span>" if i < cambios_restantes else "<span class='pip-dot'></span>" for i in range(CAMBIOS_MAXIMOS))
            st.markdown(f"<div class='pips-wrap'>🔄 Cambios disponibles: {pips}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                puede_cambiar = cambios_restantes > 0 and len(st.session_state.tombola) > 0
                if st.button(f"🔄 Cambiar ({cambios_restantes} rest.)", use_container_width=True, disabled=not puede_cambiar):
                    with st.spinner("🎰 Girando la tómbola..."):
                        nueva = sacar_bolita()
                        time.sleep(0.9)
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
