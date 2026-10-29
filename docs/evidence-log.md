# Evidence Log

I picked these entries myself and left out anything personal. There are no keys or passwords in here.

## Part 3.1

### Oct 13: Class discussion
I talked with Meshal Alqufaidi, Emad Zamzami, Rayan Alanazi, and Henry. We agreed that D3 and D2 were the clearest rules to follow, and that crisis access and the skill steps should be in the code, not left to the AI. We also weren't sure about using click behavior to guess distress for D1, because it could be wrong a lot and might feel like being watched. That's a big reason why I kept the AI's role small and didn't try to detect distress.

### Oct 14: Planning with Claude
Before writing anything, Claude asked me a few questions. My answers were:
- skills: breathing and grounding
- AI: Anthropic's Claude, same as the RAG activity
- crisis: a button that's always visible, plus a keyword check in my code
- what the AI does: only short lines before and after
- reuse: starting from scratch

### Something I changed: how you pick a skill
At first the options were a one-tap "how are you feeling?" check-in that suggests a skill, or starting with a chat where the AI suggests one. I didn't pick either. I asked to bring in my love of sports instead, and ended up with two buttons plus "Your usual". A mood check-in asks people to rate how they feel (D3), and letting the AI choose takes control away from the user (R4).

### Something else I changed: the sports idea
I first wanted the app to feel sporty and energetic. Then I realized coach-style hype goes against D6 (cheerful language felt condescending) and D3 (being asked to perform is part of the emotional cost), and that scores or streaks would add pressure. So I changed it to a calm reset idea based on my endurance racing (marathons, ultramarathons, triathlon, Hyrox), where sports only shows up in the concept of pacing and resetting. There are no scores, streaks, or hype.

### What I want to try in 3.2
- Time the breathing circle with real timestamps (my estimate is about 66 seconds).
- Run athletic expressions like "this workout is killing me" through the crisis keyword list to see how many false alarms I get.

## Part 3.2

### Oct 20: Meeting with my instructor
My instructor suggested: letting the app notice that I'm breathing, a journaling-style chatbot with a long system prompt that uses real resources and never judges, modes, talking instead of typing, and something interactive with the vision API, like drawing. I picked breath sensing and the Journal for 3.2, and left voice and drawing for 3.3 so I could build fewer things well. For breath sensing I wanted both a microphone option and press-and-hold, because some people won't want to turn on their mic.

### Tension I had to resolve: a bigger chatbot vs. D2 and D3
A chatbot asks people to type and share feelings, which is the emotional cost D3 warns about. So I kept the Journal as its own optional space on the home screen, outside the exercises, with optional starter prompts and an "I'm done" button. The exercises themselves didn't change.

### Failure found: my own mock line was blocked by my own filter
- **What happened:** after the first full Breath reset in the browser, the Done screen showed the fallback line, even though the model was in mock mode and nothing had failed.
- **Evidence:** in the database, `messages.source` was `fallback` for that closing line, but `llm_calls` showed the mock call succeeded (`ok = 1`). So the problem happened after the call. The mock line "Nothing else you need to do" contains "you need to", which `clean_reply()` blocks for short lines.
- **Decision:** I kept the filter and changed the line, then added a test that checks every mock line passes the filter.

### Revised approach: testing the microphone
- **First try:** a generated audio file played through Chromium's fake microphone, with quiet inhales and noisy exhales. It passed once and failed the next time. The file loops on its own clock, so the noise didn't always line up with the exhales, and once the room calibration happened during the noise.
- **Revised to:** the test script replaces the microphone with generated noise that it switches on during each exhale. That makes the test repeatable. It is still a simulation, and a real microphone is untested.

### Revised approach: stopping the backend during the test
The first version of the test stopped the backend with `pkill -f "uvicorn app.main:app"`. That pattern also matched the shell command running the test, so it stopped the test itself. I changed it to stop the exact process ID saved when the backend started.

### Small bug: timing log started in the wrong phase
In one run, the phase log for the Breath reset started with "close" at 0 ms. The first animation frame's timestamp can be slightly earlier than the start time, which made the elapsed time negative for one frame. I clamped the frame time to zero or more. The measured total was not affected (66.013 s).

### Results
- 20 automated tests pass, all with mock replies.
- Breath reset measured at 66.01 s against a 66 s plan, in two runs.
- Crisis panel worked inside an exercise, after a model failure, and with the backend stopped.
- No live model calls yet, because I don't have an API key.

## In-class presentation (Oct 29)

### Checking the app against the presentation rubric
I compared the app to the four presentation criteria. Skill walkthrough and chatbot tone were already covered. "User state and interface adaptation" and "user persona over time" were weak: the app only used history ("Your usual") and never asked anything about right now, and there was no place showing what is saved.

### Decision: an optional check-in, after deciding against it in 3.1
In 3.1 I decided against a mood check-in because rating feelings is an emotional cost (D3). The rubric asks for user state, so I added one, but kept it to a single optional tap with plain words, a clear "skip", and Change/Clear/Show all options. I think this keeps the cost low while still letting the screen adapt (D1) without guessing.

### Bug found: rule order in the mock replies
A test message "I feel overwhelmed before my race" got the training reply instead of the overwhelmed reply, because "race" matched the training rule first. I moved the overwhelmed rule to the top so the more important match wins, and the new test `test_mock_journal_reply_uses_profile` covers it.

### Results
22 automated tests pass (mocked). Screenshots of the new features are in `docs/evidence/presentation/`.
