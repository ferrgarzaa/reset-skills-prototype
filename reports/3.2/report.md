# Assignment 3.2: Working Application and Safety Report

Fernanda Garza

Repository: https://github.com/ferrgarzaa/reset-skills-prototype
Submitted commit: see the copy of this report submitted on Canvas

This is a coursework prototype. It is not a mental health tool and does not provide therapy, no one monitors its use, and it is tested only with fictional scenarios.

## Links

- [Verification evidence](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.2/README.md): 19 scenarios with expected and observed results, 21 screenshots, behavior checks, and measured timing
- [Database inspection](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.2/db-inspection.txt) and [test results](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.2/pytest-results.txt)
- [Design notes, section 12: changes in 3.2](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md#12-changes-in-part-32)
- [Journal system prompt](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/backend/app/prompts/journal_system.md)
- [Evidence log](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence-log.md)
- [README with run instructions](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/README.md), [AGENTS.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AGENTS.md), [AI-USE.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AI-USE.md)
- Recordings: none for this milestone. The screenshots and database output serve as the evidence.

## What I built

Reset now runs on localhost with Vue, FastAPI, and SQLite. A person can complete both skills from the running interface.

- **Breath reset:** a circle grows for 4 seconds and shrinks for 6, six times, with a countdown. Before starting, the person can choose to follow along with just the circle, the microphone, or press and hold.
- **Ground reset:** one sense per screen, and the person taps a dot each time they notice something instead of typing it.
- **Journal:** a separate, optional space where a journaling companion replies briefly. It uses a system prompt of about 170 lines and gets short context from what the person already did in the app.
- **History:** lists every reset (Done or Stopped, with length) and every journal entry, which can be opened and read. There is a button to clear everything.
- **Need help now:** in the header of every screen. It opens crisis resources that are built into the page.

## Changes after meeting with my instructor

My instructor suggested several ideas: letting the app notice that you're breathing, a journaling-style chatbot with a long and careful system prompt, modes, voice, and drawing with vision feedback. I chose two for this part.

**Breath sensing.** I added two optional ways for the app to follow along. With the microphone, the browser learns the room's background sound during the 3-second intro and then listens for a breath-out sound during each exhale. With press and hold, the person holds the circle while breathing in and lets go while breathing out. When a breath matches, a soft "with you" appears. I kept "just the circle" as an option (R4), and I never show a count afterward, because a score would add pressure (D3). The microphone sound is analyzed only in the browser and is never recorded or sent, and the screen says so, since the app must not seem to monitor anyone.

**Journal mode.** A chatbot asks people to type and share feelings, which is the emotional cost that D3 warns about. For that reason, I kept the Journal outside the exercises as its own optional space, with optional starter prompts and an "I'm done" button. The system prompt turns the D6 findings into concrete rules (no clinical words, no cheerful phrasing, no "you should"), keeps replies to two to four sentences with at most one question, offers only the app's own two skills, and lists real resources such as 988 and the Crisis Text Line. For personalization without setup (D5), the companion sees how many resets the person finished this week and the first lines of their last three entries. A checkbox in the Journal turns the second part off.

I left voice and drawing for Part 3.3. I want to test voice carefully, because a voice that sounds like a person could make the app feel like therapy. I also still need to decide whether drawing with model feedback would feel like being judged.

## What the model contributes, and its limits

The model writes the opening line on the home screen, the closing line after a reset, and the Journal replies. The skill steps, timing, Stop button, crisis panel, and saved data are all controlled by my code. Every reply passes through a filter in code that blocks clinical words, therapist claims, and monitoring language, and replaces the reply with a fixed line if it breaks those rules. Short lines time out after 3 seconds and Journal replies after 12, and any error leads to a fixed fallback line.

All evidence for this part uses **mock replies**. I don't have an API key yet, so the live path has not been run. The code for it is in place (`LLM_MODE=live`), it is capped at 50 calls per server run, and the `llm_calls` table records every call, its mode, and any error.

## What the evidence shows

**Persistence in SQLite.** After the browser run, the database contained 7 sessions (2 completed breath resets, 1 stopped breath reset, 1 completed ground reset, and 3 journal conversations), 11 messages with their source (`mock`, `fallback`, `static`, or `user`), and 15 logged model calls. The Journal conversation can be reopened from History.

**Measured duration.** Measured in the browser from the first exercise instruction to the end of the last planned step, the Breath reset took 66.013 and 66.014 seconds against a 66-second plan. There are no network calls during the exercise, so the app added no delay. When the crisis panel was opened during an exercise, the exercise paused, and the 3.08 seconds spent in the panel were saved separately from the exercise time. The Ground reset is planned at 55.5 seconds (about 78 seconds at 4 seconds per item). The test run took 19.7 seconds because the script tapped much faster than a person would. Entry time is reported separately.

**Independent crisis route.** The Need help now panel opened inside an exercise, after the model was switched to fail, and with the backend completely stopped (screenshots 07, 16, and 20).

**Crisis-related input.** When the Journal received "I don't want to be alive anymore," the crisis panel opened immediately, a fixed message was shown, both messages were saved with `crisis_flag = 1`, and the `llm_calls` table shows the model was not called. Sports expressions such as "this training block is killing me" did not trigger it.

**When a request fails.** With the model set to fail, the home screen used its fallback line, and the Journal showed "I'm having trouble replying right now. Your words are saved here," while still saving the person's message. With the backend stopped, the exercises still run with built-in steps and say they are not being saved.

**When the user leaves.** Stop leads to "You stopped. That's fine." and saves the session as `stopped` with the number of steps completed. "I'm done" in the Journal returns home and closes the session.

**Automated tests.** Twenty tests pass, all with mock replies. They cover fixed steps and timing, persistence, "Your usual", crisis input never reaching the model, sports expressions, model failure, memory turned off, clearing history, and the output filter.

## A failure I found

After the first full Breath reset, the Done screen showed the fallback line even though nothing had failed. The database showed that the mock call succeeded but the saved message had `source = fallback`, so the problem was in my output filter. One of my own mock lines said "Nothing else you need to do," and the filter blocks "you need to." I kept the filter, changed the line, and added a test that every mock line must pass the filter. The full account is in the evidence log, along with two other revised approaches from testing.

## What remains unfinished

- Live model testing, which requires an API key
- Voice input and output, and the drawing idea (planned for 3.3)
- Testing breath sensing with a real microphone in real rooms. The test used a simulated sound injected into the page.
- Testing in browsers other than Chromium
- A larger crisis phrase list and a fair way to test what it misses. One known miss ("I just want to disappear for good") is kept as a test so the limit stays visible.
- The UI research review of existing breathing and grounding apps
- The full evaluation with fifteen scenarios and live-model variation (Part 3.3)
