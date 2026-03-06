# Future Memories

This directory contains **verbose running notes** written by AI agents during
development sessions. They serve as a durable plan-and-intent record that can be
used to restore context if a session is interrupted, times out, or needs to be
resumed by a different agent instance.

## How It Works

1. **Before mutating code**, the agent commits a plan file here (e.g.,
   `v0.9.0-plan.md`) describing what it intends to do, the full task list,
   architectural decisions, and any context from the user.
2. **During implementation**, the agent may update the plan file or add
   supplementary notes as it progresses, committing iteratively.
3. **After completion**, the plan file is archived into `archive.tar.gz`
   (which always contains the full history of all prior plans), and the
   raw markdown file is removed from the working tree.

## Archival Strategy

- `archive.tar.gz` is **rebuilt** (not appended) each time to contain the
  complete history of all archived plan files.
- The old `archive.tar.gz` is replaced in-place, so git only ever has **one
  archive file at HEAD** -- no trail of orphan zip/tar files in git history.
- Raw plan files remain in the working tree while the version is in-progress.

## Caveats on Content Quality

These files may contain:

- **Typos and autocomplete artifacts** from mobile keyboard input
- **Speech-to-text transcription errors** from voice dictation
- **Ambiguous or exploratory language** -- the user has noted that they
  sometimes work through ideas on the fly, and the language itself may be
  rough or in need of refinement
- **Verbose, stream-of-consciousness notes** -- this is intentional; future
  memories are meant to be detailed enough for full context restoration

Sensitive information (API keys, credentials, personal data) is scrubbed
with `[REDACTED: <reason>]` markers before committing.

## Relationship to Session Logs

| Aspect | `future_memories/` | `session_logs/` |
|---|---|---|
| **Timing** | Written *before and during* work | Written *after* work |
| **Purpose** | Plan, intent, restoration context | Audit trail, test results |
| **Tone** | Verbose, speculative, exploratory | Factual, structured |
| **Mutability** | Updated iteratively during session | Append-only per turn |

Both directories use the same archival strategy (single `archive.tar.gz`
containing full history, no orphan files).
