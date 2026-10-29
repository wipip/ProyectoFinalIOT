import openai
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Asistente Tótem EAFIT", page_icon="🩺", layout="wide"
)

st.title("🩺 Asistente Inteligente del Tótem EAFIT")


# --- CARGAR Y RESUMIR EL CSV DESDE GITHUB (CAMBIO MÍNIMO) ---
@st.cache_data
def cargar_datos_csv():
  # Lee el archivo CSV que está en la misma raíz del repositorio en GitHub
  df = pd.read_csv("proyecto_integrador_eafit_max30102.csv")
  return df


try:
  df_datos = cargar_datos_csv()

  # Crear un resumen estadístico rápido para que la IA lo entienda
  total_meds = len(df_datos)
  total_estudiantes = df_datos["student_id"].nunique()
  validas = df_datos[df_datos["measurement_status"] == "valid"]
  bpm_prom = round(validas["heart_rate_bpm"].mean(), 1)
  spo2_prom = round(validas["spo2_percent"].mean(), 1)

  resumen_contexto = (
      f"Resumen de datos del tótem EAFIT: Total de registros: {total_meds},"
      f" Estudiantes únicos: {total_estudiantes}, Frecuencia cardíaca promedio"
      f" (válida): {bpm_prom} BPM, SpO2 promedio (válida): {spo2_prom}%."
  )
except Exception as e:
  resumen_contexto = "No se pudo cargar el archivo CSV de datos."

# --- BARRA LATERAL PARA LA CONFIGURACIÓN DE LA API KEY ---
st.sidebar.header("🔑 Configuración")
user_api_key = st.sidebar.text_input(
    "Introduce tu OpenAI API Key",
    type="password",
    help="Tu clave no se almacena permanentemente; solo se usa durante tu sesión activa.",
)

# Validar si el usuario ingresó la clave
if not user_api_key:
  st.warning(
      "⚠️ Por favor, introduce tu OpenAI API Key en la barra lateral para"
      " habilitar el chat con el asistente."
  )
else:
  # Inicializar el historial del chat en la sesión de Streamlit
  if "messages" not in st.session_state:
    st.session_state.messages = []

  # Mostrar mensajes anteriores del historial al recargar
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  # Espacio evidente para escribir la duda del usuario
  if prompt := st.chat_input(
      "Pregúntale al asistente sobre los datos, ritmos cardíacos o"
      " tendencias..."
  ):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.markdown(prompt)

    # Respuesta del asistente conectando con la API usando la key del usuario
    with st.chat_message("assistant"):
      with st.spinner("Analizando datos del tótem..."):
        try:
          client = openai.OpenAI(api_key=user_api_key)

          # Prompt del sistema que incluye los datos reales del CSV de GitHub
          system_prompt = (
              "Eres un asistente analítico del tótem IoT de salud de la"
              " Universidad EAFIT. Utiliza la siguiente información real"
              " derivada del archivo CSV del proyecto para responder las dudas"
              f" del estudiante: {resumen_contexto}. Ayudas a interpretar datos"
              " estadísticos de BPM y SpO2 de forma educativa y sin emitir"
              " diagnósticos médicos."
          )

          response = client.chat.completions.create(
              model="gpt-4o-mini",
              messages=[
                  {"role": "system", "content": system_prompt},
                  {"role": "user", "content": prompt},
              ],
          )

          bot_response = response.choices[0].message.content
          st.markdown(bot_response)
          st.session_state.messages.append(
              {"role": "assistant", "content": bot_response}
          )

        except Exception as e:
          st.error(
              "Ocurrió un error al conectar con OpenAI. Verifica que tu API"
              f" Key sea correcta. Detalle: {e}"
          )
