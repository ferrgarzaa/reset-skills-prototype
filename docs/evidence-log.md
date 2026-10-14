# Evidence Log

Curated and redacted. No credentials, personal info, or research-participant info.

## Part 3.1

### 2026-10-13: In-class ideation discussion
Group discussion (Meshal Alqufaidi, Emad Zamzami, Rayan Alanazi, Henry, me). We agreed D3 and D2 were the clearest constraints and that crisis access and the skill steps should live in code, not the prompt. We worried about detecting distress for D1 using click behavior (false positives, feels like monitoring). → Basis for keeping the model small and not inferring distress.

### 2026-10-14: Design session with Claude (claude.ai)
Claude asked me a set of multiple-choice questions before drafting. My answers:
- Skills: breathing + grounding.
- Model provider: Anthropic (Claude), same as the RAG activity.
- Crisis: always-visible static button + keyword check in code.
- Model role: short lines before/after only.
- Reuse: starting clean.

### Revised approach 1: how the user picks a skill
- **First options considered:** a one-tap "how are you feeling" check-in that suggests a skill, or a chat-first entry where the model suggests a skill.
- **Revised to:** two buttons plus "Your usual". Instead of those options, I asked to bring my interest in sports into the app.
- **Why:** a mood check-in asks the user to rate their feelings (D3), and a model choosing the skill takes control away (R4).

### Revised approach 2: sports framing
- **First idea:** make the app feel like sports.
- **Problem found:** coach-style or motivational language conflicts with D6 (cheerful phrasing felt like condescension) and with D3 (being asked to *perform* is an emotional cost). Scores and streaks would also add pressure.
- **Revised to:** a calm "reset between plays" concept: sports in the names and framing only, with no scores, streaks, or hype.

### Planned experiments for 3.2
- Time the breathing cue with real timestamps (target ≈ 66 s).
- Run sports-slang phrases ("this drill is killing me") through the crisis keyword list to measure false positives.
