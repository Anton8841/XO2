import os
import io
import certifi
import httpx
import streamlit as st
from PIL import Image

# Фікс SSL та HTTP-клієнта для google-genai v3.0+ у контейнерах Codespaces
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["GOOGLE_GENAI_HTTP_CLIENT"] = "httpx"

from google import genai
from google.genai import types

st.set_page_config(page_title="Cloud AI Document Analyzer", page_icon="☁️")
st.title("☁️ AI-Аналізатор документів та зображень (PoC)")
st.write("Хмарний сервіс на базі GitHub Codespaces та Google GenAI SDK")

# Бічна панель
api_key = st.sidebar.text_input("Введіть Gemini API Key (AQ...):", type="password").strip()
model_name = st.sidebar.selectbox(
    "Оберіть модель:",
    [
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-4-hydrogen",
        "gemini-4-argon"
    ]
)

uploaded_file = st.file_uploader("Завантажте зображення:", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Завантажене зображення", use_container_width=True)

prompt = st.text_input(
    "Що потрібно зробити з документом?",
)

if st.button("Проаналізувати в хмарі"):
    if not api_key:
        st.error("⚠️ Будь ласка, введіть API ключ у бічній панелі!")
    elif not uploaded_file:
        st.warning("⚠️ Будь ласка, завантажте зображення!")
    else:
        status = st.empty()
        try:
            status.info("⏳ 1/2 Підготовка зображення...")
            image = Image.open(uploaded_file)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.thumbnail((1600, 1600))
            
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=85)
            image_bytes = buf.getvalue()

            status.info(f"⏳ 2/2 Звернення до Google Gemini API ({model_name})...")

            # Створюємо HTTP-клієнт з примусовим IPv4 (local_address="0.0.0.0") та таймаутом 30с
            custom_httpx_client = httpx.Client(
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
                timeout=30.0
            )

            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    api_version="v1beta",
                    httpx_client=custom_httpx_client
                )
            )

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt
                ]
            )

            status.success("✅ Аналіз успішно завершено!")
            st.subheader("Результат:")
            st.write(response.text)

        except Exception as e:
            status.empty()
            st.error(f"❌ Помилка під час звернення до API: {e}")