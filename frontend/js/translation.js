/**
 * Ports backend/translation.py 1:1. No real translation engine is called
 * here (and never was, even server-side) -- these are pre-written Kannada
 * (kn-IN) advisory templates, one per known disease. This is an honest
 * limitation, not a shortcut: free-form text falls back to English with a
 * visible flag rather than pretending to translate it.
 */

export const KANNADA_TEMPLATES = {
  early_blight: (
    "ನಿಮ್ಮ ಟೊಮೇಟೊ ಗಿಡದಲ್ಲಿ ಅರ್ಲಿ ಬ್ಲೈಟ್ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬರುತ್ತಿವೆ. " +
    "ಇಂದೇ ಬಾಧಿತ ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ಮಳೆಗೆ ಮುನ್ನ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ ಸಿಂಪಡಿಸಿ."
  ),
  late_blight: (
    "ತಡವಾದ ಕೊಳೆ ರೋಗ (ಲೇಟ್ ಬ್ಲೈಟ್) ಇರುವ ಸಾಧ್ಯತೆ ಇದೆ, ಇದು ವೇಗವಾಗಿ ಹರಡುತ್ತದೆ. " +
    "ಬಾಧಿತ ಭಾಗಗಳನ್ನು ಕೂಡಲೇ ತೆಗೆದುಹಾಕಿ ಮತ್ತು ಮ್ಯಾಂಕೋಜೆಬ್ ಸಿಂಪಡಿಸಿ."
  ),
  leaf_curl_virus: (
    "ಎಲೆ ಮುರುಟು ವೈರಸ್ (ಲೀಫ್ ಕರ್ಲ್ ವೈರಸ್) ಕಂಡುಬರುತ್ತಿದೆ. " +
    "ಇದು ಬಿಳಿ ನೊಣದಿಂದ ಹರಡುತ್ತದೆ. ಇಮಿಡಾಕ್ಲೋಪ್ರಿಡ್ ಸಿಂಪಡಿಸಿ ಬಿಳಿ ನೊಣ ನಿಯಂತ್ರಿಸಿ."
  ),
  bacterial_wilt: (
    "ಹಠಾತ್ ಗಿಡ ಬಾಡುವ ಲಕ್ಷಣಗಳು ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ವಿಲ್ಟ್ ಅನ್ನು ಸೂಚಿಸುತ್ತವೆ. " +
    "ಬಾಧಿತ ಗಿಡವನ್ನು ಬೇರಿನೊಂದಿಗೆ ತೆಗೆದು ನಾಶಪಡಿಸಿ, ಮುಂದಿನ ಬೆಳೆಗೆ ಅದೇ ಜಾಗದಲ್ಲಿ ಟೊಮೇಟೊ ನೆಡಬೇಡಿ."
  ),
  fusarium_wilt: (
    "ಫ್ಯುಸಾರಿಯಂ ವಿಲ್ಟ್ ಇರುವ ಸಾಧ್ಯತೆ ಇದೆ. " +
    "ಬಾಧಿತ ಗಿಡವನ್ನು ತೆಗೆದುಹಾಕಿ ಮತ್ತು ಕನಿಷ್ಠ 4 ಬೆಳೆಗಳ ಕಾಲ ಅದೇ ಜಾಗದಲ್ಲಿ ಟೊಮೇಟೊ ನೆಡುವುದನ್ನು ತಪ್ಪಿಸಿ."
  ),
  blossom_end_rot: (
    "ಹಣ್ಣಿನ ತಳದಲ್ಲಿ ಕಪ್ಪು ಕಲೆ ಬ್ಲಾಸಮ್ ಎಂಡ್ ರಾಟ್ ಅನ್ನು ಸೂಚಿಸುತ್ತದೆ, ಇದು ಶಿಲೀಂಧ್ರ ರೋಗವಲ್ಲ. " +
    "ಕ್ರಮಬದ್ಧ ಮತ್ತು ಸಮಾನ ನೀರು ಕೊಡಿ, ಹೆಚ್ಚು ಮತ್ತು ಕಡಿಮೆ ನೀರು ಕೊಡುವುದನ್ನು ತಪ್ಪಿಸಿ."
  ),
  septoria_leaf_spot: (
    "ಸೆಪ್ಟೋರಿಯಾ ಎಲೆ ಚುಕ್ಕೆ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬರುತ್ತಿವೆ. " +
    "ಬಾಧಿತ ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆದು ಮ್ಯಾಂಕೋಜೆಬ್ ಸಿಂಪಡಿಸಿ."
  ),
  spider_mite_damage: (
    "ಎಲೆಗಳ ಮೇಲಿನ ಚುಕ್ಕೆಗಳು ಜೇಡ ಮಿಟೆ (ಸ್ಪೈಡರ್ ಮೈಟ್) ಹಾನಿಯನ್ನು ಸೂಚಿಸುತ್ತವೆ. " +
    "ಎಲೆಗಳ ಕೆಳಭಾಗಕ್ಕೆ ಬಲವಾದ ನೀರಿನ ಸಿಂಪಡಣೆ ಮಾಡಿ ಅಥವಾ ಬೇವಿನ ಎಣ್ಣೆ ಬಳಸಿ."
  ),
  healthy: (
    "ನಿಮ್ಮ ಗಿಡ ಈಗ ಆರೋಗ್ಯಕರವಾಗಿ ಕಾಣುತ್ತಿದೆ. ನಿಯಮಿತ ನೀರು ಮತ್ತು ಪರಿಶೀಲನೆ ಮುಂದುವರಿಸಿ."
  ),
  uncertain: (
    "ನೀಡಿದ ಮಾಹಿತಿಯಿಂದ ನಿರ್ದಿಷ್ಟ ರೋಗವನ್ನು ಗುರುತಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. " +
    "ದಯವಿಟ್ಟು ರೋಗಲಕ್ಷಣಗಳ ಸ್ಪಷ್ಟ ವಿವರಣೆ ನೀಡಿ."
  ),
};

/**
 * @param {string} disease
 * @param {string} englishText
 * @param {string} targetLanguageCode
 * @returns {string}
 */
export function translateAdvisory(disease, englishText, targetLanguageCode = "kn-IN") {
  if (targetLanguageCode === "kn-IN" && disease in KANNADA_TEMPLATES) {
    return KANNADA_TEMPLATES[disease];
  }
  return `[untranslated — no Kannada template for '${disease}'] ${englishText}`;
}
