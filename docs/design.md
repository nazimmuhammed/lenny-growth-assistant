# design.md --- Lenny Growth Assistant

## UI/UX principles

-   **Trust through visibility, not decoration.** The active LLM
    provider is always shown as a badge in the header (`OLLAMA` /
    `ANTHROPIC`), so the evaluator never has to guess which model
    produced an answer.
-   **Never hide a failure as if it were silence.** A slow/failed
    backend call surfaces as a visible error state in the chat thread,
    not an infinite spinner or a blank screen.
-   **Grounding is shown, not just claimed.** Every grounded answer that
    has supporting chunks displays clickable source chips (episode title
    → source URL) directly under the message, so the user can verify the
    claim against the original transcript.
-   **Insufficient context is a first-class UI state**, not an error.
    When `sufficient_context: false`, the message renders with a
    distinct warning treatment rather than looking identical to a
    confident answer.
-   **Chat and artifacts are peers, not a modal detour.** The Artifact
    Viewer sits in a permanent split-pane beside the conversation (like
    Claude's own Artifacts), so generating a document doesn't interrupt
    or navigate away from the conversation.

## Information architecture

Two-pane layout:

-   **Left (chat pane, \~55% width):** message history, input bar,
    session indicator
-   **Right (artifact pane, \~45% width):** artifact type selector
    (Markdown/HTML), instructions input, Generate button, rendered
    output

This split mirrors the mental model the client asked for explicitly
("similar to Claude Artifacts") --- conversation and output are
simultaneously visible, so a user can iterate ("generate a summary" →
read it → ask a follow-up → regenerate) without losing either context.

## Key interaction states

  -----------------------------------------------------------------------
  State                               Treatment
  ----------------------------------- -----------------------------------
  Session connecting                  Input disabled, footer reads
                                      "Connecting..."

  Session ready                       Footer shows short session ID for
                                      traceability during
                                      support/debugging

  Message sending                     Typing indicator (three animated
                                      dots) in the assistant's message
                                      slot

  Grounded answer                     Standard assistant bubble + source
                                      chips

  Insufficient context                Assistant bubble with a distinct
                                      warning border/color and an
                                      explicit "⚠ Limited grounded
                                      context for this answer" line

  Error (backend/provider failure)    Assistant bubble rendered as an
                                      error state with the underlying
                                      message, not a generic "something
                                      went wrong"

  Artifact empty                      Pane shows guidance text ("Chat
                                      first, then generate...") instead
                                      of an empty white box

  Artifact generating                 Explicit "Generating artifact..."
                                      state, not a frozen button

  Artifact ready (Markdown)           Rendered via `marked.js` into
                                      styled HTML inside the pane

  Artifact ready (HTML)               Rendered inside a sandboxed
                                      `<iframe>`, isolated from the
                                      parent page --- see
                                      `architecture.md` for the
                                      sanitization rationale
  -----------------------------------------------------------------------

## Responsive behavior

The current implementation targets desktop/laptop evaluation (the
primary expected evaluator context for this assignment). The two-pane
layout uses flex-based proportional sizing (`flex: 1.3` / `flex: 1`)
rather than fixed pixel widths, so it degrades reasonably on narrower
desktop windows.

Below a certain width, a follow-up iteration would stack the panes
vertically with a tab toggle instead of a permanent split --- noted as a
scope trade-off given the time-boxed nature of this build, not
implemented in this version.

## Accessibility considerations

-   Color is not the sole signal for state: the insufficient-context
    warning includes explicit text ("⚠ Limited grounded context"), not
    just a border color change.
-   Interactive elements (Send, Generate, source chips) are real
    `<button>`/`<a>` elements, not divs with click handlers, preserving
    keyboard/focus behavior and screen-reader semantics.
-   Input placeholder text doubles as inline guidance ("type 'ship30:
    `<topic>`{=html}' for an essay...") so the Ship30 skill's trigger
    phrase is discoverable without external documentation.
-   **Known gap:** no explicit `aria-live` region is set on the message
    list, so a screen reader won't automatically announce new assistant
    messages as they stream in --- flagged as a next-iteration
    accessibility improvement, not implemented in this time-boxed build.

## Design decisions and rationale

-   **No CSS framework/build step.** Given the deployment deadline, a
    single static HTML file with hand-written CSS was chosen over a
    bundled framework (Tailwind/Vite/etc.) to eliminate build tooling as
    a source of last-minute failure, while still allowing a genuinely
    polished look via custom CSS variables for theming (dark palette,
    consistent radii, accent colors).
-   **React via CDN, not a build pipeline.** Chosen specifically to keep
    real component structure and state management (`useState`,
    `useEffect`) without introducing `npm install`/bundler risk this
    close to the deadline --- documented explicitly as a deliberate
    trade-off, not an oversight.
-   **Dark theme by default.** Matches the tone of a technical/internal
    tool and reduces visual fatigue for an evaluator likely reviewing
    multiple submissions back-to-back.