import streamlit as st
import requests
from loguru import logger
from sys import stderr
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import torchaudio
import io

if torch.cuda.is_available():
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

speech_to_text = pipeline("automatic-speech-recognition", model="openai/whisper-small", language='fr')

# Load Qwen model and tokenizer
model_name = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
text_to_prompt_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
)

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

            text_output = speech_to_text(audio_tensor)

            st.text(f"Transcription : {text_output['text']}")

            # Prepare the model input
            messages = [
                {"role": "user", 
                "content": 
                f"Transforme cette description en prompt Midjourney optimisée. Format de sortie : [sujet principal], [style artistique], [détails visuels], [éclairage], [ambiance], [paramètres techniques]\n Description : {text_output['text']}"}
            ]
            
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            
            model_inputs = tokenizer([text], return_tensors="pt").to(text_to_prompt_model.device)
            
            # Generate text
            generated_ids = text_to_prompt_model.generate(
                **model_inputs,
                max_new_tokens=32768
            )
            
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

            try:
                # rindex finding 151668 (</think>)
                index = len(output_ids) - output_ids[::-1].index(151668)
            except ValueError:
                index = 0

            prompt =tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

            st.text(f"Prompt: {prompt}")

        except requests.exceptions.HTTPError as e:
            st.error(f"Erreur HTTP : {e}")
            logger.error(f"Erreur HTTP : {e}")
        except Exception as e:
            st.error(f"Erreur lors de l'analyse: {e}")
        
