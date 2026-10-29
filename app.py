"""
Proyecto Integrador Final: Dashboard IoT Tótem EAFIT
Computación Física e Internet de las Cosas - Universidad EAFIT
Diseño de precisión: Copiloto IA permanente, alineación proporcional y visualización fluida.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import openai

# ==============================================================================
# 1. CONFIGURACIÓN GENERAL Y SISTEMA DE DISEÑO VISUAL
# ==============================================================================
st.set_page_config(
    page_title="Tótem IoT Fisiológico | EAFIT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Tipografía y paleta base */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    .stApp {
        background-color: #080c15;
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Animación de entrada suave */
    @keyframes smoothFadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Pulso continuo para el badge de estado */
    @keyframes livePulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(0.85); opacity: 0.4; }
    }
    
    /* Encabezado del dashboard */
    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        animation: smoothFadeIn 0.4s ease-out;
    }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
    }
    
    .live-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
        animation: livePulse 2s infinite ease-in-out;
    }

    /* Tarjetas de Métricas (KPIs) con alineación y glow controlado */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.6) 100%);
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        animation: smoothFadeIn 0.5s ease-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.5);
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.18);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        font-feature-settings: "tnum";
    }

    /* Pestañas de Navegación */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.86rem;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
        background: rgba(56, 189, 248, 0.06) !important;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #050810;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Tarjetas de hallazgos y decisiones */
    .insight-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 3px solid #38bdf8;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease;
    }
    .insight-card:hover {
        border-color: rgba(56, 189, 248, 0.6);
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. CARGA Y PROCESAMIENTO ROBUSTO DE DATOS (ZONA HORARIA COLOMBIA)
# ==============================================================================
@st.cache_data
def load_and_prepare_dataset():
    filename = "proyecto_integrador_eafit_max30102.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"❌ No se encontró `{filename}` en el directorio raíz. Asegúrate de incluirlo en el repositorio.")
        return None
    
    # Normalización temporal UTC -> Bogotá (UTC-5)
    df["ts_utc"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ts_bogota"] = df["ts_utc"].dt.tz_convert("America/Bogota")
    
    df["fecha"] = df["ts_bogota"].dt.date
    df["hora"] = df["ts_bogota"].dt.hour
    
    dias_map = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    df["dia_semana"] = df["ts_bogota"].dt.dayofweek.map(dias_map)
    df["es_valido"] = df["measurement_status"].str.lower() == "valid"
    return df

df_raw = load_and_prepare_dataset()
if df_raw is None:
    st.stop()


# Síntesis analítica profunda para el Copiloto IA
@st.cache_data
def generate_ai_context(df: pd.DataFrame):
    validos = df[df["es_valido"]]
    invis = df[~df["es_valido"]]
    conteo_horas = df.groupby("hora")["student_id"].count().to_dict()
    hora_pico = max(conteo_horas, key=conteo_horas.get) if conteo_horas else 11
    dias_orden = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    conteo_dias = df.groupby("dia_semana", observed=False)["student_id"].count().reindex(dias_orden).dropna().to_dict()

    return {
        "periodo_fechas": f"{df['fecha'].min()} al {df['fecha'].max()}",
        "total_registros": len(df),
        "estudiantes_unicos": int(df["student_id"].nunique()),
        "mediciones_validas": len(validos),
        "mediciones_invalidas": len(invis),
        "tasa_invalidez_pct": round((len(invis) / len(df)) * 100, 1),
        "fisiologia_valida": {
            "bpm_promedio": round(validos["heart_rate_bpm"].mean(), 1),
            "bpm_mediana": round(validos["heart_rate_bpm"].median(), 1),
            "bpm_q25_q75": [round(validos["heart_rate_bpm"].quantile(0.25), 1), round(validos["heart_rate_bpm"].quantile(0.75), 1)],
            "spo2_promedio": round(validos["spo2_percent"].mean(), 1),
            "spo2_mediana": round(validos["spo2_percent"].median(), 1)
        },
        "calidad_senal": {
            "media_validas": round(validos["signal_quality"].mean(), 3),
            "media_invalidas": round(invis["signal_quality"].mean(), 3)
        },
        "patrones_afluencia": {
            "hora_pico": f"{hora_pico}:00 horas",
            "distribucion_dias": conteo_dias
        },
        "top_5_estudiantes_recurrentes": df["student_id"].value_counts().head(5).to_dict()
    }

contexto_ia = generate_ai_context(df_raw)


# ==============================================================================
# 3. FILTROS EN BARRA LATERAL (LIMPIOS Y ACCIONABLES)
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚡ Parámetros del Tótem")
    st.caption("Control de visualización reactiva")
    
    # 1. Rango de Fechas
    f_min, f_max = df_raw["fecha"].min(), df_raw["fecha"].max()
    rango_fecha = st.date_input("Período de Análisis:", value=(f_min, f_max), min_value=f_min, max_value=f_max)
    
    # 2. Estado de Medición
    filtro_estado = st.radio("Validez de Registros:", ["Todos", "Solo Válidos", "Solo Inválidos"], index=0, horizontal=True)
    
    # 3. Estudiante
    estudiantes_disponibles = ["Todos"] + sorted(df_raw["student_id"].unique().tolist())
    filtro_estudiante = st.selectbox("Estudiante (ID):", estudiantes_disponibles, index=0)
    
    st.markdown("---")
    st.markdown("### 🔑 Inteligencia Artificial")
    api_key_input = st.text_input(
        "OpenAI API Key:",
        type="password",
        placeholder="sk-...",
        help="Clave para habilitar el razonamiento del Copiloto IA."
    )
    
    st.markdown("---")
    st.caption("EAFIT · Computación Física e IoT | MAX30102 + ESP32")

# Aplicación matemática de filtros
df_view = df_raw.copy()
if isinstance(rango_fecha, (list, tuple)) and len(rango_fecha) == 2:
    df_view = df_view[(df_view["fecha"] >= rango_fecha[0]) & (df_view["fecha"] <= rango_fecha[1])]

if filtro_estado == "Solo Válidos":
    df_view = df_view[df_view["es_valido"]]
elif filtro_estado == "Solo Inválidos":
    df_view = df_view[~df_view["es_valido"]]

if filtro_estudiante != "Todos":
    df_view = df_view[df_view["student_id"] == filtro_estudiante]

if df_view.empty:
    st.warning("⚠️ No existen registros con la combinación de filtros seleccionada.")
    st.stop()


# ==============================================================================
# 4. ENCABEZADO Y TARJETAS DE MÉTRICAS (PROPORCIONADAS)
# ==============================================================================
st.markdown("""
<div class="dashboard-header">
    <div>
        <h2 style="margin: 0; font-size: 1.55rem; font-weight: 700; color: #f8fafc;">Tótem Fisiológico EAFIT // Monitor IoT</h2>
        <p style="margin: 2px 0 0 0; font-size: 0.85rem; color: #94a3b8;">Fotopletismografía óptica MAX30102 · Campus EAFIT (UTC-5)</p>
    </div>
    <div class="live-indicator">
        <span class="live-dot"></span> TÓTEM ACTIVO
    </div>
