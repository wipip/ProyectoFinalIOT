"""
Tótem IoT Fisiológico | Universidad EAFIT
Monitoreo de frecuencia cardíaca y saturación con sensor MAX30102.
Asesoría analítica integrada con Lardi 🐿️ vía st.secrets.
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import openai

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y SISTEMA VISUAL SMOOTH
# ==============================================================================
st.set_page_config(
    page_title="Tótem Fisiológico EAFIT // Lardi 🐿️",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    .stApp {
        background-color: #060912;
        color: #e2e8f0;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Ocultar barra lateral */
    section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Ajuste de espaciado superior */
    .block-container {
        padding-top: 3.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1420px !important;
        position: relative;
        z-index: 10;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ORBES FLOTANTES DE FONDO EN GPU */
    .ambient-orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(100px);
        pointer-events: none;
        z-index: 0;
        opacity: 0.18;
        animation: floatMotion 22s infinite alternate ease-in-out;
    }
    .orb-1 { width: 480px; height: 480px; background: #0284c7; top: -120px; left: -100px; }
    .orb-2 { width: 520px; height: 520px; background: #6366f1; bottom: -120px; right: 5%; animation-duration: 28s; }
    .orb-3 { width: 380px; height: 380px; background: #38bdf8; top: 35%; left: 30%; opacity: 0.12; animation-duration: 18s; }

    @keyframes floatMotion {
        0% { transform: translate3d(0, 0, 0) scale(1); }
        50% { transform: translate3d(40px, 30px, 0) scale(1.05); }
        100% { transform: translate3d(-30px, 50px, 0) scale(0.95); }
    }
    
    /* Transición suave para vistas */
    @keyframes viewFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .view-container {
        animation: viewFadeIn 0.3s ease-out;
    }

    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(20, 30, 55, 0.6) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 10px 16px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.45);
        box-shadow: 0 6px 20px rgba(56, 189, 248, 0.15);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }

    /* Navegación Segmentada */
    div[data-testid="stRadio"] > div {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 4px;
        gap: 6px;
        display: inline-flex;
    }
    div[data-testid="stRadio"] label {
        background: transparent !important;
        border: none !important;
        border-radius: 7px !important;
        padding: 6px 16px !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        transition: all 0.2s ease !important;
        margin: 0 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.25);
    }
    div[data-testid="stRadio"] label span {
        display: none !important;
    }

    /* Ocultar avatares cuadrados por defecto del chat */
    div[data-testid="stChatMessageAvatarAssistant"],
    div[data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }
    
    div[data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageContent"]) {
        gap: 0 !important;
    }
    
    .clean-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 3px solid #38bdf8;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
</style>

<div class="ambient-orb orb-1"></div>
<div class="ambient-orb orb-2"></div>
<div class="ambient-orb orb-3"></div>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. GESTIÓN INVISIBLE DE API KEY MEDIANTE ST.SECRETS
# ==============================================================================
def get_openai_api_key():
    # Intenta obtener de st.secrets primero, luego de variables de entorno
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    return os.getenv("OPENAI_API_KEY", None)

OPENAI_API_KEY = get_openai_api_key()


# ==============================================================================
# 3. CARGA Y PROCESAMIENTO (UTC -> BOGOTÁ)
# ==============================================================================
@st.cache_data
def load_and_preprocess_data():
    filename = "proyecto_integrador_eafit_max30102.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"❌ No se encontró `{filename}` en el directorio raíz.")
        return None

    df["ts_utc"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ts_bogota"] = df["ts_utc"].dt.tz_convert("America/Bogota")
    
    df["fecha"] = df["ts_bogota"].dt.date
    df["hora"] = df["ts_bogota"].dt.hour
    df["hora_minuto"] = df["ts_bogota"].dt.strftime("%H:%M")
    
    dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    df["dia_semana"] = df["ts_bogota"].dt.dayofweek.map(dias_es)
    df["es_valido"] = df["measurement_status"].str.lower() == "valid"
    return df

df_raw = load_and_preprocess_data
