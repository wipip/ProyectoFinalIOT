
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import requests

from influxdb_client import InfluxDBClient
from streamlit_lottie import st_lottie
from streamlit_autorefresh import st_autorefresh


# =========================================================
# CONFIGURACION INFLUXDB
# =========================================================
URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "5FESPQw5t4qA4GgZmyeZ9mu7u1sbtauo4Hh8tjRi1E8sdrIgzXAX5ESk4n5MmcpAjJWEGgEKklFX0LNasnUmng=="
ORG = "miguelcmo"
BUCKET = "iot_telemetry_data"

COLD_URL = (
    "https://raw.githubusercontent.com/wipip/"
    "iotDASHBOARDjuanS/main/Cold.json"
)

SUMMER_URL = (
    "https://raw.githubusercontent.com/wipip/"
    "iotDASHBOARDjuanS/main/Summer.%20Sale%20Animation.json"
)


# =========================================================
# CONFIGURACION STREAMLIT
# =========================================================
st.set_page_config(
    page_title="IoT Climate Dashboard",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# ESTILOS CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --accent: #36d9ff;
    --panel: rgba(12, 22, 40, 0.88);
    --border: rgba(83, 190, 255, 0.25);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 15% 10%,
            rgba(0, 125, 255, .12), transparent 40%),
        radial-gradient(ellipse at 85% 85%,
            rgba(255, 40, 75, .09), transparent 40%),
        #070b14;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1600px;
}

h1, h2, h3 {
    color: #f1f7ff;
    letter-spacing: -0.7px;
}

p, label {
    color: #b6c6dc;
}

[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px 20px;
    transition: border-color .25s ease,
                box-shadow .25s ease,
                transform .25s ease;
    backdrop-filter: blur(12px);
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    border-color: var(--accent);
    box-shadow: 0 0 18px rgba(54,217,255,.22),
                0 0 35px rgba(54,217,255,.09);
}

[data-testid="stMetricLabel"] {
    color: #a7bbd5;
}

[data-testid="stMetricValue"] {
    color: #f3f8ff;
    font-weight: 800;
}

.stButton > button,
.stDownloadButton > button {
    border: 1px solid rgba(54,217,255,.45);
    border-radius: 12px;
    background: rgba(15,34,56,.9);
    color: #eafaff;
    transition: all .25s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #36d9ff;
    color: white;
    box-shadow: 0 0 12px rgba(54,217,255,.45),
                0 0 28px rgba(54,217,255,.2);
    transform: translateY(-2px);
}

[data-testid="stSidebar"] {
    background: rgba(8,15,29,.96);
    border-right: 1px solid rgba(83,190,255,.15);
}

[data-testid="stPlotlyChart"] {
    border-radius: 16px;
    overflow: hidden;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 12px;
}

.hero {
    padding: 12px 0 20px;
}

.hero p {
    color: #91a7c4;
}

.status-pill {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    background: rgba(54,217,255,.10);
    color: #65e5ff;
    border: 1px solid rgba(54,217,255,.30);
}

.animation-panel {
    background: rgba(12,22,40,.88);
    border: 1px solid rgba(83,190,255,.22);
    border-radius: 18px;
    padding: 12px;
    text-align: center;
    transition: all .3s ease;
}

.animation-panel:hover {
    border-color: var(--accent);
    box-shadow: 0 0 24px rgba(54,217,255,.20);
}

