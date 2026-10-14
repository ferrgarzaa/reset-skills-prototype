# Assignment 3.1: Research and Design Report

Fernanda Garza

Repository: https://github.com/ferrgarzaa/reset-skills-prototype
Submitted commit: see the copy of this report submitted on Canvas

This is a class prototype. It's not a mental health tool or therapy, nobody is monitoring it, and I'm only testing it with made-up scenarios.

## Links

- [Design notes](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md): flow diagram, screen sketches, how each decision connects to the findings, the AI's role, crisis access, timing, data, and open questions
- [Evidence log](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence-log.md)
- [README](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/README.md), [AGENTS.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AGENTS.md), [AI-USE.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AI-USE.md)
- No recordings for this part

## My idea

My app is called Reset. I'm really into sports, and athletes do this all the time: you have a bad play, you take a few seconds to reset, and you keep going. I wanted the app to feel like that. It has two short skills, a Breath reset (breathing in for 4 and out for 6) and a Ground reset (5-4-3-2-1 grounding, but you tap instead of typing).

I had to be careful with the sports part though. My first thought was to make it feel energetic, but D6 says cheerful language felt condescending to participants, and D3 says being asked to perform is part of the emotional cost. So there are no scores, streaks, or "let's go!" type messages. The sports idea is just in the name and the feeling of taking a quick reset.

## Main decisions

I picked breathing and grounding because they ask the least from the person (D3) and both fit in under 90 seconds (R1). I left out the cognitive reframe because it needs a lot of thinking and typing, which felt like too much for someone who's already upset.

Every screen inside an exercise has one thing to do (D2). For grounding, that means one sense per screen, and you tap a dot each time you notice something instead of writing it down.

The user always chooses. The home screen has Breath, Ground, and once you've done one, a "Your usual" button (R4, D5). The app learns from what you've done before, so there's no settings page to fill out.

There's a Stop button on every exercise screen, and stopping just takes you to a calm screen that says it's fine (R3). It never says you "failed" or "quit".

The "Need help now" button is on every screen in the same spot. It shows crisis numbers (988, Crisis Text Line, 911) and it's built into the page, so it works even if the AI or the server is down (R2, D4).

For D1, the study doesn't say how an app would know someone's distress is going up, and I didn't want to guess. In class we talked about using click behavior, but it could be wrong a lot and it might feel like the app is watching you. So instead, the app just shows less the deeper you go. Home has a few options, and the exercise has almost nothing on it.

## What the AI does

Claude only writes a short line before and after the exercise, and replies once if the user writes an optional note at the end. The steps, the timing, the Stop button, the crisis panel, and what gets saved are all handled by my code, not the AI. The prompt tells it not to diagnose, give advice, sound like a coach, or act like someone's watching, and my code double-checks the reply. If the AI takes too long or says something it shouldn't, the app just shows a pre-written line and keeps going.

If someone writes something crisis-related in the note, a keyword check in my code catches it before anything is sent to the AI. The AI doesn't get called, a calm message shows up, and the crisis panel opens. The keyword list won't catch everything, and it'll probably flag sports slang like "this drill is killing me", but I'd rather open the info panel by mistake than miss something.

## What gets saved

SQLite stores each session (which skill, whether it was finished or stopped, how long it took, and an optional one-tap "how was it"), the messages, and the fixed exercise steps. The History page shows the date, skill, whether you finished, and how long it took. There's also a button to clear everything.

## Timing

The Breath reset takes about 66 seconds: a short intro, 6 breaths of 10 seconds each, and a short ending. The Ground reset takes around 56 seconds if someone takes 2.5 seconds per thing they notice, and around 78 seconds at 4 seconds each. Opening the app and picking a skill takes a few more seconds, which I'm counting separately. The exercise never ends someone on a timer.

## What's done and what's still open

Done: the design, the flow diagram and sketches, the decisions connected to R1 through D6, the AI's role, the crisis plan, the data plan, the timing estimates, and the project docs.

Still figuring out:
- whether the sports idea works for people who aren't into sports
- whether breathing should have a shorter option
- whether I should save the notes people write
- whether one AI reply is "conversational" enough
- how big the crisis keyword list should be and how to test it fairly
- looking at existing breathing and grounding apps for ideas

The full list is in section 10 of the design notes.
