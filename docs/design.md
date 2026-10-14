# Reset: Design Notes (Part 3.1)

This is a class prototype. It's not a mental health tool or therapy, nobody monitors it, and I only test it with made-up scenarios.

## 1. The idea

I'm a really sporty person, so I built the app around something athletes already do: after a bad play or a hard drill, you take a few seconds to reset and then keep going. The app has two short skills:

- Breath reset: paced breathing, in for 4 and out for 6
- Ground reset: 5-4-3-2-1 grounding, where you tap instead of typing

The sports part is only the framing. It shows up in the names, a couple of calm words like "reset", and the fictional people I'll test with. The actual steps of each skill don't change.

### Why I toned the sports part down

My first idea was to make it feel energetic, like a coach hyping you up. Then I looked at the findings again. D6 says cheerful phrasing felt condescending to participants, and D3 counts being asked to perform as part of the emotional cost. Sports apps usually have scores, streaks, and "new personal best!" messages, and that's exactly the kind of pressure this app shouldn't have. So:

- no scores, streaks, badges, or personal bests
- no hype or motivational messages
- stopping early is never called quitting or failing

What I kept is the idea that a reset is short and normal, and then you get back to your day. I still want to check whether this framing works for someone who doesn't care about sports (question 1 in section 10).

## 2. Main flow

```mermaid
flowchart TD
    A[Open app] --> B[Home: pick a reset]
    B -->|Breath reset| C[Breath: one screen, pacing circle]
    B -->|Ground reset| D[Ground: one sense per screen, tap dots]
    B -->|Your usual reset<br/>only after 1+ completed| E{Usual skill}
    E --> C
    E --> D
    C --> F[Done screen]
    D --> F
    C -.->|Stop, any time| G[Stopped screen: no consequence]
    D -.->|Stop, any time| G
    F --> H[Optional 1-tap check: Helped / Not sure / Not today]
    H --> I[Optional short note, one AI reply]
    F --> B
    G --> B
    B --> J[History]

    K[[Need help now: on every screen]] -.-> L[Crisis panel: built into the page, no AI]
    I -.->|keyword match on note| L
```

The "Need help now" button is in the same spot on every screen, including during an exercise and when the AI isn't working. It opens a panel that's part of the page itself, so it doesn't need the server or the AI.

## 3. Screen sketches

```
HOME                              BREATH RESET (during exercise)
+------------------------------+  +------------------------------+
| Reset          [Need help now]|  |                [Need help now]|
|                              |  |                              |
|  Take a short reset.         |  |            .---.             |
|  Stop whenever you want.     |  |          (       )           |
|                              |  |            '---'             |
|  [ Breath reset   ~1 min  ]  |  |        Breathe in... 3       |
|  [ Ground reset   ~1 min  ]  |  |                              |
|  [ Your usual: Breath     ]  |  |                              |
|                              |  |          [ Stop ]            |
|  History                     |  |                              |
+------------------------------+  +------------------------------+

GROUND RESET (one sense per screen) DONE
+------------------------------+  +------------------------------+
|                [Need help now]|  |                [Need help now]|
|  Notice 4 things you can feel|  |  That's the reset.           |
|                              |  |  <one short AI line>         |
|     ( * ) ( * ) ( ) ( )      |  |                              |
|   tap a dot each time you    |  |  How was it? (optional)      |
|   notice one, no need to     |  |  [Helped][Not sure][Not today]|
|   type what it is            |  |                              |
|                              |  |  [ Back to home ]            |
|   [ Next sense ]   [ Stop ]  |  |                              |
+------------------------------+  +------------------------------+
```

Home is the busiest the app ever gets, with two or three choices and a History link. During an exercise you only see the cue, Stop, and Need help now.

## 4. My decisions and why

