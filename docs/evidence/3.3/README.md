# Part 3.3 evaluation and evidence

Everything here comes from runs on November 2, 2026. The app ran on localhost (FastAPI on port 8000 with SQLite, Vue dev server on port 5173) with `LLM_MODE=mock`, so **every model reply in this evaluation is a saved mock reply, not the live model.** All users and situations are fictional ("Sofia" and "Maya" are made up).

## How it was run

- `run_evaluation.py` drives Chromium with Playwright through 22 scenarios, reads the SQLite file after each step, and writes `results.json` and `scenarios-table.md`. It is repeatable: start the two servers and run it.
- `backend/tests/` has 24 automated tests, all mocked (`pytest-results.txt`).
- `db-inspection.txt` is the database after the evaluation run.
- `clean-checkout.txt` shows a fresh clone set up by following the README exactly.
- `videos/` has the demo and the process screencast, and the script that recorded them.

## Results: 22 of 22 scenarios passed

Types: 13 ordinary use, 2 interruptions, 7 failure cases.

| # | Type | What the user does | Expected | Observed | Result |
|---|---|---|---|---|---|
| S01 | ordinary | Opens the app for the first time. | Home shows Breath, Ground, Journal and an optional check-in. No "Your usual" yet. | 4 check-in choices shown, no "Your usual". ([screenshot](s01-first-visit.png)) | Pass |
| S02 | ordinary | Taps the check-in "Wound up". | Screen shrinks to one suggestion (Breath reset) plus "Show all options". | 1 activity button visible, and it is Breath reset. ([screenshot](s02-wound-up.png)) | Pass |
| S03 | ordinary | Taps "Show all options" after "Wound up". | All three activities come back. | 3 activity buttons visible. | Pass |
| S04 | ordinary | Changes the check-in to "Scattered". | Ground reset becomes the suggestion at the top; the others stay. | Suggested: Ground reset. ([screenshot](s04-scattered.png)) | Pass |
| S05 | ordinary | Changes the check-in to "Low". | Journal becomes the suggestion at the top. | Suggested: Journal. | Pass |
| S06 | ordinary | Taps "Clear" on the check-in. | Normal home screen; profile shows no current check-in. | Check-in choices back; profile check-in is empty. | Pass |
| S07 | ordinary | Does a full Breath reset with press and hold. | About 66 s, saved as completed with breaths followed. | Completed, 66.008 s, 6 breaths followed. ([screenshot](s07-done.png)) | Pass |
| S08 | ordinary | Does a Breath reset with the microphone (simulated breath-out sound). | Breaths saved, but the Done screen shows no count or score. | 6 breaths saved; no count on the Done screen. | Pass |
| S09 | failure | Chooses Microphone but the browser denies access. | Stays on setup, explains it, switches to press and hold. | "Couldn't use the microphone, so you can press and hold the circle instead." Hold selected. ([screenshot](s09-mic-denied.png)) | Pass |
| S10 | interruption | Opens Need help now in the middle of a Breath reset, then closes it. | Exercise pauses; that time is not counted. | "paused" shown; 4.1 s paused, excluded from the 6.6 s of exercise time. ([screenshot](s10-crisis-during-exercise.png)) | Pass |
| S11 | interruption | Taps Stop partway through. | "You stopped. That's fine." Saved as stopped, not as a failure. | Saved as stopped after 1 step. ([screenshot](s11-stopped.png)) | Pass |
| S12 | ordinary | Does a Ground reset, tapping every 2.5 s (the planned pace). | One sense per screen, no typing, under 90 s. | Completed in 42.1 s. | Pass |
| S13 | ordinary | Returns home after two Breath resets and one Ground reset. | "Your usual: Breath reset" appears with no setup. | Shown. ([screenshot](s13-usual.png)) | Pass |
| S14 | ordinary | "Maya" saves her name and "swimming", checks in as Scattered, and writes she is overwhelmed about a swim meet. | Calm reply that uses her name once and offers her usual reset as an option. Context shows name, activity, check-in, usual. | "Thanks for writing, Maya. That sounds like a lot to hold at once. If it would help, your usual Breath reset is there and takes about a minute. Or you can keep writing here." Context has all four. ([screenshot](s14-journal-personalized.png)) | Pass |
| S15 | ordinary | Writes "this workout block is killing me". | Treated as a figure of speech: normal reply, no crisis panel. | No crisis panel. | Pass |
| S16 | failure | Writes a crisis-related sentence in the Journal. | Panel opens at once, fixed message, model not called, both messages flagged. | Panel opened; model calls stayed at 2; both messages flagged. ([screenshot](s16-crisis-input.png)) | Pass |
| S17 | failure | Writes indirect wording: "I just want to disappear for good". | Known limit: the phrase list misses this. Need help now must still be there. | Not caught (as expected); Need help now visible. | Pass |
| S18 | ordinary | Turns off "Let the companion see my past journal entries". | Context drops earlier entries and tells the model not to mention them. | Earlier entry gone; "turned off" note present. | Pass |
| S19 | failure | The model fails (fail mode), then the user writes in the Journal. | Fallback lines, message still saved, crisis panel still works. | Home and Journal used fallbacks; crisis panel opened. ([screenshot](s19-model-fail.png)) | Pass |
| S20 | ordinary | Turns on Larger text, then reloads. | Text stays larger, because the setting is saved. | Still larger after reload. ([screenshot](s20-large-text.png)) | Pass |
| S21 | ordinary | Opens History. | Each reset with Done/Stopped and length; each journal entry by its first line. | 7 items listed. ([screenshot](s21-history.png)) | Pass |
| S22 | failure | The backend is stopped; the user opens Need help now and starts a Breath reset. | Crisis panel works (static); exercise runs and says it isn't saved. | All three true. ([screenshot](s22-backend-down.png)) | Pass |

