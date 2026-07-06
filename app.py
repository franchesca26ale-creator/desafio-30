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
SEGUNDOS_ENTRE_SINCRONIZACIONES = 2  # cada cuánto se refresca la mesa en segundo plano

# Compatibilidad: st.fragment reemplazó a st.experimental_fragment en versiones
# recientes de Streamlit. Usamos el que exista para que la mesa se sincronice
# sola en segundo plano, sin recargar toda la página ni botones de "actualizar".
if hasattr(st, "fragment"):
    _fragment = st.fragment
elif hasattr(st, "experimental_fragment"):
    _fragment = st.experimental_fragment
else:
    st.error(
        "⚠️ Esta app necesita una versión más nueva de Streamlit para la "
        "sincronización automática en vivo. Actualízala con: pip install -U streamlit"
    )
    st.stop()

# =========================================================
# ESTILOS — CSS INYECTADO
# =========================================================
CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Manrope:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');

:root {
    --bg-deep: #0a0f0c;
    --panel-bg: #131b16;
    --panel-bg-soft: rgba(255,255,255,0.025);
    --panel-border: rgba(201, 162, 75, 0.20);
    --panel-border-soft: rgba(255,255,255,0.07);
    --gold: #c9a24b;
    --gold-bright: #f2d788;
    --gold-dim: #8a6f2c;
    --gold-glow: rgba(201, 162, 75, 0.38);
    --ivory: #f4efe2;
    --text-main: #eae4d6;
    --text-muted: #96907f;
    --ruby: #9c2b3e;
    --ruby-bright: #d1546a;
    --emerald: #1f7a53;
    --emerald-bright: #38b47f;
    --shadow-deep: rgba(0,0,0,0.55);
    --radius-lg: 20px;
    --radius-md: 14px;
}

/* =========================================================
   BASE — MESA DE CASINO (fieltro oscuro + viñeta + textura)
   ========================================================= */
html, body, .stApp {
    background-color: var(--bg-deep) !important;
    background-image:
        radial-gradient(ellipse 900px 500px at 50% -8%, rgba(31,122,83,0.16), transparent 60%),
        radial-gradient(circle at 12% 18%, rgba(201,162,75,0.06), transparent 42%),
        radial-gradient(circle at 88% 82%, rgba(156,43,62,0.07), transparent 42%),
        repeating-linear-gradient(45deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 1px, transparent 1px, transparent 28px),
        repeating-linear-gradient(-45deg, rgba(255,255,255,0.012) 0px, rgba(255,255,255,0.012) 1px, transparent 1px, transparent 28px) !important;
    font-family: 'Manrope', sans-serif;
    color: var(--text-main);
}

/* Ocultamos el chrome por defecto de Streamlit para una app autocontenida */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
div[data-testid="stToolbar"] { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }

.block-container { padding-top: 1.6rem !important; max-width: 1080px; }

.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    font-family: 'Playfair Display', serif; color: var(--ivory); letter-spacing: 0.5px;
}
.stApp .stCaption, .stApp small { color: var(--text-muted) !important; }
hr { border-color: var(--panel-border-soft) !important; }

/* Alertas de Streamlit re-vestidas al tono de la mesa */
div[data-testid="stAlert"] {
    background: var(--panel-bg) !important; border: 1px solid var(--panel-border) !important;
    border-radius: var(--radius-md) !important; color: var(--text-main) !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
}

/* =========================================================
   CINTA SUPERIOR DE MARCA
   ========================================================= */
.top-ribbon {
    display: flex; align-items: center; justify-content: space-between;
    max-width: 900px; margin: 0 auto 4px; padding: 12px 6px 14px;
    border-bottom: 1px solid var(--panel-border-soft);
}
.top-ribbon .brand-mark {
    font-family: 'Playfair Display', serif; font-size: 13px; letter-spacing: 4px;
    text-transform: uppercase; color: var(--text-muted); font-weight: 600;
}
.top-ribbon .brand-mark b { color: var(--gold); }
.live-badge {
    display: inline-flex; align-items: center; gap: 7px; font-size: 10.5px;
    letter-spacing: 2px; text-transform: uppercase; color: var(--emerald-bright); font-weight: 700;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--emerald-bright);
    box-shadow: 0 0 8px var(--emerald-bright); animation: live-pulse 1.7s ease-in-out infinite;
}
@keyframes live-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.35; transform: scale(1.35); }
}
.room-chip-badge {
    font-size: 11px; letter-spacing: 2px; color: var(--gold-bright); border: 1px solid var(--panel-border);
    background: rgba(201,162,75,0.07); padding: 4px 12px; border-radius: 20px; font-weight: 700;
}

