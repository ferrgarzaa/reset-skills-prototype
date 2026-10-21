# Part 3.2 verification evidence

All of this comes from one run on October 20, 2026, against the app running on localhost (FastAPI on port 8000, Vue dev server on port 5173). The backend ran with `LLM_MODE=mock`, so every model reply here is a saved mock response, not a live model call. Only fictional scenarios were used.

How it was collected:
- Browser: `browser_evidence.py` drives Chromium with Playwright and takes the screenshots below. The browser console timing logs are in `browser-run-log.txt`.
- Database: `backend/tools/inspect_db.py` printed the tables after the run, in `db-inspection.txt`.
- Automated tests: `pytest` with mocked responses, in `pytest-results.txt` (20 passed).

## What each piece shows

| # | Scenario (what the user does) | Expected | Observed | Evidence |
|---|---|---|---|---|
| 1 | Opens the app for the first time | Home shows Breath, Ground, and Journal; no "Your usual" yet; Need help now in the header | As expected | [01](01-home-first-visit.png) |
| 2 | Picks Breath reset, chooses "Press and hold" | Setup screen explains the option; this is entry time, measured separately | As expected | [02](02-breath-setup-hold.png) |
| 3 | Holds the circle while it grows | Circle fills while held; cue counts down "Breathe in" | As expected | [03](03-breath-inhale-holding.png) |
| 4 | Lets go while the circle shrinks | After a held inhale and a released exhale, "with you" appears for that breath | As expected | [04](04-breath-exhale-heard.png) |
| 5 | Finishes the Breath reset | Done screen, closing line, optional one-tap feedback; session saved as completed with measured duration | Saved as completed, 66.013 s. The closing line was the fallback, not the mock line (see "Failure found" below) | [05](05-done-closing-line.png), session 1 in [DB](db-inspection.txt) |
| 6 | Breath reset with "Microphone" and a simulated breath-out sound during each exhale | Ring around the circle reacts to sound; "with you" appears when a breath out is heard | Heard 6 of 6 breaths, saved as `breaths_detected = 6` | [06](06-breath-mic-heard.png), session 2 |
| 7 | Opens Need help now in the middle of an exercise | Panel opens over the exercise; exercise pauses; pause time is not counted | Paused 3.08 s, saved separately from the 6.9 s of exercise time | [07](07-crisis-panel-during-exercise.png), session 3 timing |
| 8 | Closes the panel | Back in the same exercise, same place | As expected | [08](08-exercise-after-crisis-panel.png) |
| 9 | Taps Stop | Neutral "You stopped. That's fine." screen; saved as `stopped`, never as a failure | As expected | [09](09-stopped.png), session 3 |
| 10 | Ground reset, tapping a dot for each thing noticed | One sense per screen, no typing, auto-moves on when all dots are filled | As expected | [10](10-ground-feel-2-of-4.png), session 4 |
| 11 | Returns home after finishing resets | "Your usual" appears, based on what was finished most | Shows "Your usual: Breath reset" | [11](11-home-your-usual.png) |
| 12 | Opens Journal | Short explanation that it is not a therapist; optional starter prompts | As expected | [12](12-journal-empty.png) |
| 13 | Writes about a bad long run, then "this training block is killing me" | Calm, non-judgmental replies; sports slang does not open the crisis panel | Two replies, no crisis flag | [13](13-journal-conversation.png), messages 4 to 7 |
| 14 | Writes "I don't want to be alive anymore" | Crisis panel opens at once; the model is not called; a fixed message is shown and saved with `crisis_flag = 1` | As expected; no `llm_calls` row for that message | [14](14-journal-crisis-input-panel.png), [15](15-journal-crisis-message.png), messages 8 and 9 |
| 15 | Model fails (switched to `fail` in Prototype tools), then writes in Journal | Fallback reply, words still saved; Need help now still works | Fallback shown and saved with `source = fallback`; failures logged in `llm_calls` | [16](16-model-failed-fallback-and-crisis-panel.png), [17](17-model-failed-fallback-reply.png), calls 13 to 15 |
| 16 | Opens History | Resets show Done or Stopped and length; journal entries show their first line | As expected | [18](18-history.png) |
| 17 | Opens a saved journal entry | The conversation is shown read-only | As expected | [19](19-history-journal-entry.png) |
| 18 | Backend is stopped, user reloads and opens Need help now | Panel still opens, because it is static content | As expected; home also says the server can't be reached | [20](20-backend-down-crisis-panel-works.png) |
| 19 | Backend is stopped, user starts a Breath reset | Exercise still runs with built-in steps and says it isn't being saved | As expected | [21](21-backend-down-exercise-still-runs.png) |

## Behavior checks (should hold in every case)

1. Need help now is visible and works on every screen, including inside exercises, after a model failure, and with the backend stopped. Evidence: screenshots 07, 16, 20.
2. Crisis-related journal text never reaches the model. Evidence: screenshot 14, the `llm_calls` table has no row for message 8, and `test_crisis_text_never_reaches_model`.
3. Stopping is always possible and saved as `stopped`. Evidence: screenshot 09, session 3, `test_stopped_session_is_saved_as_stopped`.

## Measured exercise duration

Measured in the browser with `performance.now()` from the first exercise instruction to the end of the final planned step, then saved in `sessions.timing_json`.

| Run | Planned | Measured active time | Paused (crisis panel) | Notes |
|---|---|---|---|---|
| Breath reset, hold (session 1) | 66.0 s | 66.013 s | 0 s | No network calls inside the exercise, so no app delay was added |
| Breath reset, mic (session 2) | 66.0 s | 66.014 s | 0 s | Same |
| Ground reset (session 4) | 55.5 s | 19.7 s | 0 s | The test tapped every 0.9 s, much faster than a person. The 55.5 s plan assumes 2.5 s per item plus 3 s to read each sense; at 4 s per item it is about 78 s |

Entry time (home, then the setup screen, then Start) is not included. In the hold run it was under 1 s because the test clicked immediately; for a person I estimate 3 to 5 s.

## Failure found during this run

In session 1, the Done screen showed the fallback line ("That's the reset. Take your time.") even though the model was in mock mode and nothing failed. The `messages` table showed `source = fallback`, while `llm_calls` showed the mock call succeeded. So the problem was after the call, in the output filter. One of my own mock closing lines said "Nothing else you need to do", and the filter blocks "you need to" in short lines. The filter worked as designed, but my mock text broke my own rule. I changed the line and added `test_every_mock_line_passes_the_output_filter`, so this can't come back without a failing test.

## What this evidence does not show

- No live model calls. I don't have an API key yet, so the live path in `backend/app/llm.py` has not been run. All replies here are mocks.
- The microphone test used a simulated sound injected into the page, not a real microphone. Real rooms, real mics, and quiet breathers are untested.
- Only Chromium was tested.
