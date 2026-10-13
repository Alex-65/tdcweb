"""ONE semantic authority per agent: the Claude agent file, from which the
Codex `.toml` twin is DERIVED.

THE DEFECT THIS OWNS WAS MEASURED, NOT HYPOTHESISED. A logical agent is
declared twice — once as `<name>.md` for Claude, once as `<name>.toml` for
Codex — and for as long as both copies were maintained by hand, the second
one drifted: ten of this repository's own eleven specialist pairs — the
corpus was eleven when that was measured on 2026-08-26, and is TEN today,
`fleet-problem-isolator` having been removed in `798a32c` — were
corrected on the Claude side and received ZERO commits on the Codex side, so
the Codex definitions still told a reviewer that "any remote write is out of
scope" long after typed remote mutation had shipped. Outside this repository
the same shape is worse: nineteen twins exist across the fleet, all in one
project, five of them already divergent, with nothing that detects it.

THE RULE. The Claude body is the authority. The Codex body is that body with
the CLOSED, ORDERED substitution list `AGENT_SUBSTITUTIONS` applied, and
nothing else. Two consequences, and both are the point:

  - a correction to the Claude source makes every twin derived from it
    change, so a stored twin that is not regenerated goes RED. Derivation is
    only load-bearing while that is true: an implementation whose parity
    check stays green after the source is mutated is COPYING, not deriving.
  - a substitution that stops matching its source text is a stale rule, not
    a no-op, and `substitution_incidence` exists so a caller can fail on it
    instead of silently deriving nothing.

WHAT THE LEGACY BODY CHECK DOES NOT COMPARE, and what replaced that gap.
`twin_diff` compares the body only. That was a decision when it was written
(two pairs carry a per-harness description a human wrote), and it became a
hole: the 2026-10-04 fleet-wide audit found three twins whose description was
stale against its Claude source while every check stayed green. The FULL
expectation is now `expected_twin_fields` below -- name, description AND body
-- and a description that legitimately differs is no longer exempted by the
comparison but REGISTERED as a `TwinAdaptation.description`, so it is data a
check can pass or fail. `fleetlib/twin_currentness.py` is the fleet-wide
consumer of that expectation. The triple-quote STYLE of the TOML block is
per-file and preserved as found.
`tools`/`tier`/`model`/`effort` exist only in the Claude frontmatter and have
no TOML counterpart; that absence is the declared harness difference, not a
gap this module may quietly fill.

WHAT THIS MODULE IS NOT. It does not discover projects, does not run git, and
does not know where agent definitions live: it is handed the texts, or the
individual files, it is asked about. `tools/codex_twin_render.py` owns
walking a directory pair, and a caller that wants a different corpus passes a
different pair. It imports neither `collector` nor `webapp`.
"""
import difflib
import hashlib
import pathlib
import re
import tomllib
from dataclasses import dataclass

#: The CLOSED, ORDERED list of substitutions applied to a Claude agent body to
#: derive the body its Codex twin must carry. Ordered because it is applied in
#: sequence and a later entry sees the earlier one's output.
#:
#: `CLAUDE.md -> AGENTS.md` is the kernel-file rename: the two bootstrap halves
#: of the project rules, one read by each harness.
#:
#: `Claude-side -> Codex-side` is the harness-identity rule, and it exists
#: because of a measured defect. With only the kernel rename, every OTHER word
#: had to be identical between the twins — including the phrase by which an
#: actor names WHICH HARNESS IT IS. `.codex/agents/fleet-security-reviewer.toml`
#: therefore told Codex, three times in its own effective instructions, that it
#: was an "ADDITIONAL Claude-side eye", while its own `description` said
#: Codex-side. A parity check without this entry did not merely miss that: it
#: REQUIRED it, because correcting the phrase in one twin would have been
#: reported as drift.
#:
#: PAIRWISE IDENTITY IS NOT CORRECTNESS. Two twins agreeing is agreement; the
#: thing they agree about still has to be true of each. Harness identity is the
#: one class that MUST differ, so it differs HERE, by a rule anyone can read,
#: rather than by an exemption that lets the bodies drift for unstated reasons.
#: `mcp__chrome-devtools__*` -> `mcp__chrome_devtools_attach__*` and
#: `mcp__plugin_playwright_playwright__*` -> `mcp__playwright__browser_*` are the same
#: harness-identity class as `Claude-side -> Codex-side`: an MCP tool namespace, not prose,
#: and the two harnesses spell it differently. Claude names an MCP tool
#: `mcp__<plugin>_<server>__<tool>`; Codex names it `mcp__<server>__<tool>`, and its own
#: attaching Chrome server is `chrome-devtools-attach` (declared in
#: `canonical/codex/baseline.yaml` and the operator's `~/.codex/config.toml`), which surfaces
#: as `mcp__chrome_devtools_attach__*` (hyphens normalised to underscores) rather than the
#: plugin's own launch-a-new-browser `mcp__chrome-devtools__*`. Copying the Claude spelling
#: into the Codex twin would read correctly and name nothing that harness exposes -- the
#: exact decorative-configuration failure `AGENT_SUBSTITUTIONS`'s own header describes.
AGENT_SUBSTITUTIONS = (
    ("CLAUDE.md", "AGENTS.md"),
    ("Claude-side", "Codex-side"),
    ("mcp__chrome-devtools__*", "mcp__chrome_devtools_attach__*"),
    ("mcp__plugin_playwright_playwright__*", "mcp__playwright__browser_*"),
)