/* 🎱 La ficha flotante (antes "bola de billar", ahora ficha de casino) */
.floating-ball-wrap {
    display: flex; justify-content: center; margin-top: 6px; margin-bottom: -15px;
}
.pool-ball {
    width: 78px; height: 78px; border-radius: 50%;
    background:
        radial-gradient(circle, transparent 57%, var(--gold) 59%, var(--gold) 63%, transparent 65%),
        radial-gradient(circle at 30% 26%, #24352b, #0a100c 80%);
    box-shadow: 0 20px 35px rgba(0,0,0,0.7), 0 0 45px var(--gold-glow);
    display: flex; align-items: center; justify-content: center;
    animation: float 4s ease-in-out infinite;
    border: 1px solid rgba(255,255,255,0.05);
}
.pool-ball-inner {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(150deg, #1c2b23, #0b1310);
    display: flex; align-items: center; justify-content: center;
    box-shadow: inset 0 -3px 6px rgba(0,0,0,0.5), inset 0 2px 3px rgba(255,255,255,0.06), 0 0 12px var(--gold-glow);
}
.pool-ball-text {
    font-family: 'Playfair Display', serif; font-weight: 800; font-size: 21px; color: var(--gold-bright);
    letter-spacing: -1px; text-shadow: 0 0 10px var(--gold-glow);
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); box-shadow: 0 30px 45px rgba(0,0,0,0.6), 0 0 65px var(--gold-glow); }
}

/* Títulos Elegantes */
.main-title {
    font-family: 'Playfair Display', serif; text-align: center; font-size: clamp(38px, 5.6vw, 60px);
    letter-spacing: 4px; color: var(--ivory); margin-top: 14px; margin-bottom: 5px; font-weight: 700;
}
.main-title span { color: var(--gold-bright); text-shadow: 0 0 20px var(--gold-glow); }
.sub-title {
    text-align: center; color: var(--text-muted); font-size: 14px; letter-spacing: 2px;
    font-weight: 500; margin-bottom: 15px; text-transform: uppercase;
}
.academic-badge {
    display: table; margin: 0 auto 40px; padding: 7px 26px; border: 1px solid var(--panel-border);
    border-radius: 30px; font-size: 10.5px; color: var(--gold); letter-spacing: 2.5px;
    background: rgba(201,162,75,0.05); text-transform: uppercase; font-weight: 700;
}

/* Paneles Interactivos (Efecto Hover Iluminado) */
.action-panel {
    position: relative; overflow: hidden;
    background: linear-gradient(165deg, rgba(255,255,255,0.03), rgba(255,255,255,0.005)), var(--panel-bg);
    border: 1px solid var(--panel-border-soft);
    border-radius: var(--radius-lg); padding: 32px; transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 15px 35px rgba(0,0,0,0.4); height: 100%;
}
.action-panel::before {
    content: '♠'; position: absolute; right: -16px; bottom: -34px; font-size: 130px;
    color: rgba(201,162,75,0.045); pointer-events: none; font-family: 'Playfair Display', serif;
}
.action-panel:hover {
    border-color: var(--gold); transform: translateY(-5px);
    box-shadow: 0 20px 45px rgba(0,0,0,0.6), 0 0 30px var(--gold-glow), inset 0 0 20px rgba(212,175,55,0.05);
}
.panel-header {
    font-family: 'Playfair Display', serif; font-size: 18px; color: var(--ivory); letter-spacing: 1px;
    margin-top: -10px !important; margin-bottom: 22px !important; position: relative; z-index: 1;
}

/* Reglas Visibles */
.rules-container {
    background: rgba(15, 20, 17, 0.65); border: 1px solid var(--panel-border-soft);
    border-radius: var(--radius-md); padding: 26px 28px; margin-top: 40px; border-left: 3px solid var(--gold);
}
.rules-title { font-family: 'Playfair Display', serif; color: var(--ivory); font-size: 19px; margin-bottom: 15px; letter-spacing: 0.5px; }
.rules-text { font-size: 14px; color: var(--text-muted); line-height: 1.75; }
.rules-text strong { color: var(--gold); font-weight: 700; }

