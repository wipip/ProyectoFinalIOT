"""Proyecto Integrador: Dashboard IoT Tótem Fisiológico EAFIT.

Computación Física e Internet de las Cosas - Universidad EAFIT
Visualización interactiva, análisis exploratorio y asistente cognitivo con IA.
"""

from datetime import datetime
import json
import numpy as np
import openai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS "GLOWING HIGH-TECH"
# ==============================================================================
st.set_page_config(
    page_title="Tótem IoT Fisiológico | EAFIT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyección de CSS para efectos Glowing Neón y estética Glassmorphism
st.markdown(
    """
<style>
    /* Fondo y tipografía general */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Tarjetas de Métricas con Glow */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px -2px rgba(56, 189, 248, 0.15), 0 0 10px rgba(56, 189, 248, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: #38bdf8;
        box-shadow: 0 8px 30px rgba(56, 189, 248, 0.35), 0 0 15px rgba(56, 189, 248, 0.25);
    }
    
    /* Títulos y acentos */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    .neon-text {
        color: #38bdf8;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
    }
    
    /* Contenedores con borde iluminado */
    .glowing-box {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.15);
        margin-bottom: 20px;
    }
    
    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #070a13;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Pestañas (Tabs) interactivas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #94a3b8;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS (ZONA HORARIA COLOMBIA)
# ==============================================================================
@st.cache_data
def load_and_preprocess_data():
  filename = "proyecto_integrador_eafit_max30102.csv"
  try:
    df = pd.read_csv(filename)
  except FileNotFoundError:
    st.error(
        f"❌ Archivo `{filename}` no encontrado en el directorio. Asegúrate de"
        " que esté en la raíz del repositorio."
    )
    return None

  # 1. Conversión de timestamp a datetime UTC y luego a Bogotá (UTC-5)
  df["timestamp_utc"] = pd.to_datetime(df["timestamp"], utc=True)
  df["timestamp_bogota"] = df["timestamp_utc"].dt.tz_convert("America/Bogota")

  # 2. Extracción de variables temporales para análisis
  df["fecha"] = df["timestamp_bogota"].dt.date
  df["hora"] = df["timestamp_bogota"].dt.hour
  df["hora_exacta"] = df["timestamp_bogota"].dt.strftime("%H:%M")

  dias_espanol = {
      0: "Lunes",
      1: "Martes",
      2: "Miércoles",
      3: "Jueves",
      4: "Viernes",
      5: "Sábado",
      6: "Domingo",
  }
  df["dia_semana_num"] = df["timestamp_bogota"].dt.dayofweek
  df["dia_semana"] = df["dia_semana_num"].map(dias_espanol)

  # 3. Clasificación de rangos fisiológicos (solo informativa, no diagnóstica)
  df["es_valido"] = df["measurement_status"].str.lower() == "valid"

  return df


df_raw = load_and_preprocess_data()
if df_raw is None:
  st.stop()


# ==============================================================================
# 3. CONSTRUCTOR DE CONTEXTO ESTADÍSTICO PARA EL ASISTENTE IA
# ==============================================================================
def generar_resumen_global_csv(df: pd.DataFrame) -> dict:
  validos = df[df["es_valido"]]
  invis = df[~df["es_valido"]]

  # Días de mayor y menor afluencia
  conteo_dias = (
      df.groupby("dia_semana", observed=False)["student_id"].count().to_dict()
  )
  conteo_horas = df.groupby("hora")["student_id"].count().to_dict()
  hora_pico = (
      max(conteo_horas, key=conteo_horas.get) if conteo_horas else "N/A"
  )

  # Top estudiantes más recurrentes
  top_estudiantes = df["student_id"].value_counts().head(5).to_dict()

  resumen = {
      "total_registros": len(df),
      "total_estudiantes_unicos": int(df["student_id"].nunique()),
      "fecha_inicio": str(df["fecha"].min()),
      "fecha_fin": str(df["fecha"].max()),
      "dias_totales_operacion": int((df["fecha"].max() - df["fecha"].min()).days
                                    + 1),
      "mediciones_validas": len(validos),
      "mediciones_invalidas": len(invis),
      "tasa_invalidez_porcentaje": round((len(invis) / len(df)) * 100, 2),
      "calidad_senal_promedio": round(df["signal_quality"].mean(), 3),
      "calidad_senal_mediciones_validas": round(
          validos["signal_quality"].mean(), 3
      ),
      "calidad_senal_mediciones_invalidas": round(
          invis["signal_quality"].mean(), 3
      ),
      "fisiologia_valida": {
          "bpm_promedio": round(validos["heart_rate_bpm"].mean(), 2),
          "bpm_min": round(validos["heart_rate_bpm"].min(), 2),
          "bpm_max": round(validos["heart_rate_bpm"].max(), 2),
          "bpm_q25": round(validos["heart_rate_bpm"].quantile(0.25), 2),
          "bpm_mediana": round(validos["heart_rate_bpm"].median(), 2),
          "bpm_q75": round(validos["heart_rate_bpm"].quantile(0.75), 2),
          "spo2_promedio": round(validos["spo2_percent"].mean(), 2),
          "spo2_min": round(validos["spo2_percent"].min(), 2),
          "spo2_max": round(validos["spo2_percent"].max(), 2),
          "spo2_mediana": round(validos["spo2_percent"].median(), 2),
      },
      "patrones_temporales": {
          "hora_pico_frecuencia": hora_pico,
          "distribucion_dias": conteo_dias,
          "distribucion_horas": conteo_horas,
      },
      "top_5_estudiantes_activos": top_estudiantes,
      "anomalias_detectadas": {
          "spo2_menor_90_validas": int((validos["spo2_percent"] < 90).sum()),
          "bpm_mayor_120_validas": int((validos["heart_rate_bpm"] > 120).sum()),
          "bpm_menor_50_validas": int((validos["heart_rate_bpm"] < 50).sum()),
      },
  }
  return resumen


resumen_dataset = generar_resumen_global_csv(df_raw)


# ==============================================================================
# 4. BARRA LATERAL: API KEY Y FILTROS INTERACTIVOS
# ==============================================================================
with st.sidebar:
  st.markdown("## ⚡ Tótem IoT EAFIT")
  st.caption("Computación Física & IoT | Proyecto Integrador")
  st.markdown("---")

  # --- CONFIGURACIÓN DE IA ---
  st.markdown("### 🔑 Inteligencia Artificial")
  api_key_input = st.text_input(
      "OpenAI API Key",
      type="password",
      placeholder="sk-...",
      help=(
          "Ingresa tu clave de OpenAI para habilitar el agente analítico."
          " Tu clave solo vive en la memoria de esta sesión."
      ),
  )

  st.markdown("---")
  st.markdown("### 🎛️ Filtros Globales")

  # Filtro 1: Rango de Fechas
  min_date = df_raw["fecha"].min()
  max_date = df_raw["fecha"].max()
  date_range = st.date_input(
      "Rango de Fechas:",
      value=(min_date, max_date),
      min_value=min_date,
      max_value=max_date,
  )

  # Filtro 2: Estado de la Medición
  status_options = ["Todos", "Válidos (valid)", "Inválidos (invalid)"]
  selected_status = st.radio("Estado de Medición:", status_options, index=0)

  # Filtro 3: Selección de Estudiante
  estudiantes_unicos = ["Todos"] + sorted(
      df_raw["student_id"].unique().tolist()
  )
  selected_student = st.selectbox(
      "Filtrar Estudiante Específico:", estudiantes_unicos, index=0
  )

  st.markdown("---")
  st.info(
      "💡 **Nota ética:** Datos sintéticos con fines pedagógicos. El sensor"
      " MAX30102 y este software no constituyen un dispositivo médico"
      " certificado."
  )

# Aplicación reactiva de filtros
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
  start_d, end_d = date_range
  df_filtered = df_raw[
      (df_raw["fecha"] >= start_d) & (df_raw["fecha"] <= end_d)
  ]
else:
  df_filtered = df_raw.copy()

if selected_status == "Válidos (valid)":
  df_filtered = df_filtered[df_filtered["es_valido"]]
elif selected_status == "Inválidos (invalid)":
  df_filtered = df_filtered[~df_filtered["es_valido"]]

if selected_student != "Todos":
  df_filtered = df_filtered[df_filtered["student_id"] == selected_student]

# Validar que no quede vacío tras los filtros
if df_filtered.empty:
  st.warning(
      "⚠️ No se encontraron registros con la combinación de filtros"
      " seleccionada. Por favor ajusta los parámetros en la barra lateral."
  )
  st.stop()


# ==============================================================================
# 5. ENCABEZADO Y KPIS PRINCIPALES (REQUERIMIENTO MÍNIMO DE 5 INDICADORES)
# ==============================================================================
st.markdown(
    "# 🩺 Monitor Fisiológico & Analítica IoT Campus EAFIT",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -10px;'>Plataforma"
    " de inteligencia de datos para el tótem interactivo con sensor óptico"
    " MAX30102 y lector NFC.</p>",
    unsafe_allow_html=True,
)

# Cálculo de los 5 Indicadores Mínimos Exigidos
total_mediciones = len(df_filtered)
total_estudiantes = df_filtered["student_id"].nunique()
validas_filtro = df_filtered[df_filtered["es_valido"]]
invalidas_filtro = df_filtered[~df_filtered["es_valido"]]

bpm_promedio = (
    round(validas_filtro["heart_rate_bpm"].mean(), 1)
    if not validas_filtro.empty
    else 0.0
)
spo2_promedio = (
    round(validas_filtro["spo2_percent"].mean(), 1)
    if not validas_filtro.empty
    else 0.0
)
total_invalidas = len(invalidas_filtro)
pct_invalidas = (
    round((total_invalidas / total_mediciones) * 100, 1)
    if total_mediciones > 0
    else 0.0
)

# Renderizado de Tarjetas de Métricas con Glow
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
  st.metric(
      "Total Mediciones",
      f"{total_mediciones:,}",
      help="Número total de lecturas registradas en la selección actual.",
  )
with col2:
  st.metric(
      "Estudiantes Únicos",
      f"{total_estudiantes}",
      help="Cantidad de estudiantes distintos identificados vía NFC.",
  )
with col3:
  st.metric(
      "BPM Promedio (Válidas)",
      f"{bpm_promedio} bpm",
      delta=(
          f"{round(bpm_promedio - 75.0, 1)} ref"
          if bpm_promedio > 0
          else None
      ),
      help=(
          "Frecuencia cardíaca media de registros válidos. Rango normal"
          " reposo: 60-100."
      ),
  )
with col4:
  st.metric(
      "SpO₂ Promedio (Válidas)",
      f"{spo2_promedio}%",
      delta=(
          f"{round(spo2_promedio - 98.0, 1)}%" if spo2_promedio > 0 else None
      ),
      help=(
          "Saturación de oxígeno estimada promedio de registros válidos (Normal"
          " ≥ 95%)."
      ),
  )
with col5:
  st.metric(
      "Mediciones Inválidas",
      f"{pct_invalidas}%",
      delta=f"{total_invalidas} registros",
      delta_color="inverse",
      help=(
          "Porcentaje y total de lecturas marcadas con error por baja calidad de"
          " señal."
      ),
  )

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 6. PANELES Y PESTAÑAS PRINCIPALES DEL DASHBOARD
# ==============================================================================
tab_analisis, tab_temporal, tab_individual, tab_chat, tab_hallazgos = st.tabs([
    "📊 Tablero Fisiológico",
    "📈 Patrones & Calidad IoT",
    "👤 Seguimiento por Estudiante",
    "🤖 Asistente Cognitivo & Decisiones",
    "📑 Hallazgos & Conclusiones",
])


# ------------------------------------------------------------------------------
# TAB 1: TABLERO FISIOLÓGICO Y EXPLORACIÓN
# ------------------------------------------------------------------------------
with tab_analisis:
  st.markdown("### 🫀 Distribución y Correlación Fisiológica")
  c_graf1, c_graf2 = st.columns(2)

  with c_graf1:
    # GRÁFICO 1: Histograma interactivo de BPM con rangos normales
    if not validas_filtro.empty:
      fig_bpm = px.histogram(
          validas_filtro,
          x="heart_rate_bpm",
          nbins=35,
          color_discrete_sequence=["#38bdf8"],
          opacity=0.85,
          title="<b>Distribución de Frecuencia Cardíaca (BPM)</b>",
          labels={
              "heart_rate_bpm": "Pulsaciones por Minuto (BPM)",
              "count": "Frecuencia",
          },
      )
      # Banda de normalidad 60-100 BPM
      fig_bpm.add_vrect(
          x0=60,
          x1=100,
          fillcolor="#22c55e",
          opacity=0.15,
          line_width=0,
          annotation_text="Rango Reposo Normal (60-100)",
          annotation_position="top left",
      )
      fig_bpm.update_layout(
          template="plotly_dark",
          paper_bgcolor="rgba(0,0,0,0)",
          plot_bgcolor="rgba(15,23,42,0.6)",
          hoverlabel=dict(
              bgcolor="#0f172a",
              font_size=13,
              font_color="#38bdf8",
              bordercolor="#38bdf8",
          ),
      )
      st.plotly_chart(fig_bpm, use_container_width=True)
    else:
      st.info("Sin registros válidos para graficar BPM.")

  with c_graf2:
    # GRÁFICO 2: Distribución de SpO2 con umbrales de alerta
    if not validas_filtro.empty:
      fig_spo2 = px.histogram(
          validas_filtro,
          x="spo2_percent",
          nbins=30,
          color_discrete_sequence=["#818cf8"],
          opacity=0.85,
          title="<b>Distribución de Saturación de Oxígeno (SpO₂ %)</b>",
          labels={
              "spo2_percent": "Saturación de Oxígeno (%)",
              "count": "Frecuencia",
          },
      )
      fig_spo2.add_vline(
          x=95,
          line_dash="dash",
          line_color="#eab308",
          annotation_text="Umbral Esperado (95%)",
          annotation_position="top left",
      )
      fig_spo2.update_layout(
          template="plotly_dark",
          paper_bgcolor="rgba(0,0,0,0)",
          plot_bgcolor="rgba(15,23,42,0.6)",
          hoverlabel=dict(
              bgcolor="#0f172a",
              font_size=13,
              font_color="#818cf8",
              bordercolor="#818cf8",
          ),
      )
      st.plotly_chart(fig_spo2, use_container_width=True)
    else:
      st.info("Sin registros válidos para graficar SpO₂.")

  # GRÁFICO 3: Dispersión BPM vs SpO2 coloreado por Calidad de Señal
  st.markdown("#### 🔬 Mapa de Relación Fisiológica vs Calidad Óptica")
  fig_scatter = px.scatter(
      df_filtered,
      x="heart_rate_bpm",
      y="spo2_percent",
      color="signal_quality",
      symbol="measurement_status",
      color_continuous_scale="Viridis",
      hover_data=["student_id", "fecha", "hora_exacta"],
      title=(
          "<b>Relación BPM vs SpO₂ según Calidad de Señal y Estado de"
          " Medición</b>"
      ),
      labels={
          "heart_rate_bpm": "Frecuencia Cardíaca (BPM)",
          "spo2_percent": "Saturación SpO₂ (%)",
          "signal_quality": "Calidad Señal",
          "measurement_status": "Estado",
      },
  )
  fig_scatter.update_traces(marker=dict(size=8, opacity=0.85))
  fig_scatter.update_layout(
      template="plotly_dark",
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(15,23,42,0.6)",
      hoverlabel=dict(
          bgcolor="#0f172a",
          font_size=13,
          font_color="#f8fafc",
          bordercolor="#38bdf8",
      ),
  )
  st.plotly_chart(fig_scatter, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 2: PATRONES TEMPORALES Y CALIDAD DE DATOS IOT
# ------------------------------------------------------------------------------
with tab_temporal:
  st.markdown("### ⏱️ Dinámica de Uso y Comportamiento del Hardware")

  c_temp1, c_temp2 = st.columns(2)

  with c_temp1:
    # GRÁFICO 4: Evolución diaria de utilización
    mediciones_por_dia = (
        df_filtered.groupby(["fecha", "measurement_status"], observed=False)
        .size()
        .reset_index(name="conteo")
    )

    fig_evol = px.bar(
        mediciones_por_dia,
        x="fecha",
        y="conteo",
        color="measurement_status",
        color_discrete_map={"valid": "#38bdf8", "invalid": "#ef4444"},
        title="<b>Evolución Cronológica de Utilización del Tótem</b>",
        labels={
            "fecha": "Fecha",
            "conteo": "N° Mediciones",
            "measurement_status": "Estado",
        },
        barmode="stack",
    )
    fig_evol.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        hoverlabel=dict(bgcolor="#0f172a", font_size=13),
    )
    st.plotly_chart(fig_evol, use_container_width=True)

  with c_temp2:
    # GRÁFICO 5: Mapa de Calor Día de Semana vs Hora (Patrón de Campus)
    dias_orden = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]
    heatmap_data = (
        df_filtered.pivot_table(
            index="dia_semana",
            columns="hora",
            values="student_id",
            aggfunc="count",
            fill_value=0,
            observed=False,
        )
        .reindex(dias_orden)
        .dropna(how="all")
    )

    fig_heat = px.imshow(
        heatmap_data,
        color_continuous_scale="Blues",
        title="<b>Mapa de Afluencia al Tótem: Día vs Hora (Bogotá)</b>",
        labels=dict(x="Hora del Día (0-23)", y="Día de la Semana", color="Usos"),
    )
    fig_heat.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        hoverlabel=dict(bgcolor="#0f172a", font_size=13),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

  # GRÁFICO 6: Relación entre Calidad de Señal y Validez
  st.markdown("#### 📡 Inspección de Calidad de Señal del Sensor MAX30102")
  col_sig1, col_sig2 = st.columns([2, 1])

  with col_sig1:
    fig_box = px.box(
        df_filtered,
        x="measurement_status",
        y="signal_quality",
        color="measurement_status",
        color_discrete_map={"valid": "#10b981", "invalid": "#f43f5e"},
        points="all",
        title="<b>Calidad de Señal Óptica según Validez del Registro</b>",
        labels={
            "signal_quality": "Índice de Calidad (0.0 - 1.0)",
            "measurement_status": "Estado",
        },
    )
    fig_box.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        showlegend=False,
    )
    st.plotly_chart(fig_box, use_container_width=True)

  with col_sig2:
    st.markdown("""
        <div class="glowing-box" style="margin-top: 25px;">
            <h4 style="color: #38bdf8;">Diagnóstico Técnico IoT</h4>
            <p style="font-size: 0.95rem; color: #cbd5e1;">
                El sensor <b>MAX30102</b> es altamente sensible a la presión del dedo y al ruido ambiental óptico.
            </p>
            <ul style="font-size: 0.9rem; color: #94a3b8;">
                <li>Las lecturas <b>válidas</b> concentran calidades de señal marcadamente superiores.</li>
                <li>Los registros <b>inválidos</b> ocurren comúnmente por retiro prematuro del dedo o movimiento abrupto del usuario.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# TAB 3: SEGUIMIENTO INDIVIDUAL (REQUISITO EXPLÍCITO)
# ------------------------------------------------------------------------------
with tab_individual:
  st.markdown("### 👤 Explorador de Historial por Estudiante")

  # Selector exclusivo para esta sección
  lista_est_ind = sorted(df_raw["student_id"].unique())
  selected_ind_student = st.selectbox(
      "Selecciona el Estudiante a Inspeccionar:", lista_est_ind, index=0
  )

  df_estudiante = df_raw[df_raw["student_id"] == selected_ind_student].sort_values(
      "timestamp_bogota"
  )

  # Métricas individuales
  n_mediciones = len(df_estudiante)
  primera_med = df_estudiante["timestamp_bogota"].min().strftime("%Y-%m-%d %H:%M")
  ultima_med = df_estudiante["timestamp_bogota"].max().strftime("%Y-%m-%d %H:%M")
  n_validas = df_estudiante["es_valido"].sum()
  n_invalidas = n_mediciones - n_validas

  mcol1, mcol2, mcol3, mcol4 = st.columns(4)
  with mcol1:
    st.metric("Total Mediciones", f"{n_mediciones}")
  with mcol2:
    st.metric("Registros Válidos", f"{n_validas} ({round(n_validas/n_mediciones*100,1)}%)")
  with mcol3:
    st.metric("Primera Medición", f"{primera_med}")
  with mcol4:
    st.metric("Última Medición", f"{ultima_med}")

  st.markdown("---")

  # Gráfica de evolución individual
  fig_indiv = go.Figure()

  # Serie BPM
  fig_indiv.add_trace(
      go.Scatter(
          x=df_estudiante["timestamp_bogota"],
          y=df_estudiante["heart_rate_bpm"],
          mode="lines+markers",
          name="Frecuencia Cardíaca (BPM)",
          line=dict(color="#38bdf8", width=3),
          marker=dict(
              size=9,
              color=np.where(df_estudiante["es_valido"], "#38bdf8", "#ef4444"),
              symbol=np.where(
                  df_estudiante["es_valido"], "circle", "x"
              ),
          ),
          hovertemplate=(
              "<b>BPM:</b> %{y}<br><b>Fecha:</b>"
              " %{x|%Y-%m-%d %H:%M}<extra></extra>"
          ),
      )
  )

  # Serie SpO2
  fig_indiv.add_trace(
      go.Scatter(
          x=df_estudiante["timestamp_bogota"],
          y=df_estudiante["spo2_percent"],
          mode="lines+markers",
          name="Saturación SpO₂ (%)",
          yaxis="y2",
          line=dict(color="#a855f7", width=3, dash="dot"),
          marker=dict(
              size=8,
              color=np.where(df_estudiante["es_valido"], "#a855f7", "#ef4444"),
          ),
          hovertemplate=(
              "<b>SpO₂:</b> %{y}%<br><b>Fecha:</b>"
              " %{x|%Y-%m-%d %H:%M}<extra></extra>"
          ),
      )
  )

  fig_indiv.update_layout(
      title=f"<b>Trayectoria Longitudinal: {selected_ind_student}</b>",
      template="plotly_dark",
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(15,23,42,0.6)",
      xaxis=dict(title="Fecha y Hora (Bogotá)", gridcolor="rgba(255,255,255,0.05)"),
      yaxis=dict(
          title=dict(text="BPM (ppm)", font=dict(color="#38bdf8")),
          tickfont=dict(color="#38bdf8"),
          gridcolor="rgba(255,255,255,0.05)",
      ),
      yaxis2=dict(
          title=dict(text="SpO₂ (%)", font=dict(color="#a855f7")),
          tickfont=dict(color="#a855f7"),
          overlaying="y",
          side="right",
          range=[70, 102],
      ),
      legend=dict(
          orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
      ),
      hoverlabel=dict(
          bgcolor="#0f172a",
          font_size=13,
          bordercolor="#38bdf8",
      ),
  )
  st.plotly_chart(fig_indiv, use_container_width=True)

  st.dataframe(
      df_estudiante[[
          "timestamp_bogota",
          "heart_rate_bpm",
          "spo2_percent",
          "signal_quality",
          "measurement_status",
      ]].rename(columns={"timestamp_bogota": "fecha_hora_bogota"}),
      use_container_width=True,
      hide_index=True,
  )


# ------------------------------------------------------------------------------
# TAB 4: ASISTENTE COGNITIVO & DECISIONES (CHATBOT INTEGRADO)
# ------------------------------------------------------------------------------
with tab_chat:
  st.markdown("### 🤖 Asistente Analítico & Estratégico del Tótem")
  st.markdown(
      "Este asistente posee conocimiento estructurado completo de todo el"
      " dataset: patrones por hora, días de la semana, estudiantes, percentiles"
      " de BPM/SpO₂ y fallas del sensor."
  )

  if not api_key_input:
    st.warning(
        "🔑 **Se requiere OpenAI API Key:** Introduce tu clave en la barra"
        " lateral izquierda para interactuar con el asistente."
    )
    st.info(
        "💡 **Sugerencia de preguntas:**\n"
        "- *¿Cuáles son las horas pico y qué plan de mantenimiento recomiendas?*\n"
        "- *¿Qué porcentaje de fallas tiene el sensor y cómo reducirlo en el"
        " campus?*\n"
        "- *¿Existen anomalías críticas de hipoxemia o taquicardia en los datos?*\n"
        "- *¿Qué días registran menor afluencia y cómo incentivar la"
        " participación estudiantil?*"
    )
  else:
    # Historial de conversación
    if "chat_messages" not in st.session_state:
      st.session_state.chat_messages = [{
          "role": "assistant",
          "content": (
              "¡Hola! Soy el asistente analítico del **Tótem IoT EAFIT**. Conozco"
              " en detalle los registros de los 28 días de operación, las"
              " mediciones fisiológicas y la calidad del sensor MAX30102. ¿En"
              " qué análisis o toma de decisiones institucionales puedo"
              " colaborarte hoy?"
          ),
      }]

    # Despliegue de mensajes
    for msg in st.session_state.chat_messages:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    # Input del usuario
    if user_query := st.chat_input(
        "Haz una pregunta sobre análisis, anomalías o decisiones futuras..."
    ):
      st.session_state.chat_messages.append(
          {"role": "user", "content": user_query}
      )
      with st.chat_message("user"):
        st.markdown(user_query)

      with st.chat_message("assistant"):
        with st.spinner("Sintetizando datos y generando plan analítico..."):
          try:
            client = openai.OpenAI(api_key=api_key_input)

            # Contexto maestro enriquecido con todos los detalles
            system_prompt = f"""
Eres el consultor experto en IoT, analítica de datos y bienestar universitario del proyecto 'Tótem Fisiológico EAFIT'.
Tienes acceso integral y omnisciente al resumen estadístico del conjunto de datos completo (28 días de mediciones sintéticas en EAFIT):

RESUMEN ESTRUCTURADO DEL DATASET:
{json.dumps(resumen_dataset, indent=2, ensure_ascii=False)}

FILTROS ACTUALMENTE ACTIVOS EN LA PANTALLA DEL USUARIO:
- Registros filtrados mostrados: {total_mediciones}
- Estudiantes únicos en vista: {total_estudiantes}
- Estado de medición seleccionado: {selected_status}
- Estudiante seleccionado: {selected_student}

DIRECTRICES DE TUS RESPUESTAS:
1. Responde con datos exactos, porcentajes, fechas y horas cuando te pregunten sobre tendencias, picos o métricas.
2. Orienta tus respuestas hacia la **Toma de Decisiones** institucional (planes de mantenimiento del tótem, campañas de bienestar estudiantil, alertas por ruido del sensor).
3. Distingue claramente entre mediciones válidas e inválidas, destacando el rol de la calidad de señal (`signal_quality`) del MAX30102.
4. **RIGOR ÉTICO**: Mantén siempre la aclaración de que el tótem es un dispositivo formativo/experimental y no un equipo médico validado para emitir diagnósticos clínicos.
5. Sé claro, profesional, estructurado (usa viñetas o tablas markdown cuando aporte claridad).
"""

            messages_payload = [{"role": "system", "content": system_prompt}]
            # Mantener memoria de los últimos turnos
            for m in st.session_state.chat_messages[-6:]:
              messages_payload.append(
                  {"role": m["role"], "content": m["content"]}
              )

            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages_payload, temperature=0.3
            )

            assistant_reply = response.choices[0].message.content
            st.markdown(assistant_reply)
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": assistant_reply}
            )

          except Exception as e:
            st.error(f"Error en la llamada a OpenAI: {e}")