#: Kept as the single pair some call sites still reason about (they ask whether
#: a body mentions the kernel file at all), so widening the derivation did not
#: silently widen those callers too.
AGENT_SUBSTITUTION = AGENT_SUBSTITUTIONS[0]

#: The CLOSED key set of a Codex twin. A new TOML key is a new contract half
#: and must be a recorded decision, never a drift.
CODEX_TWIN_KEYS = frozenset({"name", "description", "developer_instructions"})

#: The execution keys the tier materialization (`tools/agent_tiering.py
#: project-apply`, through `tools/agent_native_render.py`) writes into a twin
#: AFTER its `developer_instructions` block: the model and the reasoning
#: effort, derived from the agent's declared tier and never from the Claude
#: body. They are not twin fields -- `CODEX_TWIN_KEYS` stays closed at three --
#: but a materialized twin carries them, so the block extractor has to know
#: they may follow the block. MEASURED on the first materialized rosters: with
#: the pattern anchored at end-of-text directly after the block, every twin a
#: `project-apply` had touched was reported MALFORMED ("declares no
#: developer_instructions block") while its block was intact.
EXECUTION_KEYS = ("model", "model_reasoning_effort")

#: The ONE `# fleet-agent-execution: ...` comment `tools/agent_native_render.
#: py::render_codex_agent_toml` writes after the execution keys -- see that
#: module's own header for why the tier lives in a comment rather than a
#: fourth TOML key. `BODY_PATTERN` has to know it may follow the execution
#: keys for the exact reason it already has to know about `EXECUTION_KEYS`
#: itself: MEASURED, the first materialized rosters carrying this comment
#: were reported MALFORMED ("declares no developer_instructions block")
#: while their block was intact, the same failure mode `EXECUTION_KEYS`'s own
#: header already records for the keys it follows.
EXECUTION_TIER_COMMENT = re.compile(r"# fleet-agent-execution: [^\n]*")

#: The `developer_instructions` block of a Codex twin: the delimiter style is
#: captured (group 1) so a renderer preserves the one the file already uses,
#: and the body is group 2. Anchored at end-of-text because the block is the
#: last twin field; only the materialized execution keys, one per line, may
#: follow it (group 3, possibly empty), and then the one execution-tier
#: comment line (group 4, possibly empty). The body group stays greedy so
#: that the LAST closing delimiter still terminates the block, exactly as
#: before.
BODY_PATTERN = re.compile(
    r'(?s)developer_instructions = (\'\'\'|""")\n(.*)\1\n'
    r'((?:(?:' + "|".join(re.escape(key) for key in EXECUTION_KEYS)
    + r') = "[^"\n]*"\n)*)'
    r'(' + EXECUTION_TIER_COMMENT.pattern + r'\n)?\Z')

#: Frontmatter fence of a Claude agent file.
FRONTMATTER_FENCE = "---"


class CodexTwinFormatError(Exception):
    """A file handed to this module is not shaped like the half of the pair it
    was presented as. Carries the SOURCE LABEL and the reason only — never the
    file's content, which would put agent text into an error message."""

    def __init__(self, source: str, reason: str) -> None:
        self.source = source
        self.reason = reason
        super().__init__(f"{source}: {reason}")


def claude_body(text: str, source: str = "<claude agent>") -> str:
    """The authority body: everything after a Claude agent file's frontmatter.

    The frontmatter (`name`, `description`, `tools`, `tier`, ...) is harness
    configuration and is not part of the derivation.
    """
    if not text.startswith(FRONTMATTER_FENCE):
        raise CodexTwinFormatError(source, "no frontmatter fence at the start of the file")
    parts = text.split(FRONTMATTER_FENCE, 2)
    if len(parts) < 3:
        raise CodexTwinFormatError(source, "frontmatter is never closed")
    return parts[2].strip("\n")


def codex_body(text: str, source: str = "<codex twin>") -> str:
    """The stored derived body: a Codex twin's `developer_instructions` block."""
    match = BODY_PATTERN.search(text)
    if not match:
        raise CodexTwinFormatError(source, "declares no developer_instructions block")
    return match.group(2).strip("\n")


#: THE ONE SUBSTITUTION A BRIDGE PROJECT DOES NOT RECEIVE. `CLAUDE.md -> AGENTS.md`
#: is right where a project's `AGENTS.md` carries the rules its agents cite, and
#: FALSE where that `AGENTS.md` is a bridge -- a few lines naming `CLAUDE.md` as
#: the project's instruction authority. MEASURED 2026-10-04 at every governed
#: project's authoritative tip: fourteen of the seventeen non-Fleet projects carry
#: such a bridge (95 to 537 bytes, every one of them pointing at `CLAUDE.md`), and
#: on eCare the renamed pointer would have sent the database agent to look for the
#: `ecare_prod` production hard stop in a file that does not contain it. Which
#: projects are bridges is DATA, declared in `fleet/agents.yaml`'s
#: `codex_twin_bridges` and never guessed from a file's size or wording.
KERNEL_SUBSTITUTION = AGENT_SUBSTITUTIONS[0]


def derive_codex_body(text: str, *, bridge: bool = False) -> str:
    """Apply every declared substitution, in order. THE derivation.

    `bridge` drops exactly `KERNEL_SUBSTITUTION`, so a bridge project's twins
    keep naming the `CLAUDE.md` that really carries the cited rules.
    """
    for rule in AGENT_SUBSTITUTIONS:
        if bridge and rule == KERNEL_SUBSTITUTION:
            continue
        text = text.replace(*rule)
    return text


def derive_twin_body(claude_text: str, source: str = "<claude agent>", *,
                     bridge: bool = False) -> str:
    """The body the Codex twin of this Claude agent file must carry."""
    return derive_codex_body(claude_body(claude_text, source), bridge=bridge)


def substitution_incidence(claude_text: str, source: str = "<claude agent>") -> dict:
    """How many times each substitution SOURCE occurs in this Claude body,
    keyed by the source fragment.

    The anti-vacuity instrument. A substitution whose source occurs nowhere in
    the whole corpus is inert, and an inert rule degenerates the parity check
    into comparing each file with itself. A caller measures that over the
    corpus it owns; this module refuses to guess what the corpus is.
    """
    body = claude_body(claude_text, source)
    return {old_text: body.count(old_text) for old_text, _ in AGENT_SUBSTITUTIONS}


def render_twin_text(codex_text: str, claude_text: str,
                     codex_source: str = "<codex twin>",
                     claude_source: str = "<claude agent>") -> str:
    """The Codex twin's FULL text with its `developer_instructions` block
    replaced by the body derived from `claude_text`.

    Everything else in the twin — `name`, the per-harness `description`, the
    triple-quote style, and whether the closing delimiter sits on its own line —
    is preserved exactly as found: this module derives one field and owns no
    other. Refuses when the derived body would contain the delimiter that
    terminates the block, which would silently truncate it.

    PRESERVING THE TRAILING NEWLINE IS NOT COSMETIC. `codex_body` strips it, so
    a renderer that normalised it would rewrite every twin whose stored style
    differs while the parity check reported OK — a `render` that is not a no-op
    on a green `check` makes the two halves of this mechanism disagree about
    what "derived" means. Measured on this repository: 7 of 10 twins.
    """
    match = BODY_PATTERN.search(codex_text)
    if not match:
        raise CodexTwinFormatError(codex_source, "declares no developer_instructions block")
    delimiter = match.group(1)
    body = derive_twin_body(claude_text, claude_source)
    if delimiter in body:
        raise CodexTwinFormatError(
            claude_source,
            "derived body contains the twin's own block delimiter and cannot be embedded")
    if match.group(2).endswith("\n"):
        body += "\n"
    return codex_text[:match.start(2)] + body + codex_text[match.end(2):]