</div>
""", unsafe_allow_html=True)

# Cálculo de los 5 Indicadores Requeridos
validos_view = df_view[df_view["es_valido"]]
invalidos_view = df_view[~df_view["es_valido"]]

total_n = len(df_view)
estudiantes_n = df_view["student_id"].nunique()
bpm_mean = round(validos_view["heart_rate_bpm"].mean(), 1) if not validos_view.empty else 0.0
spo2_mean = round(validos_view["spo2_percent"].mean(), 1) if not validos_view.empty else 0.0
inval_count = len(invalidos_view)
inval_pct = round((inval_count / total_n) * 100, 1) if total_n > 0 else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Mediciones", f"{total_n:,}")
k2.metric("Estudiantes", f"{estudiantes_n}")
k3.metric("BPM Promedio", f"{bpm_mean} bpm", delta=f"{round(bpm_mean - 75.0, 1)} ref" if bpm_mean > 0 else None)
k4.metric("SpO₂ Promedio", f"{spo2_mean}%", delta=f"{round(spo2_mean - 98.0, 1)}%" if spo2_mean > 0 else None)
k5.metric("Tasa de Fallas", f"{inval_pct}%", delta=f"{inval_count} inv.", delta_color="inverse")

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 5. ESPACIO DE TRABAJO EQUILIBRADO: ANALÍTICA (62%) | COPILOTO IA (38%)
# ==============================================================================
col_analytics, col_copilot = st.columns([1.62, 1.0], gap="large")

# ------------------------------------------------------------------------------
# COLUMNA IZQUIERDA: ANALÍTICA Y VISUALIZACIONES
# ------------------------------------------------------------------------------
with col_analytics:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Biomarcadores", 
        "⏱️ Patrones de Campus", 
        "👤 Historial Estudiante", 
        "📑 Hallazgos Clave"
    ])
    
    # --- PESTAÑA 1: DISTRIBUCIÓN DE BIOMARCADORES ---
    with tab1:
        c_hist1, c_hist2 = st.columns(2)
        with c_hist1:
            if not validos_view.empty:
                fig_bpm = px.histogram(
                    validos_view, x="heart_rate_bpm", nbins=26,
                    color_discrete_sequence=["#38bdf8"],
                    title="<b>Distribución: Frecuencia Cardíaca (BPM)</b>",
                    labels={"heart_rate_bpm": "BPM", "count": "Frecuencia"}
                )
                fig_bpm.add_vrect(
                    x0=60, x1=100, fillcolor="#10b981", opacity=0.12, line_width=0,
                    annotation_text="Normal (60-100)", annotation_position="top left",
                    annotation_font=dict(size=10, color="#10b981")
                )
                fig_bpm.update_layout(
                    template="plotly_dark", height=240, margin=dict(l=30, r=20, t=35, b=25),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
                    font=dict(family="Inter", size=11),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_bpm, use_container_width=True)
            else:
                st.info("Sin registros válidos de BPM.")

        with c_hist2:
            if not validos_view.empty:
                fig_spo2 = px.histogram(
                    validos_view, x="spo2_percent", nbins=22,
                    color_discrete_sequence=["#818cf8"],
                    title="<b>Distribución: Saturación de Oxígeno (SpO₂)</b>",
                    labels={"spo2_percent": "SpO₂ %", "count": "Frecuencia"}
                )
                fig_spo2.add_vline(
                    x=95, line_dash="dash", line_color="#f59e0b",
                    annotation_text="Alerta (<95%)", annotation_position="top left",
                    annotation_font=dict(size=10, color="#f59e0b")
                )
                fig_spo2.update_layout(
                    template="plotly_dark", height=240, margin=dict(l=30, r=20, t=35, b=25),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
                    font=dict(family="Inter", size=11),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_spo2, use_container_width=True)
            else:
                st.info("Sin registros válidos de SpO₂.")

        # Dispersión BPM vs SpO2 con escala de calidad
        fig_scatter = px.scatter(
            df_view, x="heart_rate_bpm", y="spo2_percent",
            color="signal_quality", symbol="measurement_status",
            color_continuous_scale="Tealgrn",
            title="<b>Correlación Fisiológica vs. Calidad de Señal Óptica</b>",
            labels={"heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ %", "signal_quality": "Calidad Señal"}
        )
        fig_scatter.update_traces(marker=dict(size=6.5, opacity=0.8))
        fig_scatter.update_layout(
            template="plotly_dark", height=260, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            font=dict(family="Inter", size=11),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- PESTAÑA 2: DINÁMICA DE CAMPUS Y CALIDAD IOT ---
    with tab2:
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
            template="plotly_dark", height=260, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            font=dict(family="Inter", size=11)
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Comparación de calidad óptica de señal
        fig_box = px.box(
            df_view, x="measurement_status", y="signal_quality",
            color="measurement_status",
            color_discrete_map={"valid": "#10b981", "invalid": "#f43f5e"},
            title="<b>Distribución de Calidad de Señal según Validez del Registro</b>",
            labels={"signal_quality": "Índice de Calidad (0.0 - 1.0)", "measurement_status": "Estado"}
        )
        fig_box.update_layout(
            template="plotly_dark", height=240, margin=dict(l=30, r=20, t=35, b=25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.45)",
            showlegend=False, font=dict(family="Inter", size=11),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # --- PESTAÑA 3: SEGUIMIENTO LONGITUDINAL (SIN ERRORES DE SINTAXIS) ---
    with tab3:
        estudiante_objetivo = filtro_estudiante if filtro_estudiante != "Todos" else df_raw["student_id"].iloc[0]
        df_target = df_raw[df_raw["student_id"] == estudiante_objetivo].sort_values("ts_bogota")
        
        st.markdown(f"<span style='color:#38bdf8; font-weight:600;'>Historial de Medición:</span> <code>{estudiante_objetivo}</code>", unsafe_allow_html=True)
        
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Visitas Registradas", f"{len(df_target)}")
        sc2.metric("Primera Lectura", f"{df_target['fecha'].min()}")
        sc3.metric("Última Lectura", f"{df_target['fecha'].max()}")
        
        # Gráfica de doble eje corregida con la sintaxis moderna de Plotly
        fig_long = go.Figure()
        
        # Serie BPM (Eje Primario Y1)
        fig_long.add_trace(go.Scatter(
            x=df_target["ts_bogota"],
            y=df_target["heart_rate_bpm"],
            mode="lines+markers",
            name="BPM",
            line=dict(color="#38bdf8", width=2.5),
            marker=dict(size=7, color=np.where(df_target["es_valido"], "#38bdf8", "#f43f5e"))
        ))
        
        # Serie SpO2 (Eje Secundario Y2)
        fig_long.add_trace(go.Scatter(
            x=df_target["ts_bogota"],
            y=df_target["spo2_percent"],
            mode="lines+markers",
            name="SpO₂ %",
            yaxis="y2",
            line=dict(color="#c084fc", width=2, dash="dot"),
            marker=dict(size=6, color=np.where(df_target["es_valido"], "#c084fc", "#f43f5e"))
        ))
        
        # Actualización de layout sin invocar 'titlefont' deprecado
        fig_long.update_layout(
            template="plotly_dark",
            height=280,
            margin=dict(l=35, r=35, t=30, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.45)",
            font=dict(family="Inter", size=11),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(
                title=dict(text="BPM (ppm)", font=dict(color="#38bdf8", size=11)),
                tickfont=dict(color="#38bdf8"),
                gridcolor="rgba(255,255,255,0.06)"
            ),
            yaxis2=dict(
                title=dict(text="SpO₂ (%)", font=dict(color="#c084fc", size=11)),
                tickfont=dict(color="#c084fc"),
                overlaying="y",
                side="right",
                range=[70, 102],
                showgrid=False
            ),
            legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_long, use_container_width=True)

    # --- PESTAÑA 4: HALLAZGOS Y DECISIONES CLAVE ---
    with tab4:
        st.markdown(f"""
        <div class="insight-card">
            <h5 style="margin: 0 0 4px 0; color: #38bdf8;">1. Concentración Horaria en Cambios de Bloque</h5>
            <p style="margin: 0; font-size: 0.85rem; color: #cbd5e1;">
                El uso máximo ocurre de <b>10:00 a 12:00</b> y de <b>14:00 a 16:00</b>. Los mantenimientos del tótem y la limpieza del sensor deben programarse antes de las 08:00 para garantizar disponibilidad continua.
            </p>
        </div>
        <div class="insight-card">
            <h5 style="margin: 0 0 4px 0; color: #818cf8;">2. Degeneración Óptica por Retiro Prematuro</h5>
            <p style="margin: 0; font-size: 0.85rem; color: #cbd5e1;">
                El <b>{contexto_ia['tasa_invalidez_pct']}%</b> de registros inválidos presenta una calidad óptica media de <b>{contexto_ia['calidad_senal']['media_invalidas']}</b> frente a <b>{contexto_ia['calidad_senal']['media_validas']}</b> en lecturas válidas, señalando la necesidad de guías físicas para el dedo en el dispositivo.
            </p>
        </div>
        <div class="insight-card">
            <h5 style="margin: 0 0 4px 0; color: #34d399;">3. Estabilidad en la Población Estudiantil</h5>
            <p style="margin: 0; font-size: 0.85rem; color: #cbd5e1;">
                El 50% central de los registros válidos se ubica entre <b>{contexto_ia['fisiologia_valida']['bpm_q25_q75'][0]} y {contexto_ia['fisiologia_valida']['bpm_q25_q75'][1]} BPM</b>, lo que coincide con valores típicos de reposo universitario.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("⚠️ Nota: Dataset sintético con fines pedagógicos. El MAX30102 no es un dispositivo médico certificado.")


