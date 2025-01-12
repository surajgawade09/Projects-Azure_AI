import streamlit as st
from dotenv import load_dotenv
import os
import langcodes
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.translation.text import *
from azure.ai.translation.text.models import InputTextItem
import azure.cognitiveservices.speech as speech_sdk

# Initialize Azure clients
def initialize_azure_clients():
    try:
        load_dotenv()
        ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
        ai_key = os.getenv('AI_SERVICE_KEY')
        translator_region = os.getenv('TRANSLATOR_REGION')
        translator_key = os.getenv('TRANSLATOR_KEY')
        speech_key = os.getenv('SPEECH_KEY')
        speech_region = os.getenv('SPEECH_REGION')
        ai_region = os.getenv('SPEECH_REGION')

        # Check if all environment variables are loaded
        if not all([ai_endpoint, ai_key, translator_region, translator_key, speech_key, speech_region]):
            st.error("One or more environment variables are missing. Please check your .env file.")
            return None, None, None

        ai_client = TextAnalyticsClient(endpoint=ai_endpoint, credential=AzureKeyCredential(ai_key))
        translator_client = TextTranslationClient(TranslatorCredential(translator_key, translator_region))
        speech_config = speech_sdk.SpeechConfig(ai_key, ai_region)

        return ai_client, translator_client, speech_config
    except Exception as e:
        st.error(f"Error initializing Azure clients: {e}")
        return None, None, None

# Speech-to-text function
def SpeechToText(speech_config):
    try:
        audio_config = speech_sdk.AudioConfig(use_default_microphone=True)
        speech_recognizer = speech_sdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        st.write("Listening...")
        result = speech_recognizer.recognize_once_async().get()

        if result.reason == speech_sdk.ResultReason.RecognizedSpeech:
            return result.text
        else:
            st.error(f"Speech recognition failed: {result.reason}")
            return None
    except Exception as e:
        st.error(f"Error in SpeechToText: {e}")
        return None

# Text-to-speech function
def TextToSpeech(speech_config, text, target_language, rate, volume):
    try:
        voice_name = get_voice_for_language(target_language)
        speech_config.speech_synthesis_voice_name = voice_name
        speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config=speech_config)

        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-GB">
            <voice name="{voice_name}">
                <prosody rate="{rate}" volume="{volume}">{text}</prosody>
            </voice>
        </speak>
        """
        result = speech_synthesizer.speak_ssml_async(ssml).get()

        if result.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
            st.error(f"Speech synthesis failed: {result.reason}")
    except Exception as e:
        st.error(f"Error in TextToSpeech: {e}")

# Map language codes to voices
def get_voice_for_language(language):
    language_to_voices_map = {
        "en": "en-GB-RyanNeural",
        "fr": "fr-FR-HenriNeural",
        "es": "es-ES-AlvaroNeural",
        "de": "de-DE-KarlNeural",
        "it": "it-IT-ElsaNeural",
        "pt": "pt-BR-AntonioNeural",
        "ru": "ru-RU-DmitryNeural",
        "ja": "ja-JP-KeitaNeural",
        "ko": "ko-KR-SunHiNeural",
        "zh": "zh-CN-XiaoxiaoNeural",
        "ar": "ar-EG-AmirNeural",
        "nl": "nl-NL-EmmaNeural",
        "sv": "sv-SE-AlvaNeural",
        "pl": "pl-PL-MarekNeural",
        "tr": "tr-TR-HakanNeural",
        "da": "da-DK-MikkelNeural",
        "no": "no-NO-KristianNeural",
        "fi": "fi-FI-SatuNeural",
        "cs": "cs-CZ-VojtaNeural",
        "hu": "hu-HU-KrisztianNeural",
        "sk": "sk-SK-PeterNeural",
        "ro": "ro-RO-AndreiNeural",
        "he": "he-IL-YuvalNeural",
        "th": "th-TH-PattamaNeural",
        "id": "id-ID-DewiNeural",
        "vi": "vi-VN-AnhNeural",
        "hi": "hi-IN-SwaraNeural",
        "ms": "ms-MY-ZuraNeural",
        "fil": "fil-PH-JoannaNeural",
        "bn": "bn-IN-SwapanNeural",
        "ta": "ta-IN-SundarNeural",
        "te": "te-IN-VaniNeural",
        "ml": "ml-IN-MadhuriNeural",
        "mr": "mr-IN-AarohiNeural",
        "gu": "gu-IN-RohitNeural",
        "kn": "kn-IN-KavyaNeural",
        "pa": "pa-IN-MadhurNeural",
        "or": "or-IN-SurajNeural",
        "si": "si-LK-DilaniNeural"
    }
    return language_to_voices_map.get(language, "en-GB-RyanNeural")

# Main Streamlit app
def main():
    st.title("Speech Translation")

    ai_client, translator_client, speech_config = initialize_azure_clients()
    if not all([ai_client, translator_client, speech_config]):
        return

    col1, col2 = st.columns([2, 1])

    # Initialize session state for spoken_text and translation
    if "spoken_text" not in st.session_state:
        st.session_state["spoken_text"] = ""
    if "translation" not in st.session_state:
        st.session_state["translation"] = ""

    with col1:
        # Display the spoken text
        st.text_area("You said:", st.session_state["spoken_text"], height=100, disabled=True)
        
        # Display the translation if available
        if st.session_state["translation"]:
            st.markdown(f"### Translation:")
            st.write(st.session_state["translation"])

    with col2:
        if st.button("Tap to Speak"):
            # Capture spoken text
            spoken_text = SpeechToText(speech_config)
            if spoken_text:
                # Update session state with the new spoken text
                st.session_state["spoken_text"] = spoken_text
                # Clear the previous translation when new input is provided
                st.session_state["translation"] = ""

        # Text input for target language
        target_language_name = st.text_input("Enter target language (e.g., French, Spanish):")

        # Sliders for voice speed and volume
        speed = st.selectbox(
        "Speed of Voice:",
        options=["x-slow", "slow", "medium", "fast", "x-fast"]
        )

        volume = st.selectbox(
            "Volume:",
            options=["x-soft", "soft", "medium", "loud", "x-loud"]
        )

        if st.button("Translate"):
            if st.session_state["spoken_text"]:
                spoken_text = st.session_state["spoken_text"]
                detected_language = ai_client.detect_language([spoken_text])[0].primary_language.iso6391_name
                target_language = langcodes.find(target_language_name).language if target_language_name else None

                if target_language:
                    input_text_elements = [InputTextItem(text=spoken_text)]
                    translation_response = translator_client.translate(content=input_text_elements, to=[target_language])
                    if translation_response:
                        # Update session state with the new translation
                        st.session_state["translation"] = translation_response[0].translations[0].text
                        
                        # Perform text-to-speech
                        TextToSpeech(
                            speech_config=speech_config,
                            text=st.session_state["translation"],
                            target_language=target_language,
                            rate=str(speed),
                            volume=str(volume),
                        )


if __name__ == "__main__":
    main()
