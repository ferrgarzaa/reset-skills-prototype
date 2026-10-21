// Frontend copy of the backend crisis phrase list (backend/app/safety.py).
// Lets the crisis panel open right away, even if the backend is down.
// Same limits: misses indirect wording and typos.
const PATTERNS = [
  /\bsuicid\w*/,
  /\bkill(ing)? my ?self\b/,
  /\bend(ing)? (my|it) (life|all)\b/,
  /\bend it all\b/,
  /\btake my (own )?life\b/,
  /\bwant(ed)? to die\b/,
  /\bwish i (was|were) dead\b/,
  /\bbetter off (dead|without me)\b/,
  /\bno reason to (live|go on|keep going)\b/,
  /\bdon'?t want to (live|be alive|be here anymore|wake up)\b/,
  /\bcan'?t go on\b/,
  /\bself[- ]?harm\w*/,
  /\bhurt(ing)? my ?self\b/,
  /\bcut(ting)? my ?self\b/,
  /\boverdos\w*/,
  /\bnot safe (right now|with myself)\b/,
]

export const CRISIS_MESSAGE =
  "It sounds like things are really heavy right now. This app can't help in a crisis, " +
  "but people can. The crisis options are open on your screen. You can call or text 988 " +
  "any time, or call 911 if you're in danger. Your words are saved here, and you can come " +
  'back whenever you want.'

export function crisisMatch(text) {
  const t = text.toLowerCase().replace(/[‘’]/g, "'")
  return PATTERNS.some((p) => p.test(t))
}
