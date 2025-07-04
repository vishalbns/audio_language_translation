import streamlit as st
import requests
import uuid
from st_audiorec import st_audiorec

BACKEND_URL = "http://localhost:8000"
SEND_AUDIO_ENDPOINT = f"{BACKEND_URL}/send-audio/"
GET_PREV_ENDPOINT = f"{BACKEND_URL}/get-translations/"

st.title("🎤 Language Transcription and Translation MVP")

st.markdown("---")
st.markdown("### Record New Audio")

wav_bytes = st_audiorec()

if wav_bytes is not None:
    st.audio(wav_bytes, format="audio/wav")
    st.success("Translating...")

    files = {"file": ("recording.wav", wav_bytes, "audio/wav")}
    data = {
        "conversation_id": str(uuid.uuid4()),
        "sender": "user",
    }
    try:
        response = requests.post(SEND_AUDIO_ENDPOINT, files=files, data=data)
        if response.ok:
            result = response.json()
            #st.success("✅ Sent to backend successfully!")
            st.markdown("### Transcription:")
            st.write(result.get("transcription", ""))
            st.markdown("### Translation:")
            st.write(result.get("translation", ""))
        else:
            st.error(f"❌ Backend error: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error sending to backend: {e}")

st.markdown("---")

# Fetch previous translations
try:
    prev_resp = requests.get(GET_PREV_ENDPOINT)
    prev_resp.raise_for_status()
    prev_items = prev_resp.json()  # list of dicts
except Exception:
    prev_items = []

st.markdown("### Previous Translations (translated text)")

if prev_items:
    # Use only translation snippet as label
    options = {
        f"{item['translation'][:40]}...": item
        for item in prev_items
    }


    selected_label = st.selectbox("Select a previous translation", options.keys())
    selected_item = options[selected_label]

    st.markdown("### Previous Transcription:")
    st.write(selected_item.get("transcription", ""))
    st.markdown("### Previous Translation:")
    st.write(selected_item.get("translation", ""))
else:
    st.info("No previous translations found.")
