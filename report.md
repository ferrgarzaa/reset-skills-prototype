# Assignment 3.1: Research and Design Report

Fernanda Garza

Repository: https://github.com/ferrgarzaa/reset-skills-prototype
Submitted commit: see the copy of this report submitted on Canvas

This is a coursework prototype. It is not a mental health tool and does not provide therapy, no one monitors its use, and it is tested only with fictional scenarios.

## Links

- [Design notes](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/design.md): flow diagram, screen sketches, decisions connected to the findings, the model's role, crisis access, timing, data, and open questions
- [Evidence log](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/docs/evidence-log.md)
- [README](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/README.md), [AGENTS.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AGENTS.md), [AI-USE.md](https://github.com/ferrgarzaa/reset-skills-prototype/blob/main/AI-USE.md)
- There are no recordings for this milestone.

## Concept

My application is called Reset. The idea comes from my own experience as an endurance athlete. I have run marathons and ultramarathons, and I also compete in triathlon and Hyrox. In those events, things rarely go perfectly. A difficult kilometer, a hard transition, or a station that goes worse than planned can throw you off. What helps is not pushing harder but taking a short moment to reset: slowing your breathing back to a steady rhythm, noticing what is around you, and then continuing. That habit of a brief, intentional reset is the core idea of this application.

The application offers two short skills. The Breath reset uses paced breathing (inhale for four counts, exhale for six), which is similar to how I control my breathing to settle back into a pace during a long race. The Ground reset uses 5-4-3-2-1 sensory grounding, which resembles the way I pay attention to my surroundings when a race feels overwhelming. In this application, the user taps to count what they notice instead of typing it.

I was deliberate about how much of the athletic framing to keep. Endurance sport is closely tied to performance, splits, and personal records, and the research points away from that. D6 reports that cheerful phrasing was experienced as condescension, and D3 identifies being asked to perform as part of the emotional cost. For this reason, the application has no scores, streaks, records, or motivational slogans. The athletic influence appears only in the concept of the reset and in its emphasis on pacing.

## Main design decisions

I chose breathing and grounding because they require the least effort from the user (D3) and both fit within 90 seconds (R1). I did not include the cognitive reframe because it requires reflection and typing that seem too demanding for someone who is already distressed.

Each screen within an exercise presents a single action (D2). In the Ground reset, this means one sense per screen, and the user taps a marker for each item they notice instead of writing it down.

The user always chooses what to do. The home screen offers the Breath reset and the Ground reset, and after the user completes one, it also offers a "Your usual" option (R4, D5). Personalization comes from the user's previous sessions, so there is no setup or settings page.

A Stop button is available on every exercise screen. Stopping leads to a neutral screen confirming that stopping is fine (R3), and the application never describes it as failing or quitting.

The "Need help now" button appears in the same position on every screen. It displays crisis resources (988, the Crisis Text Line, and 911) and is built into the page itself, so it works even when the model or the server is unavailable (R2, D4).

For D1, the study does not establish how a system would know that distress has increased, and I chose not to guess. During the in-class discussion, my group considered inferring distress from clicking behavior, but we were concerned that it could often be wrong and could make users feel monitored. Instead, the interface becomes simpler as the user moves further into the experience. The home screen shows a few options, and the exercise screens show almost nothing besides the exercise.

## Role of the model

Claude writes only a short line before and after each exercise, and a single reply if the user leaves an optional note at the end. The skill steps, the timing, the Stop button, the crisis panel, and the saved data are all controlled by the application code, not by the model. The system prompt instructs the model not to diagnose, give advice, use motivational language, or suggest that anyone is monitoring the user, and the application also checks each reply. If the model is slow or produces an inappropriate response, the application displays a pre-written line and continues normally.

If a user writes something crisis-related in the optional note, a keyword check in the application code detects it before anything is sent to the model. In that case, the model is not called, a calm pre-written message appears, and the crisis panel opens. The keyword list will not detect every case, and it may flag athletic expressions such as "this workout is killing me." I accept those false positives because the only consequence is that an information panel opens.

## Stored data

SQLite stores each session (the skill used, whether it was completed or stopped, its duration, and an optional one-tap rating), the messages, and the fixed exercise steps. The History page shows the date, the skill, whether it was completed, and its duration. Users can also clear their history with one button.

## Timing

The Breath reset takes approximately 66 seconds: a short instruction, six breaths of 10 seconds each, and a brief closing. The Ground reset takes approximately 56 seconds if the user spends 2.5 seconds on each item, and approximately 78 seconds at 4 seconds per item. Opening the application and choosing a skill take a few additional seconds, which I report separately. No timer ever ends the exercise for the user.

## Completed work and open questions

The following parts are complete: the design concept, the flow diagram and screen sketches, the decisions connected to R1 through D6, the model's role and limits, the crisis-access plan, the data model, the timing estimates, and the project documentation.

The following questions remain open:
- whether the athletic framing works for users who are not interested in sports
- whether the breathing exercise should include a shorter option
- whether the notes that users write should be saved
- whether a single model reply is conversational enough
- how large the crisis keyword list should be and how to test it fairly
- which existing breathing and grounding applications to review for interface ideas

The full list appears in section 10 of the design notes.
