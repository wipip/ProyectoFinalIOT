import openai
import streamlit as st

st.set_page_config(
    page_title="Asistente Tótem EAFIT", page_icon="🩺", layout="wide"
)

st.title("🩺 Asistente Inteligente del Tótem EAFIT")

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
          # Instanciar el cliente de OpenAI con la key ingresada en tiempo de ejecución
          client = openai.OpenAI(api_key=user_api_key)

          response = client.chat.completions.create(
              model="gpt-4o-mini",
              messages=[
                  {
                      "role": "system",
                      "content": (
                          "Eres un asistente analítico del tótem IoT de salud"
                          " de la Universidad EAFIT. Ayudas a interpretar datos"
                          " estadísticos de BPM y SpO2 de forma educativa y sin"
                          " emitir diagnósticos médicos."
                      ),
                  },
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
