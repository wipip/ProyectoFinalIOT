"""
Proyecto Integrador Final: Dashboard IoT Tótem EAFIT
Computación Física e Internet de las Cosas - Universidad EAFIT
Arquitectura Zero-Sidebar: Control integrado, Copiloto permanente y visualizaciones limpias.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import openai

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y SISTEMA DE DISEÑO VISUAL
# ==============================================================================
st.set_page_config(
    page_title="Tótem Fisiológico IoT | EAFIT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyección de estilos de precisión
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Fondo principal y canvas */
    .stApp {
        background-color: #060911;
        color: #e2e8f0;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }
    
    /* Ocultar barra lateral permanentemente */
    section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* Barra Superior de Control (Control Deck) */
    .control-deck {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(10, 16, 30, 0.75) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    
    /* Tarjetas de Métricas (KPI Cards) */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(20, 30, 55, 0.5) 100%);
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 12px;
        padding: 10px 16px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
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
        font-feature-settings: "tnum";
    }

    /* Transformación de Radio a Segmented Pills Navigation */
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
        padding: 6px 14px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        transition: all 0.2s ease !important;
        margin: 0 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        font-size: 0.82rem !important;
    }
    div[data-testid="stRadio"] label span {
        display: none !important; /* Oculta el radio button circular nativo */
    }

    /* ELIMINACIÓN DE LOS AVATARES CUADRADOS NARANJAS EN CHAT */
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
    div[data-testid="stChatMessageContent"] {
        font-size: 0.85rem !important;
        line-height: 1.45 !important;
    }
    
    /* Tarjeta de Hallazgos */
    .finding-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 3px solid #38bdf8;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. CARGA Y PROCESAMIENTO ROBUSTO DE DATOS (ZONA HORARIA BOGOTÁ)
# ==============================================================================
@st.cache_data
def load_and_preprocess_data():
    filename = "proyecto_integrador_eafit_max30102.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"❌ No se encontró `{filename}` en el directorio raíz.")
        return None

    # Conversión temporal UTC -> Bogotá (UTC-5)
    df["ts_utc"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ts_bogota"] = df["ts_utc"].dt.tz_convert("America/Bogota")
    
    df["fecha"] = df["ts_bogota"].dt.date
    df["hora"] = df["ts_bogota"].dt.hour
    
    dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    df["dia_semana"] = df["ts_bogota"].dt.dayofweek.map(dias_es)
    df["es_valido"] = df["measurement_status"].str.lower() == "valid"
    return df

df_raw = load_and_preprocess_data()
if df_raw is None:
    st.stop()


# Síntesis estructurada para el contexto del Copiloto IA
@st.cache_data
def get_ai_knowledge_base(df: pd.DataFrame):
    validos = df[df["es_valido"]]
    invis = df[~df["es_valido"]]
    conteo_horas = df.groupby("hora")["student_id"].count().to_dict()
    hora_pico = max(conteo_horas, key=conteo_horas.get) if conteo_horas else 11
    dias_orden = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    conteo_dias = df.groupby("dia_semana", observed=False)["student_id"].count().reindex(dias_orden).dropna().to_dict()

    return {
        "fechas_operacion": f"{df['fecha'].min()} al {df['fecha'].max()}",
        "total_mediciones": len(df),
        "estudiantes_unicos": int(df["student_id"].nunique()),
        "mediciones_validas": len(validos),
        "mediciones_invalidas": len(invis),
        "tasa_invalidez_porcentaje": round((len(invis) / len(df)) * 100, 1),
        "fisiologia_valida": {
            "bpm_promedio": round(validos["heart_rate_bpm"].mean(), 1),
            "bpm_mediana": round(validos["heart_rate_bpm"].median(), 1),
            "bpm_rango_intercuartil": [round(validos["heart_rate_bpm"].quantile(0.25), 1), round(validos["heart_rate_bpm"].quantile(0.75), 1)],
            "spo2_promedio": round(validos["spo2_percent"].mean(), 1),
            "spo2_mediana": round(validos["spo2_percent"].median(), 1)
        },
        "calidad_optica_max30102": {
            "promedio_en_validas": round(validos["signal_quality"].mean(), 3),
            "promedio_en_invalidas": round(invis["signal_quality"].mean(), 3)
        },
        "afluencia_campus": {
            "hora_pico": f"{hora_pico}:00 hrs",
            "dias_distribucion": conteo_dias
        },
        "estudiantes_mas_frecuentes": df["student_id"].value_counts().head(5).to_dict()
    }

ai_context = get_ai_knowledge_base(df_raw)


# ==============================================================================
# 3. ENCABEZADO Y BARRA DE CONTROL INTEGRADA (CONTROL DECK)
# ==============================================================================
c_title, c_api = st.columns([3.2, 1.8])
with c_title:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
        <h2 style="margin:0; font-size:1.45rem; font-weight:700; color:#ffffff;">Tótem Fisiológico IoT // Campus EAFIT</h2>
        <span style="background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.3); padding:3px 10px; border-radius:9999px; font-size:0.72rem; font-weight:600; font-family:'JetBrains Mono';">MAX30102 ONLINE</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Procesamiento de pulsaciones ópticas y transpondedores NFC en tiempo real (UTC-5).")

with c_api:
    api_key_input = st.text_input(
        "OpenAI API Key:",
        type="password",
        placeholder="Introduce tu sk-... para habilitar IA",
        label_visibility="collapsed"
    )

# Barra de Herramientas de Filtrado Horizontal
with st.container():
    st.markdown('<div class="control-deck">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1.4, 1.4, 1.2])
    
    with f1:
        min_date, max_date = df_raw["fecha"].min(), df_raw["fecha"].max()
        filtro_fechas = st.date_input(
            "Rango de Fechas:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed"
        )
    
    with f2:
        filtro_estado = st.radio(
            "Estado de Medición:",
            ["Todas", "Válidas", "Inválidas"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )
        
    with f3:
        lista_estudiantes = ["Todos los Estudiantes"] + sorted(df_raw["student_id"].unique().tolist())
        filtro_estudiante = st.selectbox(
            "Filtrar Estudiante:",
            lista_estudiantes,
            index=0,
            label_visibility="collapsed"
        )
    st.markdown('</div>', unsafe_allow_html=True)

# Aplicación matemática de filtros
df_view = df_raw.copy()
if isinstance(filtro_fechas, (list, tuple)) and len(filtro_fechas) == 2:
    df_view = df_view[(df_view["fecha"] >= filtro_fechas[0]) & (df_view["fecha"] <= filtro_fechas[1])]

if filtro_estado == "Válidas":
    df_view = df_view[df_view["es_valido"]]
elif filtro_estado == "Inválidas":
    df_view = df_view[~df_view["es_valido"]]

if filtro_estudiante != "Todos los Estudiantes":
    df_view = df_view[df_view["student_id"] == filtro_estudiante]

if df_view.empty:
    st.warning("⚠️ No se hallaron registros con los filtros seleccionados.")
    st.stop()


# ==============================================================================
# 4. TARJETAS DE INDICADORES (5 KPIS REQUERIDOS)
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
k4.metric("SpO₂ Promedio", f"{avg_spo2}%", delta=f"{round(avg_spo2 - 98.0, 1)}%" if avg_spo2 > 0 else None)
k5.metric("Fallas de Señal", f"{pct_inval}%", delta=f"{n_inval} inv.", delta_color="inverse")

st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 5. WORKSPACE PRINCIPAL: ANALÍTICA (62%) | COPILOTO IA PERMANENTE (38%)
# ==============================================================================
col_workspace, col_copilot = st.columns([1.62, 1.0], gap="large")

# ------------------------------------------------------------------------------
# PANEL IZQUIERDO: VISUALIZACIONES & PERFILES
# ------------------------------------------------------------------------------
with col_workspace:
    # Segmented Pills para cambio de vista inmediato
    vista_activa = st.radio(
        "Sección de Análisis:",
        ["Exploración Biomédica", "Dinámica de Campus", "Historial Estudiante", "Hallazgos Clave"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    # --- VISTA 1: EXPLORACIÓN BIOMÉDICA ---
    if vista_activa == "Exploración Biomédica":
        g1, g2 = st.columns(2)
        with g1:
            if not validos_view.empty:
                fig_bpm = px.histogram(
                    validos_view, x="heart_rate_bpm", nbins=24,
                    color_discrete_sequence=["#38bdf8"],
                    title="<b>Frecuencia Cardíaca (BPM)</b>",
                    labels={"heart_rate_bpm": "BPM", "count": "Frecuencia"}
                )
                fig_bpm.add_vrect(
                    x0=60, x1=100, fillcolor="#10b981", opacity=0.12, line_width=0,
                    annotation_text="Reposo (60-100)", annotation_position="top left",
                    annotation_font=dict(size=9, color="#10b981")
                )
                fig_bpm.update_layout(
                    template="plotly_dark", height=230, margin=dict(l=30, r=20, t=35, b=25),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
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
                    title="<b>Saturación de Oxígeno (SpO₂)</b>",
                    labels={"spo2_percent": "SpO₂ %", "count": "Frecuencia"}
                )
                fig_spo2.add_vline(
                    x=95, line_dash="dash", line_color="#f59e0b",
                    annotation_text="Umbral (<95%)", annotation_position="top left",
                    annotation_font=dict(size=9, color="#f59e0b")
                )
                fig_spo2.update_layout(
                    template="plotly_dark", height=230, margin=dict(l=30, r=20, t=35, b=25),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
                    font=dict(family="Plus Jakarta Sans", size=10),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_spo2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin registros válidos de SpO₂.")

        # Dispersión BPM vs SpO2 con escala desacoplada para evitar solapamiento
        fig_scatter = px.scatter(
            df_view, x="heart_rate_bpm", y="spo2_percent",
            color="measurement_status",
            color_discrete_map={"valid": "#38bdf8", "invalid": "#f43f5e"},
            hover_data=["student_id", "fecha", "signal_quality"],
            title="<b>Correlación Fisiológica: BPM vs. SpO₂ (Válidos vs Inválidos)</b>",
            labels={"heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ %", "measurement_status": "Estado"}
        )
        fig_scatter.update_traces(marker=dict(size=6, opacity=0.8))
        fig_scatter.update_layout(
            template="plotly_dark", height=260, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            font=dict(family="Plus Jakarta Sans", size=10),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

    # --- VISTA 2: DINÁMICA DE CAMPUS Y CALIDAD IOT ---
    elif vista_activa == "Dinámica de Campus":
        dias_orden = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        heat_df = df_view.pivot_table(
            index="dia_semana", columns="hora", values="student_id",
            aggfunc="count", fill_value=0, observed=False
        ).reindex(dias_orden).dropna(how="all")
        
        fig_heat = px.imshow(
            heat_df, color_continuous_scale="Blues",
            title="<b>Mapa de Afluencia al Tótem (Hora vs Día de la Semana)</b>",
            labels=dict(x="Hora del Día (0-23)", y="Día", color="Usos")
        )
        fig_heat.update_layout(
            template="plotly_dark", height=250, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            font=dict(family="Plus Jakarta Sans", size=10)
        )
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

        # Comparativa de Calidad de Señal
        fig_box = px.box(
            df_view, x="measurement_status", y="signal_quality",
            color="measurement_status",
            color_discrete_map={"valid": "#10b981", "invalid": "#f43f5e"},
            title="<b>Índice de Calidad Óptica MAX30102 según Validez</b>",
            labels={"signal_quality": "Calidad (0.0 a 1.0)", "measurement_status": "Estado"}
        )
        fig_box.update_layout(
            template="plotly_dark", height=230, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            showlegend=False, font=dict(family="Plus Jakarta Sans", size=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar": False})

    # --- VISTA 3: HISTORIAL POR ESTUDIANTE (SIN BUGS DE PLOTLY) ---
    elif vista_activa == "Historial Estudiante":
        est_target = filtro_estudiante if filtro_estudiante != "Todos los Estudiantes" else df_raw["student_id"].iloc[0]
        df_target = df_raw[df_raw["student_id"] == est_target].sort_values("ts_bogota")
        
        st.markdown(f"<span style='color:#38bdf8; font-weight:600;'>Historial Clínico-Experimental:</span> <code>{est_target}</code>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.columns(3)
        t1.metric("Visitas Registradas", f"{len(df_target)}")
        t2.metric("Primera Medición", f"{df_target['fecha'].min()}")
        t3.metric("Última Medición", f"{df_target['fecha'].max()}")
        
        fig_long = go.Figure()
        
        # Traza BPM (Y1)
        fig_long.add_trace(go.Scatter(
            x=df_target["ts_bogota"], y=df_target["heart_rate_bpm"],
            mode="lines+markers", name="BPM",
            line=dict(color="#38bdf8", width=2),
            marker=dict(size=6, color=np.where(df_target["es_valido"], "#38bdf8", "#f43f5e"))
        ))
        
        # Traza SpO2 (Y2)
        fig_long.add_trace(go.Scatter(
            x=df_target["ts_bogota"], y=df_target["spo2_percent"],
            mode="lines+markers", name="SpO₂ %", yaxis="y2",
            line=dict(color="#c084fc", width=2, dash="dot"),
            marker=dict(size=5, color=np.where(df_target["es_valido"], "#c084fc", "#f43f5e"))
        ))
        
        fig_long.update_layout(
            template="plotly_dark", height=280, margin=dict(l=35, r=35, t=30, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            font=dict(family="Plus Jakarta Sans", size=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
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
            legend=dict(orientation="h", y=1.12, x=0)
        )
        st.plotly_chart(fig_long, use_container_width=True, config={"displayModeBar": False})

    # --- VISTA 4: HALLAZGOS Y DECISIONES CLAVE ---
    elif vista_activa == "Hallazgos Clave":
        st.markdown(f"""
        <div class="finding-box">
            <h5 style="margin:0 0 4px 0; color:#38bdf8; font-size:0.9rem;">1. Rutina de Campus y Horas Pico</h5>
            <p style="margin:0; font-size:0.84rem; color:#cbd5e1;">
                El uso máximo ocurre de <b>10:00 a 12:00</b> y de <b>14:00 a 16:00</b>. Los mantenimientos deben realizarse antes de las 08:00 para asegurar disponibilidad.
            </p>
        </div>
        <div class="finding-box" style="border-left-color: #818cf8;">
            <h5 style="margin:0 0 4px 0; color:#818cf8; font-size:0.9rem;">2. Ruido Óptico en Mediciones Inválidas</h5>
            <p style="margin:0; font-size:0.84rem; color:#cbd5e1;">
                El <b>{ai_context['tasa_invalidez_porcentaje']}%</b> de registros fallidos presenta calidad de señal media de <b>{ai_context['calidad_optica_max30102']['promedio_en_invalidas']}</b> vs <b>{ai_context['calidad_optica_max30102']['promedio_en_validas']}</b> en válidos, sugiriendo retiro prematuro del dedo.
            </p>
        </div>
        <div class="finding-box" style="border-left-color: #34d399;">
            <h5 style="margin:0 0 4px 0; color:#34d399; font-size:0.9rem;">3. Consistencia Biomédica Poblacional</h5>
            <p style="margin:0; font-size:0.84rem; color:#cbd5e1;">
                El rango intercuartil se ubica entre <b>{ai_context['fisiologia_valida']['bpm_rango_intercuartil'][0]} y {ai_context['fisiologia_valida']['bpm_rango_intercuartil'][1]} BPM</b>, reflejando patrones de reposo esperados en estudiantes.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("⚠️ Nota: Dataset sintético con fines formativos. El MAX30102 no es un dispositivo médico certificado.")


