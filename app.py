"""
Tótem IoT Fisiológico | Universidad EAFIT
Monitoreo de frecuencia cardíaca y saturación con sensor MAX30102.
Asesoría analítica con Lardi 🐿️ (la ardilla del campus).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import openai

# ==============================================================================
# 1. CONFIGURACIÓN GENERAL Y ESTILO "SMOOTH GLOW"
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
    
    /* Fondo base */
    .stApp {
        background-color: #060912;
        color: #e2e8f0;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Ocultar barra lateral por completo */
    section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Espacio superior calibrado para evitar solapamiento con header de Streamlit */
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

    /* ORBES FLOTANTES DE FONDO (SUAVES Y ACELERADOS POR GPU) */
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

    /* Tarjetas de Métricas con sutil resplandor */
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

    /* Barra de Navegación Segmentada */
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

    /* OCULTAR EL CUADRO NARANJA DEL CHAT */
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
    
    /* Tarjeta informativa */
    .clean-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 3px solid #38bdf8;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
</style>

<!-- Orbes en GPU -->
<div class="ambient-orb orb-1"></div>
<div class="ambient-orb orb-2"></div>
<div class="ambient-orb orb-3"></div>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. CARGA Y PROCESAMIENTO LIMPIO (UTC -> BOGOTÁ)
# ==============================================================================
@st.cache_data
def load_and_preprocess_data():
    filename = "proyecto_integrador_eafit_max30102.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"❌ No se encontró `{filename}` en el directorio raíz.")
        return None

    # Zona horaria local (Colombia UTC-5)
    df["ts_utc"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ts_bogota"] = df["ts_utc"].dt.tz_convert("America/Bogota")
    
    df["fecha"] = df["ts_bogota"].dt.date
    df["hora"] = df["ts_bogota"].dt.hour
    df["hora_minuto"] = df["ts_bogota"].dt.strftime("%H:%M")
    
    dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    df["dia_semana"] = df["ts_bogota"].dt.dayofweek.map(dias_es)
    df["es_valido"] = df["measurement_status"].str.lower() == "valid"
    return df

df_raw = load_and_preprocess_data()
if df_raw is None:
    st.stop()


# Síntesis para el conocimiento de Lardi 🐿️
@st.cache_data
def get_lardi_knowledge(df: pd.DataFrame):
    validos = df[df["es_valido"]]
    invis = df[~df["es_valido"]]
    horas_dict = df.groupby("hora")["student_id"].count().to_dict()
    hora_pico = max(horas_dict, key=horas_dict.get) if horas_dict else 11
    dias_orden = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    dias_dict = df.groupby("dia_semana", observed=False)["student_id"].count().reindex(dias_orden).dropna().to_dict()

    return {
        "fechas_inicio_fin": f"{df['fecha'].min()} al {df['fecha'].max()}",
        "total_registros": len(df),
        "estudiantes_unicos": int(df["student_id"].nunique()),
        "mediciones_validas": len(validos),
        "mediciones_invalidas": len(invis),
        "porcentaje_invalidas": round((len(invis) / len(df)) * 100, 1),
        "bpm_promedio": round(validos["heart_rate_bpm"].mean(), 1),
        "spo2_promedio": round(validos["spo2_percent"].mean(), 1),
        "hora_mas_concurrida": f"{hora_pico}:00 hrs",
        "afluencia_dias": dias_dict,
        "estudiantes_con_mas_visitas": df["student_id"].value_counts().head(5).to_dict()
    }

lardi_context = get_lardi_knowledge(df_raw)


# ==============================================================================
# 3. ENCABEZADO Y FILTROS INTEGRADOS (SIN BARRA VACÍA)
# ==============================================================================
top_col1, top_col2 = st.columns([3.2, 1.8], gap="medium")

with top_col1:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px;">
        <h2 style="margin:0; font-size:1.55rem; font-weight:700; color:#ffffff;">Tótem Fisiológico EAFIT</h2>
        <span style="background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.3); padding:3px 10px; border-radius:9999px; font-size:0.72rem; font-weight:600; font-family:'JetBrains Mono';">MAX30102 ACTIVO</span>
    </div>
    <p style="margin:2px 0 10px 0; font-size:0.86rem; color:#94a3b8;">Monitoreo de frecuencia cardíaca y oxígeno en sangre en el campus universitario.</p>
    """, unsafe_allow_html=True)