def twin_diff(claude_text: str, codex_text: str,
              claude_source: str = "<claude agent>",
              codex_source: str = "<codex twin>") -> str:
    """The unified diff between the derived body and the stored one, or `""`
    when the twin equals its derivation."""
    expected = derive_twin_body(claude_text, claude_source)
    actual = codex_body(codex_text, codex_source)
    if expected == actual:
        return ""
    return "\n".join(difflib.unified_diff(
        expected.splitlines(), actual.splitlines(),
        fromfile=f"{codex_source} (expected, derived from {claude_source})",
        tofile=f"{codex_source} (actual)", lineterm=""))


def read_claude_body(path) -> str:
    """`claude_body` of the file at `path`, named by its own filename."""
    return claude_body(path.read_text(encoding="utf-8"), path.name)


def read_codex_body(path) -> str:
    """`codex_body` of the file at `path`, named by its own filename."""
    return codex_body(path.read_text(encoding="utf-8"), path.name)


# ---------------------------------------------------------------------------
# CREATING A TWIN THAT DOES NOT EXIST YET.
#
# `render_twin_text` re-derives the body of a twin that EXISTS. It cannot
# bootstrap one, and on the rollout path nothing exists: measured across the 23
# managed target checkouts, `.codex/agents` is present on exactly zero of them,
# and the only twins anywhere are one project's nineteen. A mechanism that can
# only re-derive what somebody already hand-wrote does not remove the
# hand-maintained second copy, it presupposes it.
#
# WHY `description` IS DERIVED HERE AND STILL NOT COMPARED BY `twin_diff`, which
# looks like a contradiction and is not. Measured over the 29 real pairs that
# exist today: `name` is identical in 29 of 29, `description` in 26 of 29, and
# applying the SAME closed `AGENT_SUBSTITUTIONS` derives 28 of 29. The two
# genuine exceptions are both in this repository, and both are twins that
# ALREADY EXIST — so a create path never reaches them, while a comparison would.
# Deriving a description for a file that has none is therefore sound; asserting
# equality on a description somebody deliberately wrote is not. The two acts stay
# separate for exactly that reason, and a caller cannot ask for both at once.
# ---------------------------------------------------------------------------

#: Delimiters a `developer_instructions` block may use, in preference order.
#: `'''` first because a TOML multi-line LITERAL string processes no escapes: a
#: body containing a backslash — a regex, a Windows path, a `\n` written out —
#: goes in verbatim. In a `"""` string the same byte is an escape sequence, and
#: the file would either fail to parse or parse to something that is no longer
#: the body it was derived from. There is no third option and no escaping
#: fallback, because `codex_body` extracts the block RAW: any escaping applied on
#: the way in would make the stored twin differ from its own derivation forever.
BLOCK_DELIMITERS = ("'''", '"""')

#: Control characters a TOML basic string escapes by name. Anything else below
#: 0x20 is refused rather than emitted, because a description is a one-line
#: human label and a raw control byte in one is a defect upstream.
_DESCRIPTION_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


#: The ONE frontmatter line shape this module reads. MEASURED, not assumed: across
#: the 43 Claude agent files readable locally today (this repository's 10, `argus`'s
#: 14, `aria`'s 19), every non-empty frontmatter line matches this exactly, the key
#: set is `{name, description, tools, tier, model, effort}`, and ZERO values begin
#: with a character that would give YAML something to interpret — no quoting, no
#: folding, no block scalars, no anchors, no flow collections.
#:
#: WHY NOT PyYAML, WHICH IS AN APPROVED DEPENDENCY. Two reasons, and the first is a
#: measured failure. `console/tests/conftest.py` redirects `HOME` for isolation, so a
#: subprocess started by a test computes a different user site-packages and
#: `import yaml` raises `ModuleNotFoundError` — the CLI built on this module is
#: exercised as a subprocess, and with a YAML dependency every one of those cells
#: failed. The second is design: a full YAML parser accepts a hundred shapes this
#: module would then have to decide about, whereas the closed line rule refuses
#: everything it was not measured against, by name, and a refusal is a result.
FRONTMATTER_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*): (.*)$")


