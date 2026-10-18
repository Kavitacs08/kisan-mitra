# Kisan Mitra — Narration Script

**Status: this is what's actually in `Kisan_Mitra_Demo.mp4`** (2:28,
synthesized narration via `scripts/synthesize_narration.py` +
`scripts/build_synced_demo.py`). Kept here as the readable reference for
the exact wording and sequence — if you want to re-record with your own
voice instead, read this aloud against `Kisan_Mitra_Demo_silent.mp4`
(built by the older `scripts/build_demo_video.py`) and mux with
`scripts/mux_narration.py`.

---

## 0. Title card
> "Kisan Mitra. A tomato crop advisory agent for the Kolar belt, Karnataka."

## 1. The problem is enormous
*(big stat card: 86% / 1 bar of signal)*
> "Eighty-six percent of India's farmers are smallholders. One bad disease
> outbreak can wipe out an entire season's income. There's no agronomist
> on call, no reliable signal to search with, and by the time the damage
> is visible, it's already too late to stop it spreading."

## 2. The solution: one photo, five real actions
*(checklist card)*
> "Kisan Mitra turns a photo and a few spoken words into a cited
> diagnosis, a spoken answer in the farmer's own language, and real
> economic action: the nearest dealer, an outbreak warning before damage
> shows, an insurance claim ready to file, and a group discount with
> other farmers nearby."

## 3. Watch it live
> "Watch what happens, live."

## 4. Live diagnosis (real app)
*(the real app: typing the symptom, "Analyzing with Gemini...", the
result card resolving)*
> "Gemini diagnoses it live: early blight, ninety-five percent
> confidence, with a citation. A second Gemini call then decides what to
> do next, using real function-calling, not hardcoded rules."

## 5. The combo moment (real app, scrolled)
*(outbreak banner, Kannada advisory, dealer card, insurance packet)*
> "A warning: nearby outbreak, days before symptoms show. The advisory
> comes back fully in Kannada."
>
> *(spoken in Kannada by a native Kannada voice — kn-IN-SapnaNeural)*
> "ನಿಮ್ಮ ಟೊಮೇಟೊ ಗಿಡದಲ್ಲಿ ಅರ್ಲಿ ಬ್ಲೈಟ್ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬರುತ್ತಿವೆ. ಇಂದೇ ಬಾಧಿತ
> ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ಮಳೆಗೆ ಮುನ್ನ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ ಸಿಂಪಡಿಸಿ."
> (Remove the infected lower leaves today; spray copper oxychloride
> before the forecast rain.)
>
> "The nearest dealer. An insurance packet, ready to file. One diagnosis,
> five real actions."

## 6. The group-buy card, explained
*(a real screenshot of the group-buy card from the deployed app, with
callouts: 5 nearby farmers / 12% discount / ₹158 vs ₹180 per kg)*
> "Look closer at one of those actions: the group-buy card. Five nearby
> farmers, flagged by the same outbreak signal, all need the same
> treatment this week. Kisan Mitra checks the dealer's own bulk pricing
> tier and automatically unlocks a twelve percent discount the moment
> combined demand crosses the threshold: one-eighty rupees a kilogram
> alone, down to one fifty-eight together, same dealer, same day."

## 7. One screen, five actions
> "Diagnosis that doesn't stop at diagnosis."

## 8. Scale: the district view
> "And it scales beyond one farmer."

## 9. District dashboard (real app)
*(the real dashboard: cluster table, report counts)*
> "The same signal, anonymized, becomes a policy tool for an extension
> officer."

## 10. Closing card
> "Built on real Gemini, deployed at zero billing. Kisan Mitra: diagnosis
> that doesn't stop at diagnosis."

---

## Notes

- **The group-buy discount figures** (5 farmers, 12%, ₹180→₹158.4/kg) are
  read directly off a real screenshot captured from the deployed app
  (`docs/video/assets/groupbuy_card_crop.png`) — see
  `frontend/js/group-buy.js` for the actual bulk-discount logic
  (`BULK_DISCOUNT_PCT = 12`, `BULK_THRESHOLD_KG = 10.0`), which is
  illustrative demo pricing, not sourced from a real dealer's rate card
  (documented honestly in that file's own comments).
- **The 86% smallholder-farmer statistic** is a widely-cited figure for
  India's landholding structure (small/marginal holdings), used here as
  scene-setting context for the problem's scale — not a claim about the
  Kolar belt specifically.
- To regenerate this video after any further edits: `python
  scripts/synthesize_narration.py` then `python
  scripts/build_synced_demo.py`.
