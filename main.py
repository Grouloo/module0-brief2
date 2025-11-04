import streamlit as st
import requests
from loguru import logger
from sys import stderr
from transformers import pipeline
import torch
import torchaudio
import io

pipe = pipeline("automatic-speech-recognition", model="openai/whisper-small", language='fr')

logger.add(stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("logs/main.log")

st.header("Petit Prince AI")

with st.form("my_form"):
    audio_input = st.audio_input("Enregistrez-vous et demandez un dessin.")
    submitted = st.form_submit_button("Envoyer")

    if submitted:
        try:
            audio_bytes = audio_input.read()
            audio_buffer = io.BytesIO(audio_bytes)
            audio_tensor, sample_rate = torchaudio.load(audio_buffer)

            text_output = pipe(audio_tensor)

            st.text(text_output)
        except requests.exceptions.HTTPError as e:
            st.error(f"Erreur HTTP : {e}")
            logger.error(f"Erreur HTTP : {e}")
        except Exception as e:
            st.error(f"Erreur lors de l'analyse: {e}")
        
