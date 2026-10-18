/**
 * Ports backend/tts.py's intent (Prompt 10 — Text-to-Speech), but upgrades
 * the mock: instead of always returning audio_available=False, this
 * feature-detects a real kn-IN voice via the browser's Web Speech API
 * (SpeechSynthesis) and actually speaks the advisory when one is found.
 *
 * Kannada voice availability is genuinely device/browser-dependent (most
 * reliable on Chrome for Android; often absent on desktop Windows/Safari
 * unless a language pack or remote voice is installed) -- so this never
 * assumes success. When no kn-IN voice is found, it falls back to the
 * exact same "voice unavailable, text advisory shown" UX the Python mock
 * always rendered.
 */

let _voicesReady = null;

function waitForVoices() {
  if (_voicesReady) return _voicesReady;
  _voicesReady = new Promise((resolve) => {
    if (!("speechSynthesis" in window)) {
      resolve([]);
      return;
    }
    const existing = speechSynthesis.getVoices();
    if (existing.length > 0) {
      resolve(existing);
      return;
    }
    // Voice list loads asynchronously on first call in many browsers.
    speechSynthesis.addEventListener(
      "voiceschanged",
      () => resolve(speechSynthesis.getVoices()),
      { once: true }
    );
    // Safety timeout in case the event never fires (some browsers/webviews).
    setTimeout(() => resolve(speechSynthesis.getVoices()), 1500);
  });
  return _voicesReady;
}

async function findKannadaVoice() {
  const voices = await waitForVoices();
  return voices.find((v) => v.lang === "kn-IN") || voices.find((v) => v.lang?.startsWith("kn")) || null;
}

/**
 * Mirrors speak_advisory()'s return shape: {audioAvailable, spokenText}.
 * If a kn-IN voice is available, actually speaks the text via
 * speechSynthesis.speak(); the caller does not need to await playback.
 * @param {string} translatedText
 * @param {string} languageCode
 * @returns {Promise<{audioAvailable: boolean, spokenText: string}>}
 */
export async function speakAdvisory(translatedText, languageCode = "kn-IN") {
  if (!("speechSynthesis" in window)) {
    return { audioAvailable: false, spokenText: translatedText };
  }

  const voice = await findKannadaVoice();
  if (!voice) {
    return { audioAvailable: false, spokenText: translatedText };
  }

  const utterance = new SpeechSynthesisUtterance(translatedText);
  utterance.voice = voice;
  utterance.lang = languageCode;
  speechSynthesis.speak(utterance);

  return { audioAvailable: true, spokenText: translatedText };
}
