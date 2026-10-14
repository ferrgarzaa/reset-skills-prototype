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
I first wanted the app to feel sporty and energetic. Then I realized coach-style hype goes against D6 (cheerful language felt condescending) and D3 (being asked to perform is part of the emotional cost), and that scores or streaks would add pressure. So I changed it to a calm "reset between plays" idea, where sports only shows up in the names and feel. There are no scores, streaks, or hype.

### What I want to try in 3.2
- Time the breathing circle with real timestamps (my estimate is about 66 seconds).
- Run sports slang like "this drill is killing me" through the crisis keyword list to see how many false alarms I get.