/* Inputs y Botones */
div[data-testid="stTextInput"] label, div[data-testid="stNumberInput"] label {
    color: var(--text-muted) !important; font-size: 11.5px !important; letter-spacing: 1.8px !important; text-transform: uppercase;
}
.stTextInput input, .stNumberInput input {
    background-color: #0d120f !important; color: var(--ivory) !important;
    border: 1px solid var(--panel-border-soft) !important; border-radius: 8px !important;
    padding: 14px !important; transition: all 0.3s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--gold-bright) !important; box-shadow: 0 0 12px var(--gold-glow) !important;
}
.stButton button {
    background: linear-gradient(90deg, #8a6f2c 0%, var(--gold) 45%, var(--gold-bright) 100%) !important;
    color: #14100a !important; font-family: 'Playfair Display', serif !important; font-weight: 800 !important;
    letter-spacing: 2.2px !important; border: none !important; border-radius: 8px !important;
    padding: 22px 15px !important; transition: all 0.3s ease !important; width: 100%;
    box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 15px var(--gold-glow) !important; text-transform: uppercase;
}
.stButton button:hover {
    transform: scale(1.02) !important; box-shadow: 0 12px 25px rgba(0,0,0,0.6), 0 0 30px var(--gold-glow) !important;
    filter: brightness(1.08);
}
.stButton button:disabled {
    background: linear-gradient(90deg, #2a2a28, #3a3a36) !important; color: var(--text-muted) !important;
    box-shadow: none !important;
}

/* =====================================================
   SLOTS DE 3 JUGADORES OBLIGATORIOS (Anfitrión + 2)
   ===================================================== */
.slots-wrap {
    display: flex; gap: 18px; justify-content: center; flex-wrap: wrap; margin: 20px 0 10px;
}
.player-slot {
    width: 160px; padding: 18px 10px; border-radius: var(--radius-md); text-align: center;
    background: rgba(19,27,22,0.6); border: 1.5px dashed var(--panel-border-soft);
    transition: all 0.4s ease; position: relative;
}
.player-slot .slot-icon { font-size: 24px; display: block; margin-bottom: 6px; }
.player-slot .slot-name { font-weight: 700; font-size: 14px; color: var(--text-main); }
.player-slot .slot-role { font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--text-muted); margin-top: 3px; }
.slot-filled {
    border: 1.5px solid var(--gold); background: rgba(201,162,75,0.08);
    box-shadow: 0 0 20px var(--gold-glow), inset 0 0 15px rgba(201,162,75,0.06);
    animation: slot-pop 0.5s ease;
}
.slot-empty { opacity: 0.5; }
.slot-empty .slot-name { color: var(--text-muted); font-style: italic; font-weight: 500; }
.slot-host.slot-filled { border-color: var(--gold-bright); }
@keyframes slot-pop {
    0% { transform: scale(0.7); opacity: 0; }
    60% { transform: scale(1.08); }
    100% { transform: scale(1); opacity: 1; }
}
.progress-track {
    width: 280px; height: 8px; margin: 16px auto 4px; border-radius: 10px;
    background: rgba(255,255,255,0.06); overflow: hidden; border: 1px solid var(--panel-border-soft);
}
.progress-fill {
    height: 100%; border-radius: 10px; background: linear-gradient(90deg, var(--emerald), var(--gold-bright));
    transition: width 0.6s cubic-bezier(0.25,0.8,0.25,1); box-shadow: 0 0 12px var(--gold-glow);
}
.progress-caption { text-align: center; font-size: 12px; color: var(--text-muted); letter-spacing: 1.2px; margin-bottom: 10px; text-transform: uppercase; }

/* =====================================================
   TÓMBOLA DECORATIVA (bolitas flotando dentro del globo)
   ===================================================== */
.tombola-decor-wrap { display: flex; justify-content: center; margin: 6px 0 22px; }
.tombola-globe {
    width: 130px; height: 130px; border-radius: 50%; position: relative;
    background: radial-gradient(circle at 35% 25%, rgba(255,255,255,0.09), rgba(15,20,17,0.4) 65%);
    border: 2px solid var(--panel-border);
    box-shadow: inset 0 0 25px rgba(0,0,0,0.5), 0 0 30px var(--gold-glow);
    overflow: hidden;
}
.mini-ball {
    position: absolute; width: 20px; height: 20px; border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #fff6da, var(--gold) 75%);
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    animation: float-in-globe 3.4s ease-in-out infinite;
}
.mini-ball:nth-child(1) { left: 15px; top: 20px; animation-delay: 0s; background: radial-gradient(circle at 30% 30%, #fff, var(--ruby-bright) 75%); }
.mini-ball:nth-child(2) { left: 70px; top: 15px; animation-delay: 0.6s; background: radial-gradient(circle at 30% 30%, #fff, #3d8ee0 75%); }
.mini-ball:nth-child(3) { left: 40px; top: 55px; animation-delay: 1.1s; }
.mini-ball:nth-child(4) { left: 85px; top: 60px; animation-delay: 1.7s; background: radial-gradient(circle at 30% 30%, #fff, var(--emerald-bright) 75%); }
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

/* =====================================================
   TARJETA DE VIDRIO (sala de espera / turnos / plaquetas)
   ===================================================== */
.glass-card {
    background: linear-gradient(160deg, rgba(255,255,255,0.035), rgba(255,255,255,0.008)), var(--panel-bg);
    border: 1px solid var(--panel-border-soft);
    border-radius: var(--radius-lg); padding: 36px 34px;
    box-shadow: 0 20px 45px var(--shadow-deep), inset 0 1px 0 rgba(255,255,255,0.04);
    text-align: center; margin-bottom: 22px;
}
.plaque-eyebrow {
    display: inline-block; font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--gold); border: 1px solid var(--panel-border); padding: 5px 18px; border-radius: 20px;
    margin-bottom: 18px; background: rgba(201,162,75,0.06); font-weight: 700;
}
.room-code-display {
    font-family: 'Playfair Display', serif; font-size: 40px; letter-spacing: 12px;
    color: var(--ivory); font-weight: 700; margin: 6px 0 2px;
}
.bet-readout { font-size: 14.5px; color: var(--text-muted); margin-top: 12px; letter-spacing: 0.4px; }
.bet-readout strong { color: var(--gold-bright); }

/* Turno privado / traspaso de pantalla */
.handoff-card { padding-top: 12px; }
.handoff-icon { font-size: 42px; margin-bottom: 10px; filter: drop-shadow(0 0 12px var(--gold-glow)); }
.handoff-card h2 { font-family: 'Playfair Display', serif; color: var(--ivory); font-size: 25px; margin: 4px 0 10px; }
.handoff-card p { color: var(--text-muted); font-size: 14px; }
.handoff-warning { color: var(--ruby-bright) !important; font-weight: 700; letter-spacing: 0.3px; }

/* Fichas de cambios restantes */
.pips-wrap {
    text-align: center; font-size: 12.5px; color: var(--text-muted); letter-spacing: 1.2px;
    margin: 16px 0; text-transform: uppercase; font-weight: 600;
}
.pip-dot {
    display: inline-block; width: 11px; height: 11px; border-radius: 50%;
    border: 1.5px solid var(--gold-dim); margin: 0 4px; vertical-align: middle;
}
.pip-filled {
    background: radial-gradient(circle at 30% 30%, var(--gold-bright), var(--gold));
    border-color: var(--gold-bright); box-shadow: 0 0 8px var(--gold-glow);
}

/* Estado de la mesa (pastillas de turno) */
.mesa-estado { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin: 18px 0 28px; }
.status-pill {
    font-size: 12.5px; padding: 8px 17px; border-radius: 30px; letter-spacing: 0.4px;
    border: 1px solid transparent; font-weight: 700;
}
.pill-wait { background: rgba(255,255,255,0.03); color: var(--text-muted); border-color: var(--panel-border-soft); }
.pill-active {
    background: rgba(201,162,75,0.12); color: var(--gold-bright); border-color: var(--gold);
    animation: pill-glow 1.8s ease-in-out infinite;
}
@keyframes pill-glow {
    0%, 100% { box-shadow: 0 0 8px var(--gold-glow); }
    50% { box-shadow: 0 0 20px var(--gold-glow); }
}
.pill-done { background: rgba(31,122,83,0.15); color: var(--emerald-bright); border-color: var(--emerald); }

/* Resultados finales */
.results-banner {
    text-align: center; font-family: 'Playfair Display', serif; font-size: 25px; color: var(--gold-bright);
    background: linear-gradient(180deg, rgba(201,162,75,0.10), transparent);
    border: 1px solid var(--panel-border); border-radius: var(--radius-lg);
    padding: 20px; margin: 10px 0 30px; text-shadow: 0 0 18px var(--gold-glow); font-weight: 700;
}
.tie-banner { color: var(--ivory); }

.reveal-grid { display: flex; flex-wrap: wrap; gap: 18px; justify-content: center; margin-bottom: 20px; }
.reveal-card {
    width: 190px; padding: 24px 14px; border-radius: var(--radius-md); text-align: center;
    background: var(--panel-bg); border: 1px solid var(--panel-border-soft);
    animation: reveal-in 0.5s ease both; box-shadow: 0 12px 30px var(--shadow-deep);
}
@keyframes reveal-in {
    0% { opacity: 0; transform: translateY(16px) scale(0.95); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
.reveal-name { font-weight: 700; font-size: 15px; color: var(--ivory); margin-bottom: 4px; }
.reveal-number { font-family: 'Playfair Display', serif; font-size: 36px; color: var(--gold-bright); margin: 4px 0; }
.reveal-distance { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 12px; }
.reveal-badge { display: inline-block; font-size: 11px; padding: 5px 15px; border-radius: 20px; font-weight: 700; letter-spacing: 0.5px; }
.reveal-card.winner { border-color: var(--gold); box-shadow: 0 0 30px var(--gold-glow), 0 12px 30px var(--shadow-deep); }
.reveal-card.winner .reveal-badge { background: rgba(201,162,75,0.16); color: var(--gold-bright); border: 1px solid var(--gold); }
.reveal-card.tie .reveal-badge { background: rgba(255,255,255,0.06); color: var(--ivory); border: 1px solid var(--panel-border-soft); }
.reveal-card.lost { opacity: 0.62; }
.reveal-card.lost .reveal-badge { background: rgba(156,43,62,0.14); color: var(--ruby-bright); border: 1px solid var(--ruby); }

/* Ficha/tag de jugador genérico (roster) */
.roster-wrap { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin: 10px 0; }
.player-tag { font-size: 12.5px; padding: 6px 15px; border-radius: 20px; border: 1px solid var(--panel-border-soft); background: rgba(255,255,255,0.03); color: var(--text-main); }
.tag-host { border-color: var(--gold); color: var(--gold-bright); }
.empty-hint { color: var(--text-muted); font-style: italic; font-size: 13px; }

/* Ticker tipo pantalla LED de casino */
.ticker-bar {
    margin-top: 32px; overflow: hidden; border-top: 1px solid var(--panel-border-soft);
    border-bottom: 1px solid var(--panel-border-soft); background: rgba(0,0,0,0.28); padding: 11px 0;
}
.ticker-track {
    display: inline-flex; white-space: nowrap; animation: ticker-scroll 30s linear infinite;
    font-family: 'Space Mono', monospace; font-size: 12px; letter-spacing: 1px; color: var(--gold-bright);
}
.ticker-item { padding: 0 16px; }
.ticker-dot { color: var(--gold-dim); }
@keyframes ticker-scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

/* Confeti de victoria */
.confetti-wrap { position: relative; height: 0; }
.confetti-piece {
    position: fixed; top: -10px; width: 9px; height: 14px; opacity: 0.9; z-index: 9999;
    border-radius: 2px; animation: confetti-fall 3.2s ease-in forwards;
}
@keyframes confetti-fall {
    0% { transform: translateY(0) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
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
    st.session_state.phase = "playing"  # transición instantánea en tu pantalla; el resto sincroniza solo en segundos
    log_event(f"¡La ronda comienza! Apuesta fijada en 🪙 {st.session_state.bet_amount}.", icon="🎬")

def guardar_estado_jugador(nombre, datos_a_actualizar):
    ref = get_sala_ref().child(f'jugadores/{nombre}')
    ref.update(datos_a_actualizar)

def rerun_app():
    """Fuerza un rerun de TODA la app (no solo del fragmento en vivo).
    Se usa al salir de la sala, ya que esa decisión vive fuera del fragmento."""
    try:
        st.rerun(scope="app")
    except TypeError:
        st.rerun()


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
    
def render_top_ribbon():
    """Cinta superior de marca. Cuando hay una sala activa, muestra también
    el código de sala y un indicador 'EN VIVO' que reemplaza a los antiguos
    botones de 'Actualizar' — la mesa ahora se sincroniza sola en segundo plano."""
    en_sala = st.session_state.room_code is not None
    lado_derecho = (
        f"<span class='room-chip-badge'>MESA {st.session_state.room_code}</span>"
        "<span class='live-badge'><span class='live-dot'></span>En vivo</span>"
        if en_sala else
        "<span class='live-badge' style='color:var(--text-muted);'>Casino privado</span>"
    )
    st.markdown(
        f"""
        <div class='top-ribbon'>
            <div class='brand-mark'><b>TÓMBOLA</b> 30 · CASINO PRIVADO</div>
            <div style='display:flex; align-items:center; gap:14px;'>{lado_derecho}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
            chips += f"<span class='player-tag tag-player'>🃏 {nombre}</span>"
            
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
                <span class='slot-icon'>🃏</span>
                <div class='slot-name'>{invitados[i]}</div>
                <div class='slot-role'>Invitado {i + 1}</div>
            </div>"""
        else:
            slots_html += f"""
            <div class='player-slot slot-empty'>
                <span class='slot-icon'>🃏</span>
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

    if usuario["is_host"]:
        if st.button("🚀 Iniciar Ronda", use_container_width=True, disabled=not completa):
            iniciar_ronda()
            st.rerun()
    else:
        st.button("⏳ Esperando al Anfitrión...", use_container_width=True, disabled=True)

    if not completa:
        faltan = JUGADORES_REQUERIDOS - n_jugadores
        st.info(f"🙋 Faltan **{faltan}** jugador(es) para completar la mesa. La mesa se actualiza sola apenas se unan — no necesitas refrescar nada.")
            
    st.markdown("</div>", unsafe_allow_html=True)

def render_lobby_phase():
    """Pantalla de acceso (crear/unirse). Se muestra SIN auto-refresco para no
    interrumpir al usuario mientras escribe su nombre o el código de sala."""
    render_header("Conecta a todos tus amigos")
    render_login()
    render_ticker()


@_fragment(run_every=SEGUNDOS_ENTRE_SINCRONIZACIONES)
def render_mesa_en_vivo():
    """Fragmento autónomo: sincroniza la sala con Firebase cada pocos segundos
    y solo redibuja esta porción de la pantalla — sin recargar toda la página
    ni requerir botones de 'Actualizar'. Esto reemplaza el refresco manual."""
    fase = st.session_state.phase
    if fase == "lobby":
        render_header("Sala de espera")
        render_waiting_room()
        render_ticker()
    elif fase == "playing":
        render_playing_phase()
    elif fase == "results":
        render_results_phase()


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
                    st.session_state.turn_index = nuevo_idx
                    
                    if nuevo_idx >= len(orden):
                        ref_sala.update({'fase': 'results'})
                        st.session_state.phase = "results"
                        
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
        st.markdown(
            "<p style='text-align:center; color:var(--text-muted); font-size:12.5px; "
            "letter-spacing:0.5px;'>La mesa se actualiza sola — no necesitas hacer nada.</p>",
            unsafe_allow_html=True,
        )

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
        st.warning("Esperando resultados... la mesa se actualizará sola en unos segundos.")
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
    usuario = st.session_state.current_user
    if usuario["is_host"]:
        if st.button("🔁 Jugar Nueva Ronda", use_container_width=True):
            get_sala_ref().update({'fase': 'lobby'})
            st.session_state.phase = "lobby"
            st.rerun()
    else:
        if st.button("🚪 Salir de la sala", use_container_width=True):
            st.session_state.room_code = None
            st.session_state.current_user = None
            rerun_app()

    render_ticker()

# =========================================================
# PUNTO DE ENTRADA
# =========================================================
def main():
    init_state()
    inject_css()
    render_top_ribbon()

    if st.session_state.room_code is None:
        # Aún no hay sala: pantalla estática de acceso (sin auto-refresco).
        render_lobby_phase()
    else:
        # Ya está en una sala: la mesa se mantiene sincronizada sola.
        render_mesa_en_vivo()

if __name__ == "__main__":
    main()