| What I decided | Findings | What I give up |
|---|---|---|
| Only breathing and grounding | D3 (the emotional cost showed up mostly on breathing and grounding, and both can be done with almost no input), R1 | No STOP or reframe. The reframe needs thinking and typing, which doesn't fit D3 or 90 seconds. |
| One thing per screen, and grounding goes one sense at a time | D2 | Grounding becomes 5 screens instead of 1 list, so there are more transitions to time. |
| Tapping instead of typing in grounding | D3 | The app doesn't know what the person noticed, so the AI can't respond to it. That's on purpose. |
| Stop is on every exercise screen and takes you to a calm screen ("You stopped. That's fine."). It's saved as "stopped", never as a fail | R3 | Stopped sessions still show in history, but they're worded neutrally. |
| The user picks the skill. "Your usual" is an extra button, not something the app starts on its own | R4, D5 | It's one more tap than auto-starting, but the person stays in control. |
| Need help now is on every screen, built into the page, and works without the AI | R2, D4 | It takes up a bit of space everywhere, even during exercises. |
| The screen gets simpler based on where you are, not on guessing how you feel | D1 | The app never pretends to know how someone feels. |
| Soft colors, the only motion is the breathing circle, short plain sentences | D6 | It looks less "branded". The sports theme stays in the words, not in bright visuals. |
| The AI only writes short lines; the steps are written in my code | D6, assignment section 2 | The app is less chatty, but the AI can't change or make up the skill. |

## 5. D1 without guessing distress

D1 says the screen should show less as distress goes up, but the study doesn't say how an app would know that. I'm not trying to detect it. I thought about three options:

1. Guess from clicks or speed. This came up in our class discussion of the clicking-behavior study. I'm not doing it for now because it could be wrong a lot, it could feel like the app is watching you (the assignment says it can't seem like it's monitoring), and it takes the choice away from the user (R4).
2. Ask with one tap, like "How are you right now?". I'm not doing this either, because asking someone to rate their feelings is an emotional cost (D3).
3. Show less the deeper you go. This is what I chose. Each step into the experience has less on the screen, and the person decides how far to go.

What the app actually knows: which button you tapped, timing, whether you stopped, the optional one-tap answer, and the optional note. What it assumes: if you start an exercise, you want fewer things on screen. How you can change that: hit Stop or go home anytime.

## 6. What the AI does and doesn't do

I'm using Claude through the Anthropic API. The plan is `claude-haiku-5-5`, set in an environment variable so I can change it. Only the backend talks to the AI, never the browser.

What the AI does:
- one short line before an exercise (around 20 words max)
- one short line on the Done screen, which can mention which skill it was, whether it was your usual, or how many times you've done it
- one short reply if you write an optional note after a reset

What my code handles, not the AI:
- the steps of each skill, which are saved in a fixed table and never generated
- the timing of the breathing circle
- the Stop and exit buttons and where they go
- the Need help now panel
- what gets saved

The prompt also has rules, but they're a backup, not the main safety plan:
- don't diagnose, use clinical words, give therapy advice, or suggest new techniques
- no coach hype, exclamation marks, or emojis
- two sentences max
- never say or imply someone is watching or will check in
- don't claim to be a therapist

My code also checks each reply. If it's too long or uses words from a short blocked list ("diagnose", "disorder", "you should try"), it gets swapped for a pre-written line.

If the AI takes more than about 3 seconds or errors out, the app shows a pre-written line like "That's the reset. Take your time." and keeps working. The opening line loads while you're on the home screen, so it never slows down the exercise itself.

This works a lot like the hotel chatbot. There, the hotel info was the fixed context. Here it's the skill steps and your own history, and the AI just words things around that.

## 7. Crisis access

The Need help now button is in the header on every screen. It opens a panel that's part of the page:
- call or text 988 (Suicide & Crisis Lifeline, US)
- text HOME to 741741 (Crisis Text Line)
- call 911 for an emergency
- "This is a class prototype. It can't help in an emergency."

There's no server call, no AI, and no classifier involved, so it should work even with the backend turned off. That's one of the behavior checks I'm planning.