with top_col2:
    api_key_input = st.text_input(
        "OpenAI API Key (para hablar con Lardi 🐿️):",
        type="password",
        placeholder="sk-...",
        help="Tu clave se usa solo durante esta sesión."
    )

# Barra horizontal de filtros (limpia y directa)
f_col1, f_col2, f_col3 = st.columns([1.5, 1.3, 1.2], gap="small")

with f_col1:
    min_d, max_d = df_raw["fecha"].min(), df_raw["fecha"].max()
    filtro_fechas = st.date_input("Fechas de estudio:", value=(min_d, max_d), min_value=min_d, max_value=max_d)

with f_col2:
    filtro_estado = st.radio("Filtro de validez:", ["Todas", "Solo válidas", "Solo con error"], index=0, horizontal=True)

with f_col3:
    lista_estudiantes = ["Todos los estudiantes"] + sorted(df_raw["student_id"].unique().tolist())
    filtro_estudiante = st.selectbox("Estudiante (ID):", lista_estudiantes, index=0)

# Aplicación de filtros
df_view = df_raw.copy()
if isinstance(filtro_fechas, (list, tuple)) and len(filtro_fechas) == 2:
    df_view = df_view[(df_view["fecha"] >= filtro_fechas[0]) & (df_view["fecha"] <= filtro_fechas[1])]

if filtro_estado == "Solo válidas":
    df_view = df_view[df_view["es_valido"]]
elif filtro_estado == "Solo con error":
    df_view = df_view[~df_view["es_valido"]]

if filtro_estudiante != "Todos los estudiantes":
    df_view = df_view[df_view["student_id"] == filtro_estudiante]

if df_view.empty:
    st.warning("No hay registros que coincidan con estos filtros.")
    st.stop()


# ==============================================================================
# 4. TARJETAS DE INDICADORES (KPIS)
# ==============================================================================
validos_view = df_view[df_view["es_valido"]]
invalidos_view = df_view[~df_view["es_valido"]]

n_total = len(df_view)
n_estudiantes = df_view["student_id"].nunique()
avg_bpm = round(validos_view["heart_rate_bpm"].mean(), 1) if not validos_view.empty else 0.0
avg_spo2 = round(validos_view["spo2_percent"].mean(), 1) if not validos_view.empty else 0.0
n_inval = len(invalidos_view)
pct_inval = round((n_inval / n_total) * 100, 1) if n_total > 0 else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Mediciones", f"{n_total:,}")
k2.metric("Estudiantes", f"{n_estudiantes}")
k3.metric("BPM Promedio", f"{avg_bpm} bpm", delta=f"{round(avg_bpm - 75.0, 1)} ref" if avg_bpm > 0 else None)
k4.metric("Oxígeno Promedio", f"{avg_spo2}%", delta=f"{round(avg_spo2 - 98.0, 1)}%" if avg_spo2 > 0 else None)
k5.metric("Lecturas con Error", f"{pct_inval}%", delta=f"{n_inval} fallas", delta_color="inverse")

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 5. WORKSPACE EQUILIBRADO: ANÁLISIS (62%) | LARDI 🐿️ (38%)
# ==============================================================================
col_workspace, col_lardi = st.columns([1.62, 1.0], gap="large")

