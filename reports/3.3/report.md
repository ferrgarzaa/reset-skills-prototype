# Assignment 3.3: Integration, Evaluation, and Demonstration Report

Fernanda Garza

Repository: https://github.com/ferrgarzaa/reset-skills-prototype
Submitted commit: see the copy of this report submitted on Canvas

Reset is a class prototype. It isn't a mental health tool or therapy, nobody monitors it, and I only tested it with made-up scenarios and fictional users.

## Links

- [Demo video](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.3/videos/demo.mp4) (about 3 minutes, sections labeled on screen)
- [Process screencast](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.3/videos/process.mp4) (about 80 seconds: one failure, the evidence, my decision, and an explanation of generated code)
- [Evaluation](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.3/README.md): 22 scenarios with expected and observed results, 4 behavior checks, screenshots, the surprising finding, and the untested limitation
- [Database after the evaluation](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.3/db-inspection.txt), [test results](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.3/pytest-results.txt), and the [clean checkout check](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.3/clean-checkout.txt)
- [Design notes](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md), especially [section 14: what changed since 3.1](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md#14-looking-back-what-changed-since-part-31-and-why)
- [Evidence log](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence-log.md), [README](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/README.md), [AGENTS.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AGENTS.md), and [AI-USE.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AI-USE.md)

## What the finished app does

Reset runs on localhost with Vue, FastAPI, and SQLite. It has two short skills, a Breath reset (in for 4, out for 6, six times) and a Ground reset (5-4-3-2-1, tapping instead of typing), plus a Journal with a journaling companion. The "Need help now" button stays in the header of every screen.

Since 3.2, I added the pieces that connect everything to the person using the app:
- An optional one-tap check-in on the home screen: Wound up, Scattered, Low, or Okay. "Wound up" narrows the screen to one suggestion, "Scattered" puts the Ground reset first, and "Low" puts the Journal first. The person can always tap Change, Clear, or Show all options.
- A "You" page that shows everything the app keeps. That includes the two optional things the person typed (a name and something they enjoy) and what the app learned from use, like their usual reset, how many resets they finished or stopped, their recent check-ins, and how they like to follow the breathing. It also has a button that shows exactly what the companion is told.
- A companion that uses that information. It says the person's name once, offers their usual reset when they seem overwhelmed, and can mention what they wrote before, unless they turn that off.
- "Speak instead" in the Journal (speech recognition in Chrome and Edge, with the text shown before sending) and a Larger text setting.

## How my 3.1 plan changed

The biggest change was the model's role. In 3.1 it only wrote a line before and after each exercise. After my instructor's feedback, it became a full Journal. I kept the Journal outside the exercises so they stay short and simple (D2, R1).

The second change was the check-in. In 3.1 I decided against asking how someone feels, because D3 says being asked to feel or disclose is a cost. For the presentation I needed real information about the user's current state, so I added it in the lightest form I could think of: one optional tap, plain words, and an easy way to change it or turn it off. It also gave D1 something honest to work with. The app shows less when the person says they're wound up, instead of guessing.

I also decided against two of my instructor's ideas, at least for this project. I didn't build the drawing feature, because having a model comment on someone's drawing during a hard moment could feel like being judged (D3, D6), and I couldn't find a version that clearly helped. I didn't add a voice that talks back, because a human-sounding voice could make the app feel like therapy, which it must not claim to be. I did add voice input, since it lowers effort and keeps the person in control of what gets sent.

Section 14 of the design notes has the full table of changes.

## Evaluation

I tested 22 fictional scenarios in the real browser with a script that also checks the database after each step. There were 13 ordinary uses, 2 interruptions, and 7 failure cases, and all 22 passed. The 4 behavior checks also passed across all of them:
1. Need help now was visible on all 12 screens I checked, including inside exercises, with the model failing, and with the backend turned off.
2. Crisis-related text never reached the model. There were 4 Journal model calls for 4 normal messages, and 0 for the crisis message.
3. No reply shown to the user contained clinical words, therapist claims, monitoring language, praise like "great job", or an exclamation mark.
4. Every exercise is planned under 90 seconds and every finished run stayed under it. The Breath reset measured 66.008 and 66.004 seconds against a 66-second plan.

I also have 24 automated tests, all using mock replies. Two of them are new: one where the "model" returns a clinical label with an exclamation mark, which the app replaces with a fallback, and one that checks crisis messages never end up in later context. I also cloned the repository into a new folder and followed the README step by step. The backend, the tests, and the frontend all worked.

One scenario needs an honest note. S17 ("I just want to disappear for good") passes because my expected result was the known limitation: the phrase list doesn't catch indirect wording. The safety net there is the button, which is always visible, and the system prompt.

**Surprising finding:** my Ground reset plan was too cautious. I planned 55.5 seconds, but tapping at my planned pace of 2.5 seconds per item took only 42.1 seconds. The time I set aside for reading each prompt mostly disappears, because the next prompt shows up as soon as the last dot fills. A planned time is just a guess until you measure it.

**Limitation I have not tested:** I never tried the app with a screen reader. The breathing countdown updates every second, and I don't know if that is helpful or just noise when it's read aloud. I also haven't tested a real microphone in a real room, or browsers other than Chromium.

## Mocked replies and the live model

Every model reply in my evaluation and videos is a mock reply. I don't have an Anthropic API key, so I couldn't repeat cases with the live model as the assignment asks. I wrote `live_check.py` so it's ready. It sends 5 Journal inputs 3 times each (15 calls, under the 50-call limit), including one that asks for a diagnosis and one with indirect crisis wording, and records whether each reply was safe. Until it runs, my evidence shows that the app's code handles the model correctly (filtering, fallbacks, crisis routing, and context), but not how good the real model's replies are.

## The failure in my process screencast

After my first full Breath reset in 3.2, the last screen showed the backup line even though nothing had failed. The database showed that the mock call succeeded (`ok = 1`) but the message was saved with `source = fallback`, so the reply was being thrown away after the call. It turned out my own pre-written line said "Nothing else you need to do," and my filter blocks "you need to" in short lines. I kept the filter, changed the line, and added a test that checks every pre-written line against the filter. In the screencast I put the old line back for the recording only, so the failure, the database evidence, and the fix all happen on screen.

## Generated code I can explain

The code I explain in the screencast is the part of `journal_message()` in `backend/app/main.py` that handles crisis input. It was generated with Claude, and I checked it with tests. Before any model call, it runs `crisis_match()` on the person's text. If the text matches, it saves the person's message and a fixed crisis message, both marked with `crisis_flag = 1`, and returns right away. Since the function ends there, the model is never called for that message, and later context leaves flagged messages out. The tests `test_crisis_text_never_reaches_model` and `test_crisis_messages_never_enter_later_context` check this, and behavior check B2 confirms it in the browser run. Its limit is that it's only a list of phrases, so the crisis button never depends on it.

## What's still unresolved

- How the live model actually behaves, once I have a key
- A screen reader test, a real microphone test, and tests in other browsers
- Whether the endurance-sport "reset" idea works for people who don't care about sports
- Whether the check-in mappings (Wound up to breathing, Scattered to grounding, Low to the Journal) fit real people. They're my assumptions, not research findings, which is why the user can always change them.
