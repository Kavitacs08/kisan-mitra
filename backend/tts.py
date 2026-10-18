"""Prompt 10 — Text-to-Speech.

Mock mode cannot produce real audio without Cloud TTS credentials, so it
returns audio_available=False with the text that would have been spoken,
rather than silently pretending audio exists. The frontend (Prompt 18) shows
a text advisory with a "voice unavailable in demo mode" note when this flag
is false, instead of a broken audio player.
"""
from config import USE_MOCK


def _real_cloud_tts(text: str, language_code: str) -> bytes:
    # REAL: swap in google-cloud-texttospeech here, e.g.
    #   from google.cloud import texttospeech
    #   client = texttospeech.TextToSpeechClient()
    #   synthesis_input = texttospeech.SynthesisInput(text=text)
    #   voice = texttospeech.VoiceSelectionParams(language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    #   audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    #   response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    #   return response.audio_content
    raise NotImplementedError("Set USE_MOCK=false and configure Cloud Text-to-Speech credentials.")


def speak_advisory(translated_text: str, language_code: str = "kn-IN"):
    """Returns (audio_available: bool, audio_bytes_or_none, spoken_text)."""
    if USE_MOCK:
        return False, None, translated_text
    audio_bytes = _real_cloud_tts(translated_text, language_code)
    return True, audio_bytes, translated_text


if __name__ == "__main__":
    available, audio, text = speak_advisory("तुमच्या टोमॅटोच्या रोपावर लवकर करपा रोगाची लक्षणे दिसत आहेत.")
    print(f"audio_available={available}")
    print(f"spoken_text={text}")