S17 passes because the expected result is the documented limitation. It does not mean the app catches indirect wording.

## Behavior checks

These are checked across every scenario above, not just one.

| Check | What should always hold | Result |
|---|---|---|
| B1 | Need help now is visible on every screen: home, setup, inside both exercises, Done, Stopped, Journal, profile, history, with the model failing, and with the backend stopped. | Visible on all 12 screens checked. Pass |
| B2 | Crisis-flagged text never reaches the model. The number of Journal model calls equals the number of non-flagged user messages. | 4 calls for 4 non-flagged messages; the 1 flagged message caused no call. Pass |
| B3 | No reply shown to the user contains blocked words (diagnosis, disorder, therapist, monitor, "great job", "proud of you") or an exclamation mark. | 8 assistant messages checked, 0 problems. Pass |
| B4 | Every guided exercise is planned at 90 s or less and every completed run took 90 s or less. | Plans: breath 66 s, ground 55.5 s. Runs: 66.008 s, 66.004 s, 42.1 s. Pass |

## Surprising finding

My Ground reset timing plan was too cautious. I planned 55.5 seconds, assuming 3 seconds to read each sense prompt plus 2.5 seconds per item. When the test tapped at exactly 2.5 seconds per item, the whole exercise took only 42.1 seconds. The reading time I assumed mostly disappears, because the next prompt appears as soon as the last dot fills, and the person reads it while starting to notice the next thing. The good news is there is more room under 90 seconds than I thought. The other lesson is that a planned time is only a guess until you measure it.

A smaller surprise: the order of my mock reply rules changed the tone. "I feel overwhelmed before my race" first got the training reply, because "race" matched before "overwhelmed". It showed me how fragile keyword rules are, which is part of why the crisis check is a backup and not the only safety route.

## Live model: not run

I don't have an Anthropic API key, so I could not repeat cases with the live model. `live_check.py` is ready: it runs 5 Journal inputs 3 times each (15 calls, under the 50-call limit), and records the source, length, name use, and whether a reply mentions 988 or Need help now. Until it runs, nothing here shows how the real model behaves. The mocked checks prove that the app's code behaves correctly around the model (filtering, fallbacks, crisis routing, context), not that the model's own replies are good.

## Limitation I have not tested

I have not tested the app with a screen reader. The cues use `aria-live` and the buttons have labels, but I don't know if the breathing countdown is useful or just noisy when read aloud every second. I also have not tested a real microphone in a real room, or browsers other than Chromium.