# ------------------------------------------------------------------------------
# PANEL IZQUIERDO: VISUALIZACIONES & PERFILES
# ------------------------------------------------------------------------------
with col_workspace:
    vista_activa = st.radio(
        "Sección:",
        ["Biomarcadores", "Afluencia en Campus", "Historial Estudiante", "Hallazgos"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<div class='view-container'>", unsafe_allow_html=True)

    # --- 1. BIOMARCADORES ---
    if vista_activa == "Biomarcadores":
        g1, g2 = st.columns(2)
        with g1:
            if not validos_view.empty:
                fig_bpm = px.histogram(
                    validos_view, x="heart_rate_bpm", nbins=24,
                    color_discrete_sequence=["#38bdf8"],
                    title="<b>Frecuencia Cardíaca (BPM)</b>",
                    labels={"heart_rate_bpm": "Pulsaciones por minuto", "count": "Cantidad"}
                )
                fig_bpm.add_vrect(
                    x0=60, x1=100, fillcolor="#10b981", opacity=0.12, line_width=0,
                    annotation_text="Reposo normal (60-100)", annotation_position="top left",
                    annotation_font=dict(size=9, color="#10b981")
                )
                fig_bpm.update_layout(
                    template="plotly_dark", height=230, margin=dict(l=30, r=20, t=35, b=25),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
                    font=dict(family="Plus Jakarta Sans", size=10),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_bpm, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin registros válidos de BPM.")

        with g2:
            if not validos_view.empty:
                fig_spo2 = px.histogram(
                    validos_view, x="spo2_percent", nbins=20,
                    color_discrete_sequence=["#818cf8"],
                    title="<b>Oxígeno en Sangre (SpO₂ %)</b>",
                    labels={"spo2_percent": "Porcentaje SpO₂", "count": "Cantidad"}
                )
                fig_spo2.add_vline(
                    x=95, line_dash="dash", line_color="#f59e0b",
                    annotation_text="Alerta (<95%)", annotation_position="top left",
                    annotation_font=dict(size=9, color="#f59e0b")
                )
                fig_spo2.update_layout(
                    template="plotly_dark", height=230, margin=dict(l=30, r=20, t=35, b=25),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
                    font=dict(family="Plus Jakarta Sans", size=10),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_spo2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin registros válidos de SpO₂.")

        # Dispersión BPM vs SpO2 con escala ordenada
        fig_scatter = px.scatter(
            df_view, x="heart_rate_bpm", y="spo2_percent",
            color="signal_quality",
            color_continuous_scale="Tealgrn",
            hover_data=["student_id", "fecha", "hora_minuto"],
            title="<b>Relación entre BPM y SpO₂ (con calidad de lectura)</b>",
            labels={"heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ %", "signal_quality": "Calidad (0 a 1)"}
        )
        fig_scatter.update_traces(marker=dict(size=6, opacity=0.8))
        fig_scatter.update_layout(
            template="plotly_dark", height=250, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
            font=dict(family="Plus Jakarta Sans", size=10),
            coloraxis_colorbar=dict(thickness=10, len=0.7, title="Calidad"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

    # --- 2. AFLUENCIA EN CAMPUS ---
    elif vista_activa == "Afluencia en Campus":
        dias_orden = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        heat_df = df_view.pivot_table(
            index="dia_semana", columns="hora", values="student_id",
            aggfunc="count", fill_value=0, observed=False
        ).reindex(dias_orden).dropna(how="all")
        
        fig_heat = px.imshow(
            heat_df, color_continuous_scale="Blues",
            title="<b>Horas y Días con Mayor Uso del Tótem</b>",
            labels=dict(x="Hora del día", y="Día", color="Visitas")
        )
        fig_heat.update_layout(
            template="plotly_dark", height=250, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
            font=dict(family="Plus Jakarta Sans", size=10)
        )
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

        # Calidad de lectura
        fig_box = px.box(
            df_view, x="measurement_status", y="signal_quality",
            color="measurement_status",
            color_discrete_map={"valid": "#10b981", "invalid": "#f43f5e"},
            title="<b>Calidad de la Señal: Válidas vs. Con Error</b>",
            labels={"signal_quality": "Calidad (0 a 1)", "measurement_status": "Lectura"}
        )
        fig_box.update_layout(
            template="plotly_dark", height=230, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
            showlegend=False, font=dict(family="Plus Jakarta Sans", size=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar": False})

    # --- 3. HISTORIAL COMPLETO POR ESTUDIANTE ---
    elif vista_activa == "Historial Estudiante":
        # Desplegable de todos los estudiantes
        todos_los_estudiantes = sorted(df_raw["student_id"].unique().tolist())
        estudiante_seleccionado = st.selectbox(
            "Selecciona un estudiante para ver su historial completo:",
            todos_los_estudiantes,
            index=0 if filtro_estudiante == "Todos los estudiantes" else (
                todos_los_estudiantes.index(filtro_estudiante) if filtro_estudiante in todos_los_estudiantes else 0
            )
        )
        
        df_target = df_raw[df_raw["student_id"] == estudiante_seleccionado].sort_values("ts_bogota")
        
        t1, t2, t3 = st.columns(3)
        t1.metric("Visitas totales", f"{len(df_target)}")
        t2.metric("Primera visita", f"{df_target['fecha'].min()}")
        t3.metric("Última visita", f"{df_target['fecha'].max()}")
        
        # Gráfica interactiva con control deslizante de rango (Range Slider)
        fig_long = go.Figure()
        
        fig_long.add_trace(go.Scatter(
            x=df_target["ts_bogota"], y=df_target["heart_rate_bpm"],
            mode="lines+markers", name="BPM",
            line=dict(color="#38bdf8", width=2),
            marker=dict(size=6, color=np.where(df_target["es_valido"], "#38bdf8", "#f43f5e"))
        ))
        
        fig_long.add_trace(go.Scatter(
            x=df_target["ts_bogota"], y=df_target["spo2_percent"],
            mode="lines+markers", name="SpO₂ %", yaxis="y2",
            line=dict(color="#c084fc", width=2, dash="dot"),
            marker=dict(size=5, color=np.where(df_target["es_valido"], "#c084fc", "#f43f5e"))
        ))
        
        fig_long.update_layout(
            template="plotly_dark", height=300, margin=dict(l=35, r=35, t=30, b=35),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
            font=dict(family="Plus Jakarta Sans", size=10),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                rangeslider=dict(visible=True, thickness=0.08, bgcolor="rgba(15,23,42,0.8)")
            ),
            yaxis=dict(
                title=dict(text="BPM", font=dict(color="#38bdf8", size=10)),
                tickfont=dict(color="#38bdf8"),
                gridcolor="rgba(255,255,255,0.06)"
            ),
            yaxis2=dict(
                title=dict(text="SpO₂ %", font=dict(color="#c084fc", size=10)),
                tickfont=dict(color="#c084fc"),
                overlaying="y", side="right", range=[70, 102], showgrid=False
            ),
            legend=dict(orientation="h", y=1.15, x=0)
        )
        st.plotly_chart(fig_long, use_container_width=True, config={"displayModeBar": False})

    # --- 4. HALLAZGOS ---
    elif vista_activa == "Hallazgos":
        st.markdown(f"""
        <div class="clean-card">
            <h5 style="margin:0 0 4px 0; color:#38bdf8; font-size:0.9rem;">1. Rutina de Campus</h5>
            <p style="margin:0; font-size:0.85rem; color:#cbd5e1;">
                La mayor afluencia ocurre entre las <b>10:00 - 12:00</b> y las <b>14:00 - 16:00</b> (descansos entre clases). El mantenimiento del tótem conviene hacerlo antes de las 08:00.
            </p>
        </div>
        <div class="clean-card" style="border-left-color: #818cf8;">
            <h5 style="margin:0 0 4px 0; color:#818cf8; font-size:0.9rem;">2. Fallas en la Lectura</h5>
            <p style="margin:0; font-size:0.85rem; color:#cbd5e1;">
                El <b>{lardi_context['porcentaje_invalidas']}%</b> de mediciones con error se deben a que los estudiantes retiran el dedo antes de tiempo. Conviene añadir una guía táctil en el sensor.
            </p>
        </div>
        <div class="clean-card" style="border-left-color: #34d399;">
            <h5 style="margin:0 0 4px 0; color:#34d399; font-size:0.9rem;">3. Valores Habituales</h5>
            <p style="margin:0; font-size:0.85rem; color:#cbd5e1;">
                La mayoría de mediciones válidas rondan los <b>{lardi_context['bpm_promedio']} BPM</b> y <b>{lardi_context['spo2_promedio']}% de oxígeno</b>, valores normales para jóvenes en reposo en Medellín.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("ℹ️ Datos pedagógicos. El sensor MAX30102 no es un dispositivo médico certificado.")

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# PANEL DERECHO: LARDI 🐿️ (CONSEJERA INSTITUCIONAL EAFIT)
# ------------------------------------------------------------------------------
with col_lardi:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-weight:700; color:#f8fafc; font-size:0.95rem;">🐿️ Lardi · Consejera del Tótem</span>
        <span style="font-size:0.68rem; color:#38bdf8; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.25); padding:2px 8px; border-radius:9999px; font-family:'JetBrains Mono';">EN EL CAMPUS</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor con altura suave fija
    chat_box = st.container(height=450)
    
    if "lardi_messages" not in st.session_state:
        st.session_state.lardi_messages = [{
            "role": "assistant",
            "content": "¡Hola! Soy Lardi 🐿️, la ardilla del campus EAFIT. He estado atenta al tótem entre los árboles y conozco todas las 2.600 lecturas. ¿Qué te gustaría revisar hoy?"
        }]
    
    # Mostrar mensajes con prefijo limpio sin avatares cuadrados
    for msg in st.session_state.lardi_messages:
        with chat_box.chat_message(msg["role"]):
            prefix = "🐿️ **Lardi:** " if msg["role"] == "assistant" else "👤 **Investigador:** "
            st.markdown(f"{prefix}{msg['content']}")
            
    # Preguntas rápidas
    st.caption("Preguntas sugeridas:")
    p1, p2, p3 = st.columns(3)
    pregunta_rapida = None
    if p1.button("🐿️ ¿Picos?", use_container_width=True):
        pregunta_rapida = "¿En qué horarios hay más estudiantes usando el tótem y cuándo conviene hacer mantenimiento?"
    if p2.button("🍂 ¿Fallas?", use_container_width=True):
        pregunta_rapida = "¿Por qué fallan algunas mediciones del sensor y cómo podríamos mejorarlo?"
    if p3.button("🌰 ¿Atípicos?", use_container_width=True):
        pregunta_rapida = "¿Qué lecturas curiosas o atípicas has notado en los datos?"

    user_query = st.chat_input("Escribe tu pregunta a Lardi...") or pregunta_rapida

    if user_query:
        if not api_key_input:
            st.warning("Introduce tu OpenAI API Key arriba a la derecha para hablar con Lardi 🐿️.")
        else:
            st.session_state.lardi_messages.append({"role": "user", "content": user_query})
            with chat_box.chat_message("user"):
                st.markdown(f"👤 **Investigador:** {user_query}")
                
            with chat_box.chat_message("assistant"):
                with st.spinner("Lardi está pensando..."):
                    try:
                        client = openai.OpenAI(api_key=api_key_input)
                        
                        system_prompt = f"""
                        Eres Lardi 🐿️, la ardilla institucional y mascota no oficial del campus de la Universidad EAFIT en Medellín.
                        Eres inteligente, observadora, serena y muy amable. Conoces en detalle las 2.600 mediciones del tótem IoT porque sueles mirarlo desde las ramas de los árboles.
                        
                        Datos del tótem:
                        {json.dumps(lardi_context, ensure_ascii=False)}
                        
                        Filtro actual:
                        - Mediciones visibles: {len(df_view)}
                        - Estudiante: {filtro_estudiante}
                        
                        Tu personalidad y estilo de respuesta:
                        1. Tono cálido, cercano, lacónico y natural. Evita la jerga robótica o excesivamente pomposa.
                        2. Cita los datos de forma sencilla cuando sea útil (porcentajes, horas, cantidades).
                        3. Da sugerencias prácticas y de sentido común para los investigadores del campus.
                        4. Recuerda con amabilidad que estas mediciones son un ejercicio educativo y no un diagnóstico médico.
                        5. Usa algún toque sutil y tierno de ardilla (como nueces, ramas o el clima del campus) cuando encaje, sin exagerar.
                        """
                        
                        history = [{"role": "system", "content": system_prompt}] + [
                            {"role": m["role"], "content": m["content"]} for m in st.session_state.lardi_messages[-5:]
                        ]
                        
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=history,
                            temperature=0.4
                        )
                        reply = resp.choices[0].message.content
                        st.markdown(f"🐿️ **Lardi:** {reply}")
                        st.session_state.lardi_messages.append({"role": "assistant", "content": reply})
                    except Exception as err:
                        st.error(f"Error al conectar con OpenAI: {err}")