def claude_frontmatter(text: str, source: str = "<claude agent>") -> dict:
    """The Claude agent file's frontmatter as a mapping of string to string.

    Refused, never guessed at: a file whose frontmatter is absent, unclosed, or
    carries a line outside `FRONTMATTER_LINE` has no authority to derive a twin
    from, and this raises rather than returning a partial mapping.
    """
    if not text.startswith(FRONTMATTER_FENCE):
        raise CodexTwinFormatError(source, "no frontmatter fence at the start of the file")
    parts = text.split(FRONTMATTER_FENCE, 2)
    if len(parts) < 3:
        raise CodexTwinFormatError(source, "frontmatter is never closed")
    fields: dict[str, str] = {}
    for line in parts[1].strip("\n").splitlines():
        if not line.strip():
            continue
        match = FRONTMATTER_LINE.match(line)
        if not match:
            raise CodexTwinFormatError(
                source, "frontmatter carries a line that is not a plain `key: value`")
        if match.group(1) in fields:
            raise CodexTwinFormatError(source, "frontmatter declares a key twice")
        fields[match.group(1)] = match.group(2).strip()
    if not fields:
        raise CodexTwinFormatError(source, "frontmatter is empty")
    return fields


def _required_frontmatter_text(frontmatter: dict, key: str, source: str) -> str:
    value = frontmatter.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CodexTwinFormatError(source, "frontmatter declares no non-empty " + key)
    return value.strip()


def derive_twin_fields(claude_text: str, source: str = "<claude agent>") -> dict:
    """The three fields of `CODEX_TWIN_KEYS`, derived from the Claude authority
    and from nothing else.

    `name` verbatim — it is the key the pair is joined by, and it is identical in
    every real pair measured. `description` and the body both under the SAME
    closed `AGENT_SUBSTITUTIONS`: one rule, not a second one written for this
    path.
    """
    frontmatter = claude_frontmatter(claude_text, source)
    return {
        "name": _required_frontmatter_text(frontmatter, "name", source),
        "description": derive_codex_body(
            _required_frontmatter_text(frontmatter, "description", source)),
        "developer_instructions": derive_twin_body(claude_text, source),
    }


def _toml_basic_string(value: str, source: str) -> str:
    out = ['"']
    for character in value:
        if character in _DESCRIPTION_ESCAPES:
            out.append(_DESCRIPTION_ESCAPES[character])
        elif character < " " or character == "\x7f":
            raise CodexTwinFormatError(source, "description carries a control character")
        else:
            out.append(character)
    out.append('"')
    return "".join(out)


def _block_delimiter(body: str, source: str) -> str:
    """The delimiter this body can be embedded in VERBATIM, or a refusal.

    A body is refused rather than escaped: see `BLOCK_DELIMITERS`.
    """
    for delimiter in BLOCK_DELIMITERS:
        if delimiter not in body and not body.endswith(delimiter[0]):
            if delimiter == '"""' and "\\" in body:
                continue
            return delimiter
    raise CodexTwinFormatError(
        source, "derived body cannot be embedded verbatim in either block delimiter")


def create_twin_text(claude_text: str, source: str = "<claude agent>") -> str:
    """The FULL text of a Codex twin that does not exist yet.

    Self-checked before it is returned: the emitted bytes are parsed back with
    `tomllib` and must decode to exactly the derived fields. Quoting and
    escaping are the one place this module could silently produce a file that
    reads back as something else, so it does not take its own word for it.
    """
    fields = derive_twin_fields(claude_text, source)
    body = fields["developer_instructions"]
    delimiter = _block_delimiter(body, source)
    text = (f'name = {_toml_basic_string(fields["name"], source)}\n'
            f'description = {_toml_basic_string(fields["description"], source)}\n'
            f'developer_instructions = {delimiter}\n{body}\n{delimiter}\n')
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        raise CodexTwinFormatError(source, "derived twin is not parsable TOML") from None
    parsed["developer_instructions"] = parsed.get("developer_instructions", "").strip("\n")
    if parsed != fields or set(parsed) != set(CODEX_TWIN_KEYS):
        raise CodexTwinFormatError(source, "derived twin does not read back as its own fields")
    return text