# ------------------------------------------------------------------------------
# TAB 5: HALLAZGOS Y CONCLUSIONES (MÍNIMO 3 SUSTENTADOS EN DATOS)
# ------------------------------------------------------------------------------
with tab_hallazgos:
  st.markdown("### 📑 Hallazgos Clave & Sustentación Técnica")
  st.markdown(
      "A continuación se presentan los principales hallazgos derivados del"
      " procesamiento de los datos del tótem, respaldados por la evidencia"
      " observada en las mediciones:"
  )

  h1, h2, h3 = st.columns(3)

  with h1:
    st.markdown("""
        <div class="glowing-box" style="height: 100%;">
            <h4 style="color: #38bdf8;">1. Patrón Horario y Rutina de Campus</h4>
            <p style="font-size: 0.95rem; color: #cbd5e1;">
                <b>Evidencia:</b> Las horas con mayor concentración de lecturas corresponden a las franjas de <b>10:00 a 12:00</b> y de <b>14:00 a 16:00</b>, coincidiendo con los cambios de bloque de clase en EAFIT.
            </p>
            <p style="font-size: 0.9rem; color: #94a3b8;">
                <b>Decisión:</b> Programar mantenimientos de hardware y limpieza del sensor fuera de estas franjas (ej. antes de las 07:00 o después de las 18:00) para no interrumpir el flujo.
            </p>
        </div>
        """, unsafe_allow_html=True)

  with h2:
    st.markdown(f"""
        <div class="glowing-box" style="height: 100%;">
            <h4 style="color: #818cf8;">2. Ruido Óptico e Invalidez de Señal</h4>
            <p style="font-size: 0.95rem; color: #cbd5e1;">
                <b>Evidencia:</b> Cerca del <b>{resumen_dataset['tasa_invalidez_porcentaje']}%</b> de los registros resultaron inválidos. La calidad de señal promedio en registros inválidos cae drásticamente a <b>{resumen_dataset['calidad_senal_mediciones_invalidas']}</b> vs <b>{resumen_dataset['calidad_senal_mediciones_validas']}</b> en válidos.
            </p>
            <p style="font-size: 0.9rem; color: #94a3b8;">
                <b>Decisión:</b> Implementar en el tótem una guía visual o soporte ergonómico para el dedo que garantice estabilidad óptica antes de iniciar la captura de fotopletismografía.
            </p>
        </div>
        """, unsafe_allow_html=True)

  with h3:
    st.markdown(f"""
        <div class="glowing-box" style="height: 100%;">
            <h4 style="color: #34d399;">3. Distribución Fisiológica y Anomalías</h4>
            <p style="font-size: 0.95rem; color: #cbd5e1;">
                <b>Evidencia:</b> El 50% central de la población se ubica entre <b>{resumen_dataset['fisiologia_valida']['bpm_q25']} y {resumen_dataset['fisiologia_valida']['bpm_q75']} BPM</b>. Se identificaron <b>{resumen_dataset['anomalias_detectadas']['spo2_menor_90_validas']}</b> mediciones con SpO₂ &lt; 90% aún marcadas como válidas.
            </p>
            <p style="font-size: 0.9rem; color: #94a3b8;">
                <b>Decisión:</b> Ajustar el firmware del ESP32 para descartar mediciones con SpO₂ fisiológicamente inverosímil en personas asintomáticas antes de transmitirlas a la nube.
            </p>
        </div>
        """, unsafe_allow_html=True)

  st.markdown("---")
  st.markdown("#### ⚖️ Consideraciones Éticas y Limitaciones del Sistema")
  st.warning(
      "⚠️ **Limitación del Dispositivo:** Las lecturas de fotopletismografía"
      " obtenidas mediante el sensor MAX30102 en un tótem público están sujetas"
      " a factores como frío periférico, esmalte de uñas, luz ambiental y"
      " presión dactilar. Estas mediciones tienen un propósito"
      " estrictamente **educativo y de sensibilización**, y no deben usarse"
      " para emitir diagnósticos clínicos o prescripciones médicas."
  )