# ------------------------------------------------------------------------------
# PANEL DERECHO: COPILOTO IA PERMANENTE (SIN AVATARES NARANJAS)
# ------------------------------------------------------------------------------
with col_copilot:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-weight:700; color:#f8fafc; font-size:0.9rem;">🤖 Copiloto IA EAFIT</span>
        <span style="font-size:0.68rem; color:#38bdf8; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.25); padding:2px 8px; border-radius:9999px; font-family:'JetBrains Mono';">GPT-4o-mini</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor con altura fija para evitar desajustes visuales
    chat_stream = st.container(height=450)
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{
            "role": "assistant",
            "content": "Conozco las 2.600 lecturas del tótem, patrones de campus y fallas de señal. ¿En qué análisis o decisión institucional te puedo apoyar?"
        }]
    
    # Renderizado limpio sin avatares naranjas
    for msg in st.session_state.chat_messages:
        with chat_stream.chat_message(msg["role"]):
            prefix = "🤖 **Copiloto:** " if msg["role"] == "assistant" else "👤 **Analista:** "
            st.markdown(f"{prefix}{msg['content']}")
            
    # Chips de consulta rápida de un clic
    st.caption("Consultas rápidas:")
    c1, c2, c3 = st.columns(3)
    prompt_click = None
    if c1.button("⏰ Picos", use_container_width=True):
        prompt_click = "¿Cuáles son las horas de mayor afluencia y qué horario de mantenimiento sugieres?"
    if c2.button("📉 Ruido", use_container_width=True):
        prompt_click = "¿A qué se deben las lecturas inválidas y qué porcentaje representan?"
    if c3.button("🫀 Alertas", use_container_width=True):
        prompt_click = "¿Qué anomalías de BPM o SpO2 destacan en los registros válidos?"

    user_query = st.chat_input("Escribe tu consulta analítica...") or prompt_click

    if user_query:
        if not api_key_input:
            st.warning("⚠️ Ingresa tu OpenAI API Key en el campo superior derecho.")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": user_query})
            with chat_stream.chat_message("user"):
                st.markdown(f"👤 **Analista:** {user_query}")
                
            with chat_stream.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    try:
                        client = openai.OpenAI(api_key=api_key_input)
                        
                        system_prompt = f"""
                        Eres el asesor analítico de IoT del Tótem EAFIT.
                        Base de conocimiento del dataset completo:
                        {json.dumps(ai_context, ensure_ascii=False)}
                        
                        Filtros visibles en pantalla:
                        - Registros: {len(df_view)}
                        - Estudiante: {filtro_estudiante}
                        - Condición: {filtro_estado}
                        
                        Instrucciones:
                        1. Sé conciso, profesional y estructurado con viñetas.
                        2. Cita cifras exactas del contexto analítico (porcentajes, horas pico, BPM).
                        3. Orienta hacia decisiones operativas de bienestar universitario.
                        4. Mantén la aclaración ética de que no se emiten diagnósticos clínicos.
                        """
                        
                        messages_payload = [{"role": "system", "content": system_prompt}] + [
                            {"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages[-5:]
                        ]
                        
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages_payload,
                            temperature=0.3
                        )
                        reply = resp.choices[0].message.content
                        st.markdown(f"🤖 **Copiloto:** {reply}")
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except Exception as err:
                        st.error(f"Error de comunicación: {err}")