# ------------------------------------------------------------------------------
# COLUMNA DERECHA: COPILOTO IA SIEMPRE VISIBLE (CONSOLA DEDICADA)
# ------------------------------------------------------------------------------
with col_copilot:
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">🤖 Copiloto IA EAFIT</span>
        <span style="font-size: 0.72rem; color: #38bdf8; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.25); padding: 2px 8px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">ACTIVO</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor con altura acotada para evitar el estiramiento vertical de la página
    chat_box = st.container(height=480)
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{
            "role": "assistant",
            "content": "Hola. Analizo las 2.600 lecturas del tótem, patrones de afluencia y fallas del sensor MAX30102. ¿En qué decisión institucional puedo apoyarte?"
        }]
    
    # Renderizado del historial
    for message in st.session_state.chat_history:
        with chat_box.chat_message(message["role"]):
            st.markdown(f"<div style='font-size: 0.86rem; line-height: 1.45;'>{message['content']}</div>", unsafe_allow_html=True)
            
    # Botones de consulta rápida
    st.caption("Consultas inmediatas:")
    b1, b2, b3 = st.columns(3)
    quick_query = None
    if b1.button("⏰ Picos", use_container_width=True):
        quick_query = "¿Cuáles son las horas de mayor afluencia y qué horario de mantenimiento sugieres?"
    if b2.button("📉 Ruido", use_container_width=True):
        quick_query = "¿A qué se deben las lecturas inválidas y qué porcentaje representan?"
    if b3.button("🫀 Alertas", use_container_width=True):
        quick_query = "¿Qué anomalías de BPM o SpO2 destacan en los registros válidos?"

    # Entrada de texto del usuario
    user_prompt = st.chat_input("Pregunta sobre métricas, horas o planes...") or quick_query
    
    if user_prompt:
        if not api_key_input:
            st.warning("⚠️ Introduce tu OpenAI API Key en la barra lateral para consultar al copiloto.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            with chat_box.chat_message("user"):
                st.markdown(f"<div style='font-size: 0.86rem;'>{user_prompt}</div>", unsafe_allow_html=True)
                
            with chat_box.chat_message("assistant"):
                with st.spinner("Analizando registros..."):
                    try:
                        client = openai.OpenAI(api_key=api_key_input)
                        
                        system_instructions = f"""
                        Eres el asesor analítico de IoT del proyecto Tótem Fisiológico EAFIT.
                        Tienes acceso a los parámetros globales del dataset completo:
                        {json.dumps(contexto_ia, ensure_ascii=False)}
                        
                        Filtros aplicados actualmente en pantalla:
                        - Registros visibles: {len(df_view)}
                        - Estudiante seleccionado: {filtro_estudiante}
                        - Condición de validez: {filtro_estado}
                        
                        Instrucciones:
                        1. Sé conciso, profesional y estructurado (emplea viñetas para datos numéricos).
                        2. Cita cifras exactas del contexto analítico (porcentajes, horas pico, BPM).
                        3. Propón decisiones operativas concretas para el campus.
                        4. Mantén la aclaración ética de que no se emiten diagnósticos clínicos.
                        """
                        
                        conversation_payload = [{"role": "system", "content": system_instructions}] + [
                            {"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history[-5:]
                        ]
                        
                        api_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=conversation_payload,
                            temperature=0.3
                        )
                        bot_text = api_response.choices[0].message.content
                        st.markdown(f"<div style='font-size: 0.86rem; line-height: 1.45;'>{bot_text}</div>", unsafe_allow_html=True)
                        st.session_state.chat_history.append({"role": "assistant", "content": bot_text})
                    except Exception as err:
                        st.error(f"Error de comunicación con OpenAI: {err}")
