# Kisan Mitra — Narration Script

Read this aloud while watching `Kisan_Mitra_Demo_silent.mp4` play. Each
line's timestamp is where that *segment starts* in the silent assembly —
start speaking at or just after that mark. Total runtime: 62.4s (well
under the 3:00 limit — there's room to speak at a natural, confident pace
without rushing, or to add B-roll later if you want to stretch it).

Record straight through in one take if you can — it's short enough that a
single take usually beats stitching several together. If you must retake
a line, re-record just that segment and we can re-mux.

---

## 0:00–0:05 — Title card
*(Kisan Mitra logo card is on screen)*

> "Kisan Mitra — a smallholder tomato crop advisory agent for the Kolar
> belt, Karnataka. Built for the AI Builder Cup, Google Cloud GenAI
> Hackathon."

## 0:05–0:08 — Beat 1: The problem
*(dark card, "The problem")*

> "A smallholder tomato farmer spots a diseased leaf. There's no
> agronomist to call, and one bar of signal to search with."

## 0:08–0:11 — Beat 2/3 label: Diagnosis + orchestration
*(dark card, "Live diagnosis, cited — and the orchestration behind it")*

> "Watch what happens when they describe it — live, right now, no mockup."

## 0:11–0:25 — Live diagnosis (app, typing → Gemini call → result)
*(the real app: symptom text visible, "Analyzing description with
Gemini..." then the result card appears)*

> "They type the symptom. Gemini analyzes it — multimodal, grounded in a
> bilingual disease guide — and comes back with early blight, ninety-five
> percent confidence, and a citation: section one-point-one of the early
> blight guide. This isn't a black box guessing. And notice the label
> right here — 'via Gemini,' and 'tool selection via Gemini.' That second
> label is the part no other diagnosis app does: a second Gemini call,
> using real function-calling, decides which of four tools to invoke
> next — not a hardcoded if-else a developer wrote in advance."

## 0:25–0:41 — The combo moment (scroll through all cards)
*(outbreak banner, Kannada advisory, dealer card, insurance packet all
visible as the page scrolls)*

> "And here's the moment that matters most. A warning at the top: 'Late
> blight has been reported on five nearby tomato plots in the last seven
> days — inspect your crop today.' That's a second farmer being warned
> *before* their own crop shows symptoms, because Kisan Mitra reasons
> across nearby reports, not just one photo at a time.
>
> The advisory itself comes back in Kannada —
> *(read the Kannada line aloud; phonetic guide below)*
> 'nimma tomato giḏḏadalli early blight rōgada lakṣaṇagaḻu kaṇḍubaruttive.
> inde bādhita kelagina elegaḻannu tegeduhāki. maḻege munna copper
> oxychloride simpaḏisi.'
> — remove the infected lower leaves today, and spray copper oxychloride
> before the forecast rain arrives.
>
> Below that: the nearest dealer with today's stock and price. And
> below *that*: a crop-loss insurance evidence packet, already assembled,
> ready to attach to a claim. One diagnosis. Five real actions."

## 0:41–0:44 — Beat 4 label: One screen, five actions
*(dark card, "One screen, five actions")*

> "Diagnosis that doesn't stop at diagnosis."

## 0:44–0:47 — Beat 5 label: Scale, the district view
*(dark card, "Scale: the district view")*

> "And it scales beyond one farmer, too."

## 0:47–0:56 — District dashboard
*(the real dashboard: cluster table, report counts)*

> "The same signal, aggregated and anonymized, becomes a policy tool —
> an extension officer sees active outbreak clusters by village, without
> ever seeing an individual farmer's identity or exact plot location."

## 0:56–1:02 — Closing card
*(dark card, Kisan Mitra, tagline, stack, links)*

> "Built on real Gemini — multimodal diagnosis and real function-calling
> orchestration — deployed on Firebase Hosting at zero billing, zero
> credit card. Kisan Mitra: diagnosis that doesn't stop at diagnosis."

---

## Notes

- **Kannada line pronunciation**: the phonetic guide above is a rough
  transliteration, not formal IAST — close enough for a confident read.
  If you'd rather skip reading the Kannada aloud and just say "the
  advisory comes back fully in Kannada" while pointing at the screen,
  that's a safe fallback — judges will see the Kannada script directly
  either way.
- **Pacing**: the live-diagnosis segment (0:11–0:25, 14s) and the combo
  scroll (0:25–0:41, 16s) are the two segments with the most to say —
  if you find yourself rushing, we can lengthen those two clips in
  `scripts/build_demo_video.py` (the `trim_clip` calls) and rebuild in
  under a minute.
- **If you re-record a single beat**: tell me which timestamp range,
  and I'll remux just that portion once you send the new audio file —
  no need to re-record the whole thing.
