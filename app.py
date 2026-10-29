import openai
import streamlit as st

st.title("🩺 Asistente Inteligente del Tótem EAFIT")

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

  # Respuesta del asistente (Aquí conectas con la API de OpenAI)
  with st.chat_message("assistant"):
    with st.spinner("Analizando datos del tótem..."):
      # Opcional: Puedes extraer métricas clave del DataFrame filtrado (ej. promedio de BPM)
      # y pasárselas al prompt del sistema para que la IA responda con base real.

      client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

      response = client.chat.completions.create(
          model="gpt-4o-mini",  # O el modelo de tu preferencia
          messages=[
              {
                  "role": "system",
                  "content": (
                      "Eres un asistente analítico del tótem IoT de salud de"
                      " la Universidad EAFIT. Ayudas a interpretar datos"
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