div[data-testid="stExpander"] {
    border-color: var(--border);
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# CARGAR ANIMACIONES LOTTIE
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_lottie(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


# =========================================================
# CONSULTAR INFLUXDB
# =========================================================
@st.cache_data(ttl=10, show_spinner=False)
def load_data(time_range):

    query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: {time_range})
      |> filter(fn: (r) =>
          r["_field"] == "temperature" or
          r["_field"] == "humidity")
      |> pivot(
          rowKey: ["_time"],
          columnKey: ["_field"],
          valueColumn: "_value"
      )
      |> keep(columns: ["_time", "temperature", "humidity"])
      |> sort(columns: ["_time"])
    '''

    with InfluxDBClient(
        url=URL,
        token=TOKEN,
        org=ORG,
        timeout=20000,
    ) as client:
        result = client.query_api().query_data_frame(query)

    if isinstance(result, list):
        frames = [frame for frame in result if not frame.empty]

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
    else:
        df = result

    if df.empty or "_time" not in df.columns:
        return pd.DataFrame()

    df["_time"] = pd.to_datetime(df["_time"], utc=True)

    for column in ["temperature", "humidity"]:
        if column not in df.columns:
            df[column] = float("nan")

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = (
        df.dropna(subset=["_time"])
        .sort_values("_time")
        .drop_duplicates(subset=["_time"], keep="last")
    )

    return df


# =========================================================
# FONDO DE PARTICULAS INTERACTIVAS
# =========================================================
def render_particles(temperature):

    # 15 °C = azul, 40 °C = rojo
    normalized = max(
        0.0,
        min(1.0, (temperature - 15.0) / 25.0),
    )

    components.html(
        f"""
        <script>
        const root = window.parent;
        const doc = root.document;

        const oldCanvas = doc.getElementById(
            "iot-particle-background"
        );

        if (oldCanvas) oldCanvas.remove();

        const canvas = doc.createElement("canvas");
        canvas.id = "iot-particle-background";

        Object.assign(canvas.style, {{
            position: "fixed",
            inset: "0",
            width: "100%",
            height: "100%",
            zIndex: "0",
            pointerEvents: "none",
            opacity: "0.68"
        }});

        doc.body.prepend(canvas);

        const ctx = canvas.getContext("2d");
        const intensity = {normalized};

        let width, height, particles = [];

        const mouse = {{
            x: -1000,
            y: -1000
        }};

        function resize() {{
            const dpr = Math.min(root.devicePixelRatio || 1, 2);

            width = root.innerWidth;
            height = root.innerHeight;

            canvas.width = width * dpr;
            canvas.height = height * dpr;

            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }}

        function color(t) {{
            const cold = [40, 170, 255];
            const hot = [255, 45, 75];

            const rgb = cold.map((v, i) =>
                Math.round(v + (hot[i] - v) * t)
            );

            return `rgb(${{rgb.join(",")}})`;
        }}

        function makeParticle() {{
            return {{
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                r: 1 + Math.random() * 1.8
            }};
        }}

        function init() {{
            resize();

            const count = Math.min(
                100,
                Math.floor(width / 14)
            );

            particles = Array.from(
                {{ length: count }},
                makeParticle
            );
        }}

        root.addEventListener("resize", resize);

        root.addEventListener("pointermove", e => {{
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        }});

        function animate() {{
            ctx.clearRect(0, 0, width, height);

            particles.forEach((p, i) => {{
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                const dist = Math.sqrt(dx*dx + dy*dy);

                if (dist < 140 && dist > 0) {{
                    p.vx -= dx / dist * 0.018;
                    p.vy -= dy / dist * 0.018;
                }}

                p.vx *= 0.995;
                p.vy *= 0.995;

                p.x += p.vx;
                p.y += p.vy;

                if (p.x < 0 || p.x > width) p.vx *= -1;
                if (p.y < 0 || p.y > height) p.vy *= -1;

                const c = color(intensity);

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = c;
                ctx.shadowColor = c;
                ctx.shadowBlur = 12;
                ctx.fill();
                ctx.shadowBlur = 0;

                for (let j = i + 1; j < particles.length; j++) {{
                    const q = particles[j];
                    const ddx = q.x - p.x;
                    const ddy = q.y - p.y;
                    const d = Math.sqrt(ddx*ddx + ddy*ddy);

                    if (d < 95) {{
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(q.x, q.y);
                        ctx.strokeStyle =
                            `rgba(120,190,255,${{0.16*(1-d/95)}})`;
                        ctx.lineWidth = 0.7;
                        ctx.stroke();
                    }}
                }}
            }});

            root.requestAnimationFrame(animate);
        }}

        init();
        animate();
        </script>
        """,
        height=0,
        scrolling=False,
    )


# =========================================================
# BARRA LATERAL
# =========================================================
st.sidebar.markdown("## ⚙️ Configuración")

time_range = st.sidebar.selectbox(
    "Rango de tiempo",
    ["-1h", "-6h", "-12h", "-24h", "-7d"],
    index=3,
)

refresh = st.sidebar.slider(
    "Auto-refresh (segundos)",
    min_value=0,
    max_value=60,
    value=10,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌡️ Umbrales")
st.sidebar.markdown("🔵 Frío: menos de 25 °C")
st.sidebar.markdown("🟣 Neutral: 25–30 °C")
st.sidebar.markdown("🔴 Calor: más de 30 °C")

if refresh > 0:
    st_autorefresh(
        interval=refresh * 1000,
        key="iot_dashboard_refresh",
    )


# =========================================================
# CABECERA
# =========================================================
st.markdown("""
<div class="hero">
    <span class="status-pill">● LIVE MONITORING</span>
    <h1>Climate Intelligence</h1>
    <p>Monitorización ambiental · IoT Telemetry · Celsius</p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# CARGAR DATOS
# =========================================================
try:
    df = load_data(time_range)
except Exception:
    st.error(
        "No se pudieron cargar los datos de InfluxDB. "
        "Verifica URL, token, organización y bucket."
    )
    st.stop()

if df.empty:
    st.warning(
        "No hay datos disponibles en el rango seleccionado."
    )
    st.stop()

valid_temp = df.dropna(subset=["temperature"])
valid_humidity = df.dropna(subset=["humidity"])

if valid_temp.empty:
    st.warning("No hay mediciones válidas de temperatura.")
    st.stop()

current_temp = float(valid_temp["temperature"].iloc[-1])

current_humidity = (
    float(valid_humidity["humidity"].iloc[-1])
    if not valid_humidity.empty
    else float("nan")
)

avg_temp = float(valid_temp["temperature"].mean())

avg_humidity = (
    float(valid_humidity["humidity"].mean())
    if not valid_humidity.empty
    else float("nan")
)


# =========================================================
# ESTADO CLIMATICO Y COLOR
# =========================================================
if current_temp < 25:
    accent = "#36d9ff"
    climate = "COLD"
    climate_message = "Ambiente frío"

elif current_temp > 30:
    accent = "#ff496c"
    climate = "SUMMER"
    climate_message = "Ambiente cálido"

else:
    accent = "#b58cff"
    climate = "NEUTRAL"
    climate_message = "Ambiente templado"

st.markdown(
    f"""
    <style>
    :root {{
        --accent: {accent};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FONDO ANIMADO
# =========================================================
render_particles(current_temp)


# =========================================================
# METRICAS Y ANIMACIONES
# =========================================================
data_col, animation_col = st.columns(
    [2.3, 1],
    gap="large",
)

with data_col:
    st.subheader("📡 Datos ambientales")

    c1, c2 = st.columns(2)

    c1.metric(
        "🌡️ Temperatura actual",
        f"{current_temp:.2f} °C",
    )

    c2.metric(
        "💧 Humedad actual",
        f"{current_humidity:.2f} %"
        if pd.notna(current_humidity)
        else "Sin datos",
    )

    c3, c4 = st.columns(2)

    c3.metric(
        "📊 Temperatura promedio",
        f"{avg_temp:.2f} °C",
    )

    c4.metric(
        "📊 Humedad promedio",
        f"{avg_humidity:.2f} %"
        if pd.notna(avg_humidity)
        else "Sin datos",
    )

    st.markdown(
        f"""
        <span class="status-pill">
            {climate} · {climate_message} · {current_temp:.1f} °C
        </span>
        """,
        unsafe_allow_html=True,
    )


with animation_col:
    st.subheader("🌤️ Estado climático")

    try:
        if current_temp < 25:
            animation = load_lottie(COLD_URL)

            st.markdown(
                """
                <div class="animation-panel">
                    <h3 style="color:#36d9ff">❄️ COLD MODE</h3>
                """,
                unsafe_allow_html=True,
            )

            st_lottie(
                animation,
                height=230,
                key="cold_animation",
                speed=1,
                loop=True,
            )

            st.markdown(
                """
                    <p style="color:#91cfff">
                        Temperatura inferior a 25 °C
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif current_temp > 30:
            animation = load_lottie(SUMMER_URL)

            st.markdown(
                """
                <div class="animation-panel">
                    <h3 style="color:#ff647e">☀️ SUMMER MODE</h3>
                """,
                unsafe_allow_html=True,
            )

            st_lottie(
                animation,
                height=230,
                key="summer_animation",
                speed=1,
                loop=True,
            )

            st.markdown(
                """
                    <p style="color:#ff9eac">
                        Temperatura superior a 30 °C
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                """
                <div class="animation-panel">
                    <h3 style="color:#b58cff">🌤️ COMFORT MODE</h3>
                    <p style="font-size:48px;color:#b58cff">◈</p>
                    <p>Temperatura entre 25 y 30 °C</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except Exception:
        st.warning(
            "No se pudo cargar la animación. "
            "Comprueba que el JSON sea accesible."
        )


# =========================================================
# GRAFICA PRINCIPAL CON GLOW
# =========================================================
st.markdown("---")
st.subheader("📈 Evolución de temperatura y humedad")

fig = go.Figure()

# Resplandor de temperatura
fig.add_trace(go.Scatter(
    x=valid_temp["_time"],
    y=valid_temp["temperature"],
    mode="lines",
    line=dict(color="rgba(54,217,255,0.12)", width=12),
    hoverinfo="skip",
    showlegend=False,
))

# Temperatura
fig.add_trace(go.Scatter(
    x=valid_temp["_time"],
    y=valid_temp["temperature"],
    mode="lines",
    name="Temperatura (°C)",
    line=dict(color="#36d9ff", width=2.5),
    yaxis="y",
    hovertemplate="%{y:.2f} °C<extra>Temperatura</extra>",
))

# Resplandor de humedad
fig.add_trace(go.Scatter(
    x=valid_humidity["_time"],
    y=valid_humidity["humidity"],
    mode="lines",
    line=dict(color="rgba(255,73,108,0.12)", width=12),
    hoverinfo="skip",
    showlegend=False,
    yaxis="y2",
))

# Humedad
fig.add_trace(go.Scatter(
    x=valid_humidity["_time"],
    y=valid_humidity["humidity"],
    mode="lines",
    name="Humedad (%)",
    line=dict(color="#ff496c", width=2.5),
    yaxis="y2",
    hovertemplate="%{y:.2f} %<extra>Humedad</extra>",
))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(8,15,29,0.65)",
    font=dict(color="#d8e6f7", family="Inter"),
    height=430,
    margin=dict(l=15, r=15, t=30, b=15),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),
    xaxis=dict(
        title="Tiempo",
        showgrid=True,
        gridcolor="rgba(120,160,200,0.10)",
        zeroline=False,
    ),
    yaxis=dict(
        title="Temperatura (°C)",
        side="left",
        showgrid=True,
        gridcolor="rgba(120,160,200,0.10)",
        zeroline=False,
    ),
    yaxis2=dict(
        title="Humedad (%)",
        overlaying="y",
        side="right",
        showgrid=False,
        zeroline=False,
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "displaylogo": False,
    },
)


# =========================================================
# PROMEDIOS CADA 10 MINUTOS
# =========================================================
st.subheader("⏱️ Promedios cada 10 minutos")

df_resampled = (
    df.set_index("_time")[["temperature", "humidity"]]
    .resample("10min")
    .mean()
    .dropna(how="all")
    .reset_index()
)

if not df_resampled.empty:
    fig2 = go.Figure()

    for column, color, label, unit in [
        ("temperature", "#36d9ff", "Temperatura", "°C"),
        ("humidity", "#ff496c", "Humedad", "%"),
    ]:
        series = df_resampled.dropna(subset=[column])

        # Capa de brillo
        fig2.add_trace(go.Scatter(
            x=series["_time"],
            y=series[column],
            mode="lines",
            line=dict(color=color, width=10),
            opacity=0.13,
            hoverinfo="skip",
            showlegend=False,
        ))

        # Línea principal
        fig2.add_trace(go.Scatter(
            x=series["_time"],
            y=series[column],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                f"%{{y:.2f}} {unit}<extra>{label}</extra>"
            ),
        ))

    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,15,29,0.65)",
        font=dict(color="#d8e6f7", family="Inter"),
        height=350,
        hovermode="x unified",
        margin=dict(l=15, r=15, t=25, b=15),
        xaxis_title="Tiempo",
        yaxis_title="Promedio",
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        config={"displaylogo": False},
    )


# =========================================================
# DATOS CRUDOS Y DESCARGA
# =========================================================
with st.expander("📋 Consultar datos crudos"):
    st.dataframe(
        df.sort_values("_time", ascending=False).head(50),
        use_container_width=True,
        hide_index=True,
    )

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Descargar CSV",
        data=csv,
        file_name="iot_telemetry.csv",
        mime="text/csv",
    )


# =========================================================
# PIE DE PAGINA
# =========================================================
st.markdown("---")

st.caption(
    f"Climate Intelligence · Actualización: "
    f"{refresh} s · Rango: {time_range} · "
    f"Temperatura: °C"
)
