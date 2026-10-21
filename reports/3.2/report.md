# Assignment 3.2: Working Application and Safety Report

Fernanda Garza

Repository: https://github.com/ferrgarzaa/reset-skills-prototype
Submitted commit: see the copy of this report submitted on Canvas

Reset is a class prototype. It isn't a mental health tool or therapy, nobody monitors it, and I only tested it with made-up scenarios.

## Links

- [Verification evidence](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.2/README.md) with the screenshots, the scenarios I tested, and the timing results
- [Database output](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.2/db-inspection.txt) and [test results](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence/3.2/pytest-results.txt)
- [What changed in the design for 3.2](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md#12-changes-in-part-32)
- [Journal system prompt](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/backend/app/prompts/journal_system.md)
- [Evidence log](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence-log.md)
- [README](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/README.md), [AGENTS.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AGENTS.md), and [AI-USE.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AI-USE.md)
- I didn't make a recording for this part. The screenshots and the database output are my evidence.

## What works now

The app runs on localhost with Vue, FastAPI, and SQLite, and you can finish both skills from the interface. In the Breath reset, a circle grows for 4 seconds and shrinks for 6, six times, with a countdown. In the Ground reset, you see one sense at a time and tap a dot for each thing you notice, so there's nothing to type. I also added a Journal where a companion replies to what you write, and a History page where you can see your past resets and reopen old journal entries. The "Need help now" button stays at the top of every screen.

## What I changed after talking to my instructor

After 3.1, my instructor gave me a few ideas: have the app notice when you're breathing, add a journaling chatbot with a long and careful system prompt, add modes, let people talk instead of type, and try drawing with the vision API. I couldn't do all of that well in one week, so I picked two for this part.

The first one is breath sensing. Before the Breath reset starts, you choose how to follow along: just the circle, the microphone, or pressing and holding the circle. With the microphone, the app listens to the room for the first 3 seconds and then listens for the sound of breathing out. With press and hold, you hold the circle while you breathe in and let go when you breathe out. When your breath matches, a small "with you" shows up. I added the hold option for people who don't want to turn on their mic. I also never show a count at the end, like "5 of 6," because that would feel like a score, and D3 says being asked to perform is part of the emotional cost. The sound is only checked inside the browser and is never recorded or saved, and the screen says so, because the app can't seem like it's watching anyone.

The second one is the Journal. A chatbot asks people to type and talk about their feelings, which is exactly the kind of effort D3 warns about. That's why I kept it as its own optional space on the home screen instead of putting it inside the exercises. It has a few optional prompts to help people start and an "I'm done" button. The system prompt is about 170 lines long. It turns the D6 findings into rules (no clinical words, no cheerful phrasing, no "you should"), keeps replies to a few sentences, only suggests the app's own two skills, and includes real resources like 988 and the Crisis Text Line. To personalize without making anyone fill out a profile (D5), the companion sees how many resets you did this week and how your last three entries started. If you don't want that, you can turn it off with a checkbox.

I left voice and drawing for 3.3. With voice, I want to be careful, because a voice that sounds like a real person could make the app feel like therapy. With drawing, I still need to figure out whether getting comments on a drawing would make people feel judged.

## What the AI does and where I limited it

The model writes the welcome line on the home screen, a short line after each reset, and the Journal replies. My code controls everything else: the steps, the timing, the Stop button, the crisis panel, and what gets saved. Every reply also goes through a filter in my code. If the model uses clinical words, says it's a therapist, or suggests anyone is watching, the reply gets swapped for a pre-written line. If the model doesn't answer in time (3 seconds for short lines, 12 for the Journal), the app shows a pre-written line too.

One important thing: everything I tested for this part uses mock replies, which are pre-written answers that stand in for the model. I don't have an API key yet, so I haven't run the live model. The code for it is ready, it stops after 50 calls, and the database keeps a record of every call and any error.

## What my evidence shows

The data is saved in SQLite. After my test run, the database had 7 sessions (two finished breath resets, one stopped breath reset, one finished ground reset, and three journal conversations), 11 messages, and 15 model calls. Each message shows where it came from, whether that's the user, a mock reply, a fallback line, or the fixed crisis message.

The timing matches my plan. I measured the Breath reset from the first instruction to the last step, and it took 66.01 seconds both times, against a planned 66. No network calls happen during the exercise, so the app didn't add any delay. When I opened the crisis panel in the middle of an exercise, the exercise paused, and the 3 seconds I spent in the panel were saved separately. The Ground reset is planned at 55.5 seconds, or about 78 if someone takes 4 seconds per item. My test only took 19.7 seconds because the script tapped much faster than a real person would. Opening the app and choosing a skill is counted separately.

The crisis button always worked. It opened inside an exercise, after I made the model fail on purpose, and even with the backend turned off completely (screenshots 07, 16, and 20).

Crisis-related messages never reach the model. When I wrote "I don't want to be alive anymore" in the Journal, the crisis panel opened right away, a fixed message appeared, and the database shows the model was never called. Sports expressions like "this training block is killing me" didn't set it off.

The app handles failures. When I set the model to fail, the home screen and the Journal both used their backup lines, and the message I wrote was still saved. With the backend turned off, the exercises still ran and just said they weren't being saved.

Leaving is easy and costs nothing. Pressing Stop shows "You stopped. That's fine." and saves the session as stopped. In the Journal, "I'm done" takes you back home.

All 20 automated tests pass, using mock replies.

## A mistake I found

After my first full Breath reset, the last screen showed the backup line even though nothing had failed. The database showed that the mock reply came through fine but was saved as a fallback, so I knew the problem was in my filter. It turned out one of my own pre-written lines said "Nothing else you need to do," and my filter blocks "you need to." The filter was doing its job, and the line was the problem. I changed the line and added a test that checks every pre-written line against the filter, so this can't happen again without a test failing. The evidence log has this and two other things I had to fix while testing.

## What's still unfinished

- Trying the live model, once I have an API key
- Voice and drawing, planned for 3.3
- Testing breath sensing with a real microphone, since my test used a simulated breathing sound
- Testing in browsers other than Chrome
- Making the crisis phrase list bigger and finding a fair way to test what it misses. One phrase it misses ("I just want to disappear for good") is saved as a test so I don't forget about it.
- Looking at other breathing and grounding apps for ideas
- The full evaluation with 15 scenarios, planned for 3.3
