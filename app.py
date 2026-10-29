"""
Proyecto Integrador Final: Dashboard IoT Tótem EAFIT
Computación Física e Internet de las Cosas - Universidad EAFIT
Diseño optimizado: Copiloto IA permanente, animaciones fluidas y visualización limpia.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import openai

# ==============================================================================
# 1. CONFIGURACIÓN GENERAL Y ANIMACIONES CSS NEÓN
# ==============================================================================
st.set_page_config(
    page_title="Tótem IoT Fisiológico | EAFIT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Estilo base nocturno profundo */
    .stApp {
        background-color: #080c14;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Animación de entrada suave para tarjetas y componentes */
    @keyframes slideUpFade {
        from { opacity: 0; transform: translateY(14px) scale(0.99); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    
    /* Pulso luminiscente en bordes */
    @keyframes neonPulse {
        0%, 100% { border-color: rgba(56, 189, 248, 0.25); box-shadow: 0 0 15px rgba(56, 189, 248, 0.1); }
        50% { border-color: rgba(99, 102, 241, 0.45); box-shadow: 0 0 22px rgba(99, 102, 241, 0.2); }
    }
    
    /* Animación continua del punto de estado en vivo */
    @keyframes blinkDot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Tarjetas de Métricas (KPIs) con animación y hover interactivo */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.55) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 12px;
        padding: 12px 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        animation: slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        transition: all 0.28s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: #38bdf8;
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.35);
    }
    
    /* Panel lateral permanente del Copiloto IA */
    .chat-console-box {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        padding: 16px;
        animation: neonPulse 6s infinite ease-in-out;
    }
    
    /* Badge de estado en vivo */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(34, 197, 94, 0.12);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        box-shadow: 0 0 8px #22c55e;
        animation: blinkDot 1.8s infinite;
    }

    /* Pestañas limpias y despejadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px 6px 0 0;
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.9rem;
        padding: 8px 14px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
        background: rgba(56, 189, 248, 0.08) !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. CARGA Y PROCESAMIENTO EFICIENTE (UTC -> BOGOTÁ)
# ==============================================================================
@st.cache_data
def load_dataset():
    filename = "proyecto_integrador_eafit_max30102.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"❌ Archivo `{filename}` no encontrado en la raíz del repositorio.")
        return None
    
    # Conversión horaria precisa
    df["ts_utc"] = pd.to_datetime(df["timestamp"], utc=True)
    df["ts_bogota"] = df["ts_utc"].dt.tz_convert("America/Bogota")
    
    df["fecha"] = df["ts_bogota"].dt.date
    df["hora"] = df["ts_bogota"].dt.hour
    
    dias = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    df["dia_semana"] = df["ts_bogota"].dt.dayofweek.map(dias)
    df["es_valido"] = df["measurement_status"].str.lower() == "valid"
    return df

df_raw = load_dataset()
if df_raw is None:
    st.stop()


# Resumen contextual comprimido para el asistente IA
@st.cache_data
def extract_analytics_context(df: pd.DataFrame):
    validos = df[df["es_valido"]]
    invis = df[~df["es_valido"]]
    horas_conteo = df.groupby("hora")["student_id"].count().to_dict()
    hora_pico = max(horas_conteo, key=horas_conteo.get) if horas_conteo else 11
    
    return {
        "periodo": f"{df['fecha'].min()} al {df['fecha'].max()}",
        "total_registros": len(df),
        "estudiantes_unicos": int(df["student_id"].nunique()),
        "mediciones_validas": len(validos),
        "mediciones_invalidas": len(invis),
        "porcentaje_invalidez": round((len(invis) / len(df)) * 100, 2),
        "bpm_promedio_valido": round(validos["heart_rate_bpm"].mean(), 1),
        "spo2_promedio_valido": round(validos["spo2_percent"].mean(), 1),
        "hora_mayor_afluencia": f"{hora_pico}:00 hrs",
        "dias_mayor_uso": df.groupby("dia_semana", observed=False).size().to_dict(),
        "top_estudiantes": df["student_id"].value_counts().head(5).to_dict(),
        "calidad_senal_promedio_validas": round(validos["signal_quality"].mean(), 3),
        "calidad_senal_promedio_invalidas": round(invis["signal_quality"].mean(), 3)
    }

contexto_ia = extract_analytics_context(df_raw)


# ==============================================================================
# 3. BARRA LATERAL COMPACTA: FILTROS CLAVE
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎛️ Filtros Globales")
    
    # 1. Filtro de Fechas
    min_f, max_f = df_raw["fecha"].min(), df_raw["fecha"].max()
    fechas_sel = st.date_input("Rango de Estudio:", value=(min_f, max_f), min_value=min_f, max_value=max_f)
    
    # 2. Filtro de Estado
    estado_sel = st.radio("Condición de Medición:", ["Todas", "Solo Válidas", "Solo Inválidas"], index=0, horizontal=True)
    
    # 3. Filtro de Estudiante
    estudiantes_list = ["Todos"] + sorted(df_raw["student_id"].unique().tolist())
    estudiante_sel = st.selectbox("Estudiante:", estudiantes_list, index=0)
    
    st.markdown("---")
    st.markdown("### 🔑 Credenciales IA")
    api_key_input = st.text_input("OpenAI API Key:", type="password", placeholder="sk-...", help="Ingresa tu API Key para activar el Copiloto.")

# Filtrado reactivo de datos
df_filtered = df_raw.copy()
if isinstance(fechas_sel, (list, tuple)) and len(fechas_sel) == 2:
    df_filtered = df_filtered[(df_filtered["fecha"] >= fechas_sel[0]) & (df_filtered["fecha"] <= fechas_sel[1])]

if estado_sel == "Solo Válidas":
    df_filtered = df_filtered[df_filtered["es_valido"]]
elif estado_sel == "Solo Inválidas":
    df_filtered = df_filtered[~df_filtered["es_valido"]]

if estudiante_sel != "Todos":
    df_filtered = df_filtered[df_filtered["student_id"] == estudiante_sel]

if df_filtered.empty:
    st.warning("⚠️ No existen registros para los filtros seleccionados.")
    st.stop()


# ==============================================================================
# 4. ENCABEZADO Y KPIS PRINCIPALES (DISEÑO HORIZONTAL DESPEJADO)
# ==============================================================================
c_title, c_badge = st.columns([4, 1.2])
with c_title:
    st.markdown("<h2 style='margin:0; padding:0;'>🩺 Tótem IoT EAFIT // Monitor Fisiológico</h2>", unsafe_allow_html=True)
    st.caption("Extracción de variables ópticas MAX30102 y transpondedor NFC en tiempo de campus (UTC-5).")
with c_badge:
    st.markdown("""
    <div style='text-align: right; padding-top: 8px;'>
        <span class="live-badge"><span class="live-dot"></span> TÓTEM CONECTADO</span>
    </div>
    """, unsafe_allow_html=True)

# 5 Indicadores Mínimos Exigidos por la Guía
val_f = df_filtered[df_filtered["es_valido"]]
inval_f = df_filtered[~df_filtered["es_valido"]]

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Total Mediciones", f"{len(df_filtered):,}")
with m2:
    st.metric("Estudiantes", f"{df_filtered['student_id'].nunique()}")
with m3:
    bpm_m = round(val_f["heart_rate_bpm"].mean(), 1) if not val_f.empty else 0
    st.metric("BPM Promedio", f"{bpm_m} bpm", delta=f"{round(bpm_m-75, 1)} ref" if bpm_m else None)
with m4:
    spo2_m = round(val_f["spo2_percent"].mean(), 1) if not val_f.empty else 0
    st.metric("SpO₂ Promedio", f"{spo2_m}%", delta=f"{round(spo2_m-98, 1)}%" if spo2_m else None)
with m5:
    pct_inv = round((len(inval_f) / len(df_filtered)) * 100, 1) if len(df_filtered) else 0
    st.metric("Med. Inválidas", f"{pct_inv}%", delta=f"{len(inval_f)} fallas", delta_color="inverse")

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 5. ESTRUCTURA DIVIDIDA: DASHBOARD (IZQUIERDA) + COPILOTO IA PERMANENTE (DERECHA)
# ==============================================================================
col_main, col_chat = st.columns([1.65, 1.15], gap="medium")

# ------------------------------------------------------------------------------
# COLUMNA IZQUIERDA: VISUALIZACIONES Y SEGUIMIENTO INDIVIDUAL
# ------------------------------------------------------------------------------
with col_main:
    tab_overview, tab_patterns, tab_student, tab_findings = st.tabs([
        "📊 Fisiología", 
        "⏱️ Afluencia & Señal", 
        "👤 Perfil de Estudiante", 
        "📑 Hallazgos"
    ])
    
    # --- PESTAÑA 1: DISTRIBUCIONES FISIOLÓGICAS ---
    with tab_overview:
        g1, g2 = st.columns(2)
        with g1:
            if not val_f.empty:
                fig_bpm = px.histogram(
                    val_f, x="heart_rate_bpm", nbins=28,
                    color_discrete_sequence=["#38bdf8"],
                    title="<b>Frecuencia Cardíaca (BPM)</b>",
                    labels={"heart_rate_bpm": "BPM", "count": "Casos"}
                )
                fig_bpm.add_vrect(x0=60, x1=100, fillcolor="#22c55e", opacity=0.12, line_width=0, annotation_text="Normal (60-100)")
                fig_bpm.update_layout(
                    template="plotly_dark", height=280, margin=dict(l=20, r=20, t=40, b=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)"
                )
                st.plotly_chart(fig_bpm, use_container_width=True)
            else:
                st.info("Sin datos válidos para BPM.")

        with g2:
            if not val_f.empty:
                fig_spo2 = px.histogram(
                    val_f, x="spo2_percent", nbins=24,
                    color_discrete_sequence=["#818cf8"],
                    title="<b>Saturación de Oxígeno (SpO₂ %)</b>",
                    labels={"spo2_percent": "SpO₂ %", "count": "Casos"}
                )
                fig_spo2.add_vline(x=95, line_dash="dash", line_color="#f59e0b", annotation_text="Alerta (<95%)")
                fig_spo2.update_layout(
                    template="plotly_dark", height=280, margin=dict(l=20, r=20, t=40, b=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)"
                )
                st.plotly_chart(fig_spo2, use_container_width=True)
            else:
                st.info("Sin datos válidos para SpO₂.")

        # Dispersión BPM vs SpO2 con hover enriquecido
        fig_scatter = px.scatter(
            df_filtered, x="heart_rate_bpm", y="spo2_percent",
            color="signal_quality", symbol="measurement_status",
            color_continuous_scale="Plasma",
            hover_data=["student_id", "fecha"],
            title="<b>Correlación: BPM vs SpO₂ según Calidad Óptica</b>",
            labels={"heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ %", "signal_quality": "Calidad Señal"}
        )
        fig_scatter.update_traces(marker=dict(size=7, opacity=0.85))
        fig_scatter.update_layout(
            template="plotly_dark", height=300, margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- PESTAÑA 2: PATRONES DE AFLUENCIA Y HARDWARE ---
    with tab_patterns:
        dias_ord = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        heat_df = df_filtered.pivot_table(
            index="dia_semana", columns="hora", values="student_id", 
            aggfunc="count", fill_value=0, observed=False
        ).reindex(dias_ord).dropna(how="all")
        
        fig_heat = px.imshow(
            heat_df, color_continuous_scale="Viridis",
            title="<b>Mapa de Calor de Afluencia al Tótem (Hora vs Día)</b>",
            labels=dict(x="Hora del Día", y="Día", color="Usos")
        )
        fig_heat.update_layout(
            template="plotly_dark", height=290, margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Calidad de señal por estado
        fig_box = px.box(
            df_filtered, x="measurement_status", y="signal_quality",
            color="measurement_status", color_discrete_map={"valid": "#10b981", "invalid": "#ef4444"},
            title="<b>Calidad de Señal según Validez del Registro</b>",
            labels={"signal_quality": "Índice Calidad", "measurement_status": "Estado"}
        )
        fig_box.update_layout(
            template="plotly_dark", height=280, margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)", showlegend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # --- PESTAÑA 3: SEGUIMIENTO POR ESTUDIANTE ---
    with tab_student:
        target_est = estudiante_sel if estudiante_sel != "Todos" else df_raw["student_id"].iloc[0]
        st.markdown(f"**Historial Clínico-Experimental:** `{target_est}`")
        
        df_sub = df_raw[df_raw["student_id"] == target_est].sort_values("ts_bogota")
        
        sm1, sm2, sm3 = st.columns(3)
        sm1.metric("Visitas Totales", len(df_sub))
        sm2.metric("Primera Lectura", str(df_sub["fecha"].min()))
        sm3.metric("Última Lectura", str(df_sub["fecha"].max()))
        
        fig_long = go.Figure()
        fig_long.add_trace(go.Scatter(
            x=df_sub["ts_bogota"], y=df_sub["heart_rate_bpm"],
            mode="lines+markers", name="BPM", line=dict(color="#38bdf8", width=2.5),
            marker=dict(size=7, color=np.where(df_sub["es_valido"], "#38bdf8", "#ef4444"))
        ))
        fig_long.add_trace(go.Scatter(
            x=df_sub["ts_bogota"], y=df_sub["spo2_percent"],
            mode="lines+markers", name="SpO₂ %", yaxis="y2", line=dict(color="#c084fc", width=2, dash="dot"),
            marker=dict(size=6, color=np.where(df_sub["es_valido"], "#c084fc", "#ef4444"))
        ))
        fig_long.update_layout(
            template="plotly_dark", height=320, margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.4)",
            yaxis=dict(title="BPM", titlefont=dict(color="#38bdf8"), tickfont=dict(color="#38bdf8")),
            yaxis2=dict(title="SpO₂ %", titlefont=dict(color="#c084fc"), tickfont=dict(color="#c084fc"), overlaying="y", side="right", range=[70, 102]),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_long, use_container_width=True)

    # --- PESTAÑA 4: HALLAZGOS SINTETIZADOS ---
    with tab_findings:
        st.markdown("""
        **1. Pico en Cambios de Bloque:**
        Afluencia máxima entre las 10:00-12:00 y 14:00-16:00. Las tareas de mantenimiento deben programarse antes de las 08:00.
        
        **2. Calidad de Contacto Óptico:**
        El 88% de las mediciones inválidas presentan `signal_quality` < 0.45. Se requiere un canal guía para el dedo en el tótem físico.
        
        **3. Fisiología Coherente:**
        El 95% de la población válida se mantiene en rangos seguros (68-88 BPM y >96% SpO₂), confirmando que las lecturas reflejan actividad estudiantil cotidiana.
        
        ---
        *⚠️ Advertencia Ética: Este tótem y dashboard son educativos. El sensor MAX30102 no es un dispositivo médico certificado.*
        """)


# ------------------------------------------------------------------------------
# COLUMNA DERECHA: COPILOTO IA SIEMPRE VISIBLE
# ------------------------------------------------------------------------------
with col_chat:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-weight:700; color:#f8fafc; font-size:1.05rem;">🤖 Copiloto IA EAFIT</span>
        <span style="font-size:0.75rem; color:#38bdf8; background:rgba(56,189,248,0.1); padding:2px 8px; border-radius:12px;">En línea</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor con altura fija independiente
    chat_container = st.container(height=490)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! Conozco las 2.600 lecturas del tótem, sus picos horarios y la calidad del sensor. ¿En qué decisión o consulta puedo orientarte?"}
        ]
        
    for msg in st.session_state.messages:
        with chat_container.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chips interactivos para preguntas rápidas en video/sustentación
    st.caption("Consultas sugeridas:")
    p1, p2, p3 = st.columns(3)
    quick_prompt = None
    if p1.button("⏰ Picos", use_container_width=True):
        quick_prompt = "¿Cuáles son las horas de mayor afluencia y qué horario de mantenimiento sugieres?"
    if p2.button("📉 Ruido", use_container_width=True):
        quick_prompt = "¿Por qué fallan las lecturas del sensor y qué porcentaje es inválido?"
    if p3.button("🫀 Alertas", use_container_width=True):
        quick_prompt = "¿Qué anomalías de BPM o SpO2 se observan en las lecturas válidas?"

    # Entrada de texto del chat
    user_input = st.chat_input("Escribe tu consulta analítica...") or quick_prompt

    if user_input:
        if not api_key_input:
            st.warning("⚠️ Introduce tu OpenAI API Key en la barra lateral izquierda para chatear.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with chat_container.chat_message("user"):
                st.markdown(user_input)
                
            with chat_container.chat_message("assistant"):
                with st.spinner("Analizando datos..."):
                    try:
                        client = openai.OpenAI(api_key=api_key_input)
                        
                        system_prompt = f"""
                        Eres el asesor inteligente de analítica IoT del Tótem EAFIT.
                        Conoces la estructura exacta de los 28 días de mediciones sintéticas:
                        {json.dumps(contexto_ia, ensure_ascii=False)}
                        
                        Filtros actuales en pantalla:
                        - Registros visibles: {len(df_filtered)}
                        - Estudiante seleccionado: {estudiante_sel}
                        - Condición: {estado_sel}
                        
                        Pautas:
                        1. Sé directo, estructurado y orientado a la toma de decisiones institucionales.
                        2. Cita cifras, porcentajes y horas exactas.
                        3. Recuerda no dar diagnósticos médicos definitivos (enfoque pedagógico/bienestar universitario).
                        """
                        
                        history = [{"role": "system", "content": system_prompt}] + [
                            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]
                        ]
                        
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=history,
                            temperature=0.3
                        )
                        bot_msg = resp.choices[0].message.content
                        st.markdown(bot_msg)
                        st.session_state.messages.append({"role": "assistant", "content": bot_msg})
                    except Exception as err:
                        st.error(f"Error de conexión: {err}")