# ---------------------------------------------------------------------------
# THE FULL EXPECTATION: name, description and body, under a project's bridge
# declaration and an agent's REGISTERED adaptation.
#
# WHY ADAPTATIONS ARE DATA. The 2026-10-04 audit found 26 twins that were
# deliberately different from their derivation and therefore permanently
# "different" to every check: an intended Codex-only overlay and an unintended
# edit looked the same, so a real drift could hide behind a registered
# divergence for as long as nobody re-read it. An adaptation is now the exact
# delta from the derivation, applied by this module, so the adapted twin is
# itself an expected output: it PASSES when it equals that output and FAILS on
# any byte the adaptation does not account for.
# ---------------------------------------------------------------------------


class TwinAdaptationError(CodexTwinFormatError):
    """A registered adaptation no longer applies to the derivation it adapts:
    a `replace` anchor that stopped occurring, or a `require`d text that is no
    longer present. Stale adaptation data is a refusal, never a silent no-op."""


@dataclass(frozen=True)
class TwinAdaptation:
    """The registered, closed delta between a derived twin and the twin a
    project intends Codex to read. Applied in field order: `replace` pairs in
    sequence on the derived body, then `append`; `description` pairs in
    sequence on the derived DESCRIPTION; `require` asserts texts the final body
    must still carry -- a safety pointer that no later source or renderer
    change may drop silently.

    EVERY TEXTUAL CHANGE IS AN ANCHORED PAIR, the description included. A
    full-text description override was measured to freeze the Claude source's
    description out of the twin: an edit to it never reached Codex and
    `reverify` re-bound the stale copy. A pair changes only its anchor, so the
    rest of the source keeps propagating and an edit to the anchor fails closed.
    """

    description: tuple[tuple[str, str], ...] = ()
    replace: tuple[tuple[str, str], ...] = ()
    append: str = ""
    require: tuple[str, ...] = ()

    def is_empty(self) -> bool:
        return not (self.description or self.replace or self.append or self.require)


#: The refusal each anchored field states, fixed text only (spec §8.5).
_STALE_ANCHOR = {
    "body": "a registered replace anchor no longer occurs in the derived body",
    "description": "a registered description anchor no longer occurs in the derived description",
}


def _apply_pairs(text: str, pairs: tuple[tuple[str, str], ...], what: str, source: str) -> str:
    for old_text, new_text in pairs:
        if old_text not in text:
            raise TwinAdaptationError(source, _STALE_ANCHOR[what])
        text = text.replace(old_text, new_text)
    return text


def renderer_identity() -> str:
    """The content address of THIS module, which is the whole renderer: every
    rule that shapes an expected twin -- the substitution list, the bridge
    rule, the adaptation semantics -- lives in these bytes and nowhere else.

    A recorded verification names the renderer it was proven under, so any
    edit here makes every recorded verification stale until it is re-proven.
    That is deliberately coarse: a renderer edit that changes no expected
    output still costs a re-verification, and it is the price of never having
    to decide by hand which edits "could not matter".
    """
    return "sha256:" + hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()


def expected_twin_fields(claude_text: str, source: str = "<claude agent>", *,
                         bridge: bool = False,
                         adaptation: TwinAdaptation | None = None) -> dict:
    """The three `CODEX_TWIN_KEYS` values the twin of this Claude file must
    carry, for a project with this bridge declaration and an agent with this
    registered adaptation. Raises `TwinAdaptationError` when the adaptation
    no longer applies."""
    frontmatter = claude_frontmatter(claude_text, source)
    description = derive_codex_body(
        _required_frontmatter_text(frontmatter, "description", source), bridge=bridge)
    body = derive_twin_body(claude_text, source, bridge=bridge)
    if adaptation is not None:
        body = _apply_pairs(body, adaptation.replace, "body", source) + adaptation.append
        description = _apply_pairs(description, adaptation.description, "description", source)
        for required in adaptation.require:
            if required not in body:
                raise TwinAdaptationError(
                    source, "a registered required text is absent from the expected body")
    return {"name": _required_frontmatter_text(frontmatter, "name", source),
            "description": description, "developer_instructions": body}