The only place someone can type is the optional note after a reset. Before that text goes to the AI, my backend checks it against a list of crisis-related words and phrases (the frontend has a copy too). If something matches:
- the AI doesn't get called
- a calm, pre-written message shows up and the crisis panel opens
- the person can close the panel and keep using the app, and nothing gets locked
- the message is saved with a crisis flag so I can test it, but it's not sent anywhere

Limits of the keyword list:
- it'll miss indirect wording or typos
- it'll flag some things it shouldn't, especially with sports slang like "this drill is killing me" or "I'm dead after practice"
- I'm fine with extra false alarms, because a false alarm only opens an info panel
- the app never calls it detection or monitoring

## 8. Timing

I'm measuring from the first exercise instruction to the last planned step. Opening the app and the Done screen are counted separately.

Breath reset:
- first instruction ("Follow the circle. In for 4, out for 6."): 3 s
- 6 breaths, 4 seconds in and 6 seconds out: 60 s
- ending ("Last breath out. That's it."): 3 s
- total: about 66 seconds, and there's no AI call during it, so no waiting on the network

Ground reset (assuming about 2.5 seconds to notice and tap each thing):
- intro: 3 s
- 15 things at 2.5 s each: 37.5 s
- 5 sense screens with about 3 s to read each one: 15 s
- total: about 56 seconds, or about 78 seconds if someone takes 4 seconds per thing, which is still under 90
- people can tap "Next sense" early, and nothing makes them find everything

Opening the app and picking a reset takes about 3 to 5 seconds, counted separately.

No timer ever ends the exercise or kicks someone out. If they take longer, the app just waits.

For 3.2, I want to try a small experiment: build only the breathing circle, record the real timestamps, and compare them to my 66-second estimate.

## 9. What gets saved and how it personalizes

It's one local user with no accounts. Nothing leaves my computer except the requests to the AI.

```
sessions
  id, started_at, ended_at, skill ('breath'|'ground'),
  status ('completed'|'stopped'), steps_completed, duration_s,
  feedback ('helped'|'not_sure'|'not_today'|NULL), was_usual (0/1)

messages
  id, session_id, role ('assistant'|'user'), content,
  source ('model'|'fallback'|'static'), crisis_flag (0/1), created_at

skill_steps          -- fixed script, loaded at setup, the AI never writes here
  skill, step_order, text, duration_s
```

How it personalizes without settings (D5):
- "Your usual" is whichever skill you've finished the most in your last 10 sessions. It only shows up after you've finished at least one.
- If you tapped "Not today" the last two times for a skill, it stops showing as your usual. I'm not sure yet if that's too much.
- The AI's closing line can mention it lightly, like "Your usual breath reset, done."

The History page is a simple list with the date, skill, whether you finished or stopped, and about how long it took. There are no streaks, charts, or scores, and there's a Clear history button that deletes everything.

What I give up: there's no settings page, so you can't, for example, change breathing to 5 rounds. Adding settings would be the kind of setup D5 says to avoid. I might come back to this.

## 10. Questions I still have

1. Does the sports "reset" idea help, or does it turn some people off? I want to test it with a fictional non-sporty person too.
2. Is 66 seconds of breathing right, or should there be a shorter option of about 40 seconds? R1 says around 60 felt comfortable.
3. Should the breathing circle have optional sound or vibration? Speech is optional for this assignment and would mean more browser testing.
4. Is hiding "Your usual" after two "Not today" answers helpful, or does it take control away?
5. How big should the crisis keyword list be, and how do I fairly test what it misses with made-up inputs?
6. Should I save the notes people write, or only keep them for that session? It's a trade-off between privacy and history.
7. Which breathing or grounding apps should I look at for the UI research step? I haven't done that yet.
8. Is one AI reply after the note enough to count as conversational, or do I need a short optional chat?

## 11. Reuse

I'm starting from scratch. I'll use the same stack and patterns from class (Vue, FastAPI, SQLite, a backend route that calls the AI, and saved conversation history like in the RAG activity), but I'm not copying code from A1, A2, or the RAG activity.