def stored_twin_fields(codex_text: str, source: str = "<codex twin>") -> dict:
    """The three `CODEX_TWIN_KEYS` values a stored twin actually carries, ALL
    THREE AS TOML DECODES THEM, because that is what Codex reads. The body is
    the decoded `developer_instructions` with its edge newlines stripped (the
    normalisation `codex_body` applies). MEASURED before this: comparing the
    raw block let a triple-double-quoted twin whose escapes or line
    continuations Codex decodes differently read healthy, and a crafted file
    whose real key was spelt without spaces hid the genuine block inside its
    string for the leftmost raw match to find. A key outside the closed set,
    the execution keys included in the tolerance `BODY_PATTERN` already pins,
    is refused."""
    try:
        parsed = tomllib.loads(codex_text)
    except tomllib.TOMLDecodeError:
        raise CodexTwinFormatError(source, "is not parsable TOML") from None
    if not set(parsed) <= CODEX_TWIN_KEYS | set(EXECUTION_KEYS):
        raise CodexTwinFormatError(source, "carries a key outside the closed twin key set")
    for key in ("name", "description", "developer_instructions"):
        if not isinstance(parsed.get(key), str):
            raise CodexTwinFormatError(source, "declares no string " + key)
    return {"name": parsed["name"], "description": parsed["description"],
            "developer_instructions": parsed["developer_instructions"].strip("\n")}


def expected_twin_diff(expected: dict, stored: dict, source: str = "<codex twin>") -> str:
    """A reader's account of how a stored twin differs from its expectation,
    or `""`: one line per differing scalar field, then the body's unified
    diff."""
    out = [f"{key}: expected {expected[key]!r}, stored {stored[key]!r}"
           for key in ("name", "description") if expected[key] != stored[key]]
    if expected["developer_instructions"] != stored["developer_instructions"]:
        out.extend(difflib.unified_diff(
            expected["developer_instructions"].splitlines(),
            stored["developer_instructions"].splitlines(),
            fromfile=f"{source} (expected)", tofile=f"{source} (stored)", lineterm=""))
    return "\n".join(out)


#: The one line a rendered twin's description may occupy. A twin whose
#: description is not exactly one such line is refused by `render_expected_twin_text`
#: rather than rewritten by a pattern that could also match the body.
_DESCRIPTION_LINE = re.compile(r"(?m)^description = [^\n]*$")


def render_expected_twin_text(codex_text: str, claude_text: str,
                              codex_source: str = "<codex twin>",
                              claude_source: str = "<claude agent>", *,
                              bridge: bool = False,
                              adaptation: TwinAdaptation | None = None) -> str:
    """The stored twin rewritten to its FULL expectation: the body as
    `render_twin_text` writes it, and the description line re-emitted when it
    differs. Everything else -- name, execution keys, and the delimiter style
    wherever it can carry the body verbatim -- is preserved. A block whose
    delimiter cannot carry the body verbatim (the delimiter inside it, or a
    backslash inside a triple-double-quoted block, which TOML would decode as
    an escape) is switched to the delimiter `_block_delimiter` chooses. The
    result is read back AS CODEX DECODES IT and must equal the expectation."""
    fields = expected_twin_fields(claude_text, claude_source, bridge=bridge,
                                  adaptation=adaptation)
    match = BODY_PATTERN.search(codex_text)
    if not match:
        raise CodexTwinFormatError(codex_source, "declares no developer_instructions block")
    body = fields["developer_instructions"]
    delimiter = match.group(1)
    if delimiter in body or body.endswith(delimiter[0]) or (
            delimiter == '"""' and "\\" in body):
        delimiter = _block_delimiter(body, claude_source)
    if match.group(2).endswith("\n"):
        body += "\n"
    head = codex_text[:match.start()]
    lines = _DESCRIPTION_LINE.findall(head)
    if len(lines) != 1:
        raise CodexTwinFormatError(codex_source, "does not declare exactly one description line")
    if stored_twin_fields(codex_text, codex_source)["description"] != fields["description"]:
        head = _DESCRIPTION_LINE.sub(
            lambda _: "description = " + _toml_basic_string(fields["description"], claude_source),
            head, count=1)
    closing = match.end(2) + len(match.group(1))
    text = (head + codex_text[match.start():match.start(1)] + delimiter + "\n" + body
            + delimiter + codex_text[closing:])
    if stored_twin_fields(text, codex_source) != fields:
        raise CodexTwinFormatError(codex_source, "rendered twin does not read back as its expectation")
    return text
