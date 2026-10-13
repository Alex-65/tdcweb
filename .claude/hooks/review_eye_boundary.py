#!/usr/bin/env python3
"""The execution boundary of a review eye: it writes only inside disposable state it owns.

The explicitly invoked cross-harness Claude review transport has one operator
exception: OS sandbox attestation is waived for that invocation, reported as
NOT_VERIFIED. Its sealed invocation context still binds the canonical role,
project, policy and session; its hook establishes identity and owned scratch.
This exception never changes a native actor's classification or OS boundary.

RUN, by the harness, on every mutating tool call of every subagent:
    `.claude/settings.json` -> hooks.PreToolUse -> `python3 -B "$CLAUDE_PROJECT_DIR/tools/review_eye_boundary.py" hook`
RUN, by an actor, before a review eye is dispatched and at the commit check:
    `python3 -B tools/review_eye_boundary.py check [--root PATH]`

WHY THIS EXISTS -- the incident of 2026-09-06, work item `doc-writer-retirement`. The
round-1 Claude eye, `fleet-code-reviewer`, held an unbounded `Bash` grant. It created a
base-comparison worktree INSIDE the shared operator checkout, then re-ran a "must refuse"
cell of `git worktree remove` against that checkout to prove a guard; the earlier refusal
had been git's own, caused by the eye's stray directory, and with the tree clean the second
run succeeded and deleted `/Volumes/.../claude-fleet-dev`. Tracked state survived because it
was committed; untracked and ignored content was lost and cannot be enumerated; the
operator's shell stayed attached to a deleted directory; and the recreated checkout did not
bring the project agent roster back, so round 2 was reviewed by a general-purpose agent
reading the reviewer contract as prose. The contract already said "you never write the
shared checkout". Prose is authority, not capability, and the capability was unbounded.

THE PROPERTY, from `CANON.md` §Review: an independent review eye treats the shared subject
checkout as read-only; every mutation a review needs -- a mutation test, a refusal proof, a
destructive verification, cleanup -- happens only inside disposable state created for and
owned by that review execution. This module makes the violation UNAVAILABLE rather than
forbidden: the eye's write capability is confined by the operating system to one root this
module mints for that one agent, and nothing else on the machine is writable to it.

WHAT THE BOUNDARY IS, AND WHAT IT IS NOT. It is POSITIVE OWNERSHIP, never a blacklist of
spellings. The hook does not read the command; it does not know what `git worktree remove`,
`rm -rf`, `git reset --hard` or the next spelling mean. `Bash` is executed under a macOS
Seatbelt profile that denies `file-write*` everywhere except the eye's own scratch root (and
`/dev`), so the shared checkout, its git common directory, every other worktree, the home
directory and the rest of the file system are read-only to it whatever the command says. On
Linux the same property comes from unprivileged bubblewrap (`/usr/bin/bwrap`): the whole file
system is bound read-only, a private `/dev` and `/proc` are mounted, and the eye's scratch
root (real path) is the one read-write bind; every namespace but the network is unshared and
no capability is kept. A write elsewhere fails with `EROFS`, a hard link out of the root with
`EXDEV`, and a nested user namespace cannot remount the locked read-only binds.
`Write`, `Edit`, `MultiEdit` and `NotebookEdit` are harness file operations, not shell: the
harness writes them itself, unsandboxed, AFTER this hook has answered, so a path this hook
found inside the root can be swapped for a symlink to the subject between the check and the
write (the eye's own Bash can do the swap). A check-then-write race is not a boundary, so
these tools are DENIED for an eye outright; it writes its report and its fixtures through
Bash, where the operating system decides at the moment of the write. Reads are not
restricted here: the eye must read the real subject, its history and its diffs, and that is
the point of its existence.

WHO IS BOUNDED. Membership is DERIVED FROM THE CONTRACT, not from a list of names. The hook
receives the harness's own `agent_type`, finds the contract declaring that name and looks for
the one-line declaration `DOCUMENTATION-REVIEW-ROLE: REVIEW_EYE` that
`tools/test_review_consumer_boundary.py` already requires of every Fleet actor contract. An
actor that declares itself an eye is bounded from its first tool call; a future eye inherits
the boundary by declaring the role, with no edit here. The harness names an agent by the
`name:` its contract declares, so the contract is found by that name and never by guessing
the file stem; a name two contracts claim is refused. A `WRITER` or `NONE` actor, a built-in
harness agent with no contract file, and the parent session itself (no `agent_type`) pass
through untouched: implementers and the orchestrator keep the authority they have. Membership
is also PINNED: `EXPECTED_EYES` names the contracts that must declare `REVIEW_EYE`, so an eye
cannot leave the class by editing one line while every gate stays green -- it leaves it by a
recorded decision here, the same way `tools/test_review_consumer_boundary.py` pins the
documentation specialist as the `WRITER`.

FAIL CLOSED, STRUCTURALLY. A hook process that exits 1 is a non-blocking error and the tool
call PROCEEDS -- an uncaught exception would fail OPEN. So `hook` never raises: every
failure it can meet -- unparsable input, an unsafe identifier, a contract whose role line is
missing or ambiguous, a tool the boundary does not cover, a scratch root it cannot create,
the platform's primitive (`sandbox-exec`, `bwrap`) absent or not executable, a platform with
neither, a Linux bwrap that cannot establish its sandbox over the eye's root (proven by one
probe before each allow) -- becomes a DENY carried in the hook's JSON, and if
even that cannot be printed the process exits 2, which blocks. An eye whose isolation cannot
be established therefore cannot execute at all, and reports that it could not; it never
falls back to unrestricted execution.

THE SCRATCH ROOT is minted by this module, never by the dispatching brief:
`<base>/claude-review-eye/<session_id>/<agent_id>`, created by the hook on the eye's
first call. Ownership is thereby proven from the instrument's own data (the harness's ids),
not from a name an orchestrator typed. The wrapped command sees it as `$REVIEW_EYE_SCRATCH`,
its `TMPDIR` is redirected beneath it so `tempfile`, `mktemp` and git temp files land
inside the boundary, and `$REVIEW_EYE_ACTOR` carries the classified `agent_type`. The
Seatbelt profile and the bwrap arguments are regenerated on every call and passed inline, so
there is no sandbox description inside the writable root for the eye to edit. `<base>` is
`scratch_base()`: the FleetLocal volume on macOS, the account's own owner-only
`~/.local/state/fleet/scratch/work` elsewhere, or `FLEET_SCRATCH_ROOT` when it is set. An eye that needs a mutable copy
of the subject CLONES it into its scratch (`git clone --shared`), which writes nothing into
the subject's repository; `git worktree add` from the subject would, and is refused like any
other write there.

WHAT `check` PROVES. That the project binds this hook exactly (matcher and command) in
`.claude/settings.json`, PreToolUse and SubagentStart both; that every contract declaring
`REVIEW_EYE` grants only tools an eye may hold -- `Read`, `Grep`, `Glob`, which do not write,
plus `Bash`, which it confines -- and that a new eye granting anything else
(`Agent`, an MCP tool, `*`, `Write`, or no `tools` line at all) is REFUSED, because a
capability the boundary does not cover is exactly the unbounded authority this module exists
to remove; that every pinned eye still declares the role and every contract's `name` is its
file stem; and that the sandbox primitive on this host actually refuses a write outside a
root and permits one inside it, both cells, at check time. What it does not judge: prose. A
contract sentence is read by the eye, not by this tool.

`check` AND THE CONTROL ARE THE PARENT'S TO RUN, NEVER AN EYE'S. macOS refuses a nested
`sandbox_apply`, so from inside the boundary the primitive cannot be applied at all: `check`
then reports a distinct, named outcome (`not measurable from inside a sandbox`) rather than
a false `REFUSED`, and the control run fails loudly instead of counting a command that never
reached the boundary as a refusal. On Linux a nested `bwrap` is refused where the host forbids
nested user namespaces, and `check` reports that as a failed cell carrying bwrap's own words.
The orchestrator runs both before dispatching an eye and
cites them; an eye consumes that evidence, as `CANON.md` §Review says of every proof.

MANAGED PROJECTS RUN THIS SAME FILE. A Fleet-managed project whose Claude roster declares
a `REVIEW_EYE` receives it through `tools/review_eye_boundary_render.py`, which writes it to
`.claude/hooks/review_eye_boundary.py` with exactly one substitution -- `EXPECTED_EYES`
becomes the eyes that project's contracts declare -- together with the `fleetlib` module
`check` parses frontmatter with, and binds it in the project's `.claude/settings.json`. The
hook, the scratch roots, the ledger and `check` are this module's, unchanged; only the root,
the parser location and the hook command follow from where the file sits.

LIMITS, stated so nobody infers them away. The hook is a LOCAL project setting and runs only
in a session that loaded `.claude/settings.json`; a harness build that does not run
settings hooks for subagents, or a caller that disables hooks, has no boundary, which is
why every eye's contract makes it print `$REVIEW_EYE_SCRATCH` first and stop when it is
unset. Reads are unrestricted, so this is not a secrets boundary. The parent session is
deliberately unbounded. The eye's Bash is auto-approved once rewritten,
so no permission prompt stands in front of it: reads of the whole file system and outbound
network are open to it, and the project's prohibition on reading secret values stays a
contract rule, not a capability. A malformed hook payload denies for EVERY actor, the parent
included, because classification happens after parsing. The Codex eye runs under its own
dispatcher's disposable worktrees and Codex's sandbox (`tools/codex-review`), not under this
hook.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import NamedTuple

#: `ROLE_LINE` is the one exact shape of the role declaration. It is owned by
#: `claude_projection_identity`, whose launch decision reads it too (only a REVIEW_EYE launch
#: obeys a review point's policy pin), and re-exported here for
#: `tools/test_review_consumer_boundary.py`, which imports it from this module.
from claude_projection_identity import (ROLE_LINE, SAFE_NAME, Unproven, _normalised, _roster,
                                        _split, canonical_identity, record_fields)

ROLES = frozenset({"WRITER", "REVIEW_EYE", "NONE"})
BOUNDED_ROLE = "REVIEW_EYE"

#: Tools that never write. An eye may hold them unconfined.
READ_ONLY_TOOLS = frozenset({"Read", "Grep", "Glob"})
#: The one mutating tool the boundary confines: the shell, under the OS sandbox,
#: which decides at the moment of each write.
BASH_TOOL = "Bash"
#: The harness's own file writers. Matched so that an eye's call to one is
#: DENIED: the harness writes after the hook answers, so a path check here is a
#: race, not a boundary (see the module docstring).
PATH_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
COVERED_TOOLS = frozenset({BASH_TOOL, *PATH_TOOLS})
#: The grants an eye may hold: read-only tools and the confined shell.
EYE_TOOLS = READ_ONLY_TOOLS | {BASH_TOOL}
#: The contracts pinned as review eyes. A contract named here that no longer
#: declares REVIEW_EYE is refused by `check`: leaving the class is a recorded
#: decision in this set, never a one-line edit elsewhere.
EXPECTED_EYES = frozenset({"tdc-code-reviewer", "tdc-design-system-enforcer"})
#: WHERE THIS FILE SITS DECIDES THE PROJECT IT SERVES. In this repository it is
#: `tools/review_eye_boundary.py`; in a Fleet-managed project
#: `tools/review_eye_boundary_render.py` materializes it at
#: `.claude/hooks/review_eye_boundary.py`, beside a copy of the one `fleetlib` module
#: `check` parses frontmatter with. Those two layouts are the whole set: the root, the
#: parser's import location and the hook command are derived from them, never configured.
HERE = pathlib.Path(__file__).resolve()
MATERIALIZED_DIR = pathlib.PurePosixPath(".claude/hooks")


def _layout(here: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """(project root, directory holding `fleetlib`) for the file at `here`."""
    if here.parent.name == MATERIALIZED_DIR.name and here.parent.parent.name == MATERIALIZED_DIR.parent.name:
        return here.parents[2], here.parent
    return here.parents[1], here.parents[1] / "console"


REPO, FLEETLIB_PARENT = _layout(HERE)
#: The exact settings binding `check` requires. A regex matcher anchored to
#: the closed set, and the command that reaches this file through the
#: variable the harness sets for every hook.
MATCHER = "^(" + "|".join(sorted(COVERED_TOOLS)) + ")$"
HOOK_COMMAND = f'python3 -B "$CLAUDE_PROJECT_DIR/{HERE.relative_to(REPO).as_posix()}" hook'
SETTINGS_PATH = ".claude/settings.json"
AGENTS_DIR = ".claude/agents"

SANDBOX_EXEC = "/usr/bin/sandbox-exec"
#: The Linux primitive: unprivileged bubblewrap at its fixed distribution path, never one found
#: on PATH. Measured on 2026-10-13 on all six managed Linux accounts (0.9.0, and 0.6.1 on dwh;
#: not setuid; caps dropped, subject writes EROFS).
BWRAP = "/usr/bin/bwrap"
LINUX = sys.platform.startswith("linux")
#: This platform's primitive. Every platform but Linux names `sandbox-exec`, which exists only
#: on macOS: elsewhere it is absent, and absence is a refusal.
SANDBOX_PRIMITIVE = BWRAP if LINUX else SANDBOX_EXEC
#: The shell that runs the eye's command under the primitive. The managed Linux accounts carry
#: no zsh (measured on all six), and Claude Code runs its Bash tool there in bash.
EYE_SHELL = "/bin/bash" if LINUX else "/bin/zsh"
#: Test seam only: lets the "isolation unavailable" cell point at a path that
#: does not exist. Never set in production. It overrides `SANDBOX_PRIMITIVE`.
SANDBOX_EXEC_ENV = "REVIEW_EYE_SANDBOX_EXEC"
SCRATCH_ENV = "REVIEW_EYE_SCRATCH"
ACTOR_ENV = "REVIEW_EYE_ACTOR"
SCRATCH_PARENT = "claude-review-eye"
LEDGER_NAME = "dispatch.jsonl"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
#: THE ONLY FRONTMATTER WHOSE IDENTITY THE BOUNDARIES ESTABLISH: column-0 `key: value` lines,
#: blank lines and comments -- the shape every contract here already has, and the one
#: `fleetlib.codex_twin.claude_frontmatter` requires. The harness parses YAML, which spells a
#: `name` key in ways no line pattern enumerates (indented, quoted, `name :`, `? name`, a flow
#: mapping, a value continued on the next line); so a file OUTSIDE this grammar is not read as
#: nameless but kept as a contract whose name cannot be established. Inside it, every column-0
#: line is read as a key, which is every top-level key YAML can produce and possibly more: a
#: quoted or flow value continued onto a column-0 `name:` line leaves that name carrying its
#: quote or bracket, which is no safe name, so such a file is refused, not misread.
PLAIN_LINE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]+(.*?))?[ \t]*")
#: What macOS prints when a sandboxed process tries to apply another profile.
NESTED_SANDBOX_MARK = "sandbox_apply"
#: What the operating system says when the boundary refuses a write.
DENIAL_MARK = "read-only file system" if LINUX else "operation not permitted"


class Refusal(Exception):
    """A reason the boundary cannot be established or was violated; becomes a deny."""


def canonical_actor(agent_type: str, project_dir: pathlib.Path) -> str:
    """The Fleet identity an actor's contract is looked up by.

    An `fp:*` runtime name is its source agent's name only when the session's own
    projection proves it against the live source contract of `project_dir`
    (`claude_projection_identity`); one it cannot prove is refused, because
    an actor whose identity cannot be proven is not allowed to act unbounded. Every other name is
    returned unchanged, a foreign `plugin:name` included, which no contract here declares."""
    try:
        return canonical_identity(agent_type, project_dir).canonical
    except Unproven as exc:
        raise Refusal(f"projected identity {agent_type!r} is unproven ({exc}); an actor whose "
                      "identity cannot be proven is not allowed to act unbounded") from exc


# ---------------------------------------------------------------------------
# classification: who is bounded, derived from the contract
# ---------------------------------------------------------------------------

def declared_role(text: str) -> tuple[str | None, str | None]:
    """The role a contract declares, or the reason it declares none validly."""
    values = ROLE_LINE.findall(text)
    if not values:
        return None, "declares no DOCUMENTATION-REVIEW-ROLE line"
    if len(values) > 1:
        return None, f"declares {len(values)} DOCUMENTATION-REVIEW-ROLE lines ({', '.join(values)})"
    if values[0] not in ROLES:
        return None, (f"declares the unknown role {values[0]!r}; the closed set is "
                      f"{', '.join(sorted(ROLES))}")
    return values[0], None


def plain_frontmatter(front: list[str]) -> tuple[dict[str, str], str | None]:
    """(keys, None) for a frontmatter inside `PLAIN_LINE`'s grammar, else ({}, the reason)."""
    fields: dict[str, str] = {}
    for line in front:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = PLAIN_LINE.fullmatch(line)
        if match is None:
            return {}, f"carries the frontmatter line {line!r}, not a plain `key: value` line"
        key, value = match.group(1), match.group(2) or ""
        if key in fields:
            return {}, f"declares the frontmatter key {key!r} twice"
        fields[key] = value
    return fields, None


class Contract(NamedTuple):
    """One agent file of a roster, read as Claude Code reads it."""
    path: pathlib.Path
    relative: str
    text: str  # byte-order mark stripped, line endings translated
    name: str | None  # the one safe name it declares; None when `problem` says why not
    problem: str | None


def roster(project_dir: pathlib.Path) -> list[Contract]:
    """Every agent file Claude Code loads from `project_dir`'s own agent directory.

    NOT every agent the session can run: in a linked worktree with no agent directory of its
    own the harness falls back to the main worktree's, and `--add-dir` directories add agents;
    neither is read here. An empty roster is therefore refused by the boundary rather than
    read as "no contract" (`is_bounded`).

    THE ONE DISCOVERY PATH of the boundary, its check and the renderer. It is the identity
    module's loader-faithful reader (`claude_projection_identity._roster`): `*.md` RECURSIVELY
    under the agent directory, links followed, a byte-order mark stripped, line endings
    translated, and Claude Code's own frontmatter recogniser. The top-level glob and the
    `startswith("---")` test this replaced skipped a contract with a byte-order mark or in a
    subdirectory, which the harness loads -- and a REVIEW_EYE or IMPLEMENTER the boundary cannot
    find runs unbounded. A file is left out only when it PROVABLY declares no name -- its
    frontmatter inside `PLAIN_LINE`'s grammar, with no `name` key -- because the harness does not
    load such a file (2.1.281: 'Missing required "name" field in frontmatter'). Every other file
    is kept, with its `problem` when its one safe name cannot be established."""
    base = pathlib.Path(project_dir) / AGENTS_DIR
    contracts = []
    for path, raw in _roster(project_dir):
        text = _normalised(raw.decode("utf-8", "replace"))
        fields, problem = plain_frontmatter(_split(text)[0])
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            problem = "is not UTF-8"
        if problem is None and "name" not in fields:
            continue
        if problem is None and not SAFE_NAME.match(fields["name"]):
            problem = f"declares the name {fields['name']!r}, which is not one plain safe name"
        contracts.append(Contract(path, f"{AGENTS_DIR}/{path.relative_to(base).as_posix()}",
                                  text, None if problem else fields["name"], problem))
    return contracts


def contract(project_dir: pathlib.Path, agent_type: str,
             contracts: list[Contract] | None = None) -> Contract | None:
    """The project contract the harness runs `agent_type` under, or None.

    The harness names a subagent by the `name` its contract declares, never by the file stem,
    so the lookup reads every contract's declared name. A plugin agent (`plugin:name`) declares
    nothing here -- the harness refuses `:` in a project agent's name -- and is not this
    boundary's to bound. A Refusal when two contracts declare the name, and when ANY agent file
    of the roster declares a name this reader cannot establish: the harness may be running that
    file under this very name, and an actor whose contract cannot be identified is not allowed
    to act unbounded."""
    if ":" in agent_type:
        return None
    contracts = roster(project_dir) if contracts is None else contracts
    unreadable = [f"{c.relative} {c.problem}" for c in contracts if c.problem]
    if unreadable:
        raise Refusal(f"{'; '.join(unreadable)}; so which contract {agent_type!r} runs under "
                      f"cannot be established, and an actor whose contract cannot be "
                      f"identified is not allowed to act unbounded")
    matches = [c for c in contracts if c.name == agent_type]
    if len(matches) > 1:
        raise Refusal(f"{len(matches)} contracts under {AGENTS_DIR} declare name {agent_type!r}; "
                      f"an actor whose contract is ambiguous is not allowed to act unbounded")
    return matches[0] if matches else None


def is_bounded(project_dir: pathlib.Path, agent_type: str) -> bool:
    """True when `agent_type` declares REVIEW_EYE. Raises Refusal on a contract
    that exists but declares no single valid role: an actor that cannot be
    classified is not allowed to act unbounded. Raises Refusal, too, on a project
    directory whose roster is empty, absent or unreadable: the harness may then be
    running an eye from a roster this boundary does not read (a linked worktree's
    fallback to the main worktree's), and "the authority could not be found" is not
    "this actor is not an eye"."""
    contracts = roster(project_dir)
    if not contracts:
        raise Refusal(f"{project_dir}/{AGENTS_DIR} carries no contract that could be read, so no "
                      f"actor of this project can be classified; an actor that may be a review "
                      f"eye is not allowed to act unbounded")
    found = contract(project_dir, agent_type, contracts)
    if found is None:
        return False
    role, problem = declared_role(found.text)
    if problem:
        raise Refusal(f"{found.relative} {problem}; an actor that cannot be "
                      f"classified is not allowed to act unbounded")
    return role == BOUNDED_ROLE


# ---------------------------------------------------------------------------
# the scratch root and the sandbox profile
# ---------------------------------------------------------------------------

def scratch_base() -> pathlib.Path:
    """Fleet-owned heavy scratch, independent of global TMPDIR and shell startup.

    `FLEET_SCRATCH_ROOT` when set. Otherwise macOS uses the FleetLocal volume, refusing when it
    is not mounted, and Linux uses the account's own `~/.local/state/fleet/scratch/work`, made
    owner-only -- the default `codex-review` already applies on the same accounts. A per-account
    base keeps one account's eyes out of a `/tmp` another account on the same host shares."""
    if "FLEET_SCRATCH_ROOT" in os.environ:
        root = pathlib.Path(os.environ["FLEET_SCRATCH_ROOT"])
        if not root.is_absolute():
            raise ValueError("FLEET_SCRATCH_ROOT must be absolute")
        return root.resolve()
    if LINUX:
        state = pathlib.Path.home() / ".local" / "state" / "fleet" / "scratch"
        root = state / "work"
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for directory in (state, root):
            directory.chmod(0o700)
        return root.resolve()
    if not pathlib.Path("/Volumes/ST7T2T").is_mount():
        raise OSError("Fleet scratch volume is not mounted; set FLEET_SCRATCH_ROOT explicitly")
    return pathlib.Path("/Volumes/ST7T2T/FleetLocal/scratch/work").resolve()


def private_scratch(prefix: str) -> pathlib.Path:
    """Allocate a new private invocation directory; never prune an existing actor."""
    root = scratch_base()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return pathlib.Path(tempfile.mkdtemp(prefix=prefix, dir=root)).resolve()


def scratch_root(session_id: str, agent_id: str) -> pathlib.Path:
    if not SAFE_ID.match(session_id):
        raise Refusal("session_id is not a safe path segment")
    if not SAFE_ID.match(agent_id):
        raise Refusal("agent_id is not a safe path segment")
    base = scratch_base()
    return base / SCRATCH_PARENT / session_id / agent_id


def ledger_path(session_id: str) -> pathlib.Path:
    if not SAFE_ID.match(session_id):
        raise Refusal("session_id is not a safe path segment")
    base = scratch_base()
    return base / SCRATCH_PARENT / session_id / LEDGER_NAME


def ensure_scratch(root: pathlib.Path) -> bool:
    """Create the eye's root (0700) and its `tmp`; True when it was created now."""
    created = not root.exists()
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        (root / "tmp").mkdir(exist_ok=True, mode=0o700)
    except OSError as error:
        raise Refusal(f"the eye's scratch root could not be created: {error}") from error
    if not root.is_dir():
        raise Refusal("the eye's scratch root is not a directory")
    return created


def seatbelt_profile(root: pathlib.Path) -> str:
    """Deny every file write except under `root` (real path) and `/dev`."""
    real = os.path.realpath(root)
    if any(c in real for c in '"\\\n'):
        raise Refusal("the scratch root path is not representable in a sandbox profile")
    return ("(version 1)\n"
            "(allow default)\n"
            "(deny file-write*)\n"
            f'(allow file-write* (subpath "{real}"))\n'
            '(allow file-write* (subpath "/dev"))\n')


def bwrap_arguments(root: pathlib.Path) -> list[str]:
    """Bind everything read-only, then a private `/dev` and `/proc`, then `root` (real path)
    read-write. The order is the mechanism: a later bind covers an earlier one, so `/` first."""
    real = os.path.realpath(root)
    return ["--unshare-all", "--share-net", "--die-with-parent", "--new-session",
            "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--bind", real, real]


def sandbox_primitive() -> str:
    path = os.environ.get(SANDBOX_EXEC_ENV, SANDBOX_PRIMITIVE)
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        raise Refusal(f"isolation unavailable: {path} is absent or not executable; "
                      f"the eye cannot execute unbounded instead")
    return path


def sandbox_argv(root: pathlib.Path) -> list[str]:
    """The primitive and its arguments: every file write denied except under `root`."""
    primitive = sandbox_primitive()
    if LINUX:
        return [primitive, *bwrap_arguments(root)]
    return [primitive, "-p", seatbelt_profile(root)]


def establish_sandbox(root: pathlib.Path) -> None:
    """On Linux, prove the sandbox can be set up over `root` before the eye's Bash is allowed.

    An executable bwrap can still be unable to create its namespaces (a host forbidding
    unprivileged user namespaces, an AppArmor profile it depends on unloaded). Allowed anyway,
    every command -- the eye's mandatory first one included -- would fail, and the eye would end
    REVIEW NOT OBTAINED; refused here, it keeps the read-only mode its contract names for a host
    with no usable sandbox. Never a fallback to unconfined execution either way."""
    if not LINUX:
        return
    try:
        probe = subprocess.run([*sandbox_argv(root), "/bin/true"], capture_output=True,
                               text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(f"isolation unavailable: the sandbox could not be established: {error}; "
                      f"the eye cannot execute unbounded instead") from error
    if probe.returncode != 0:
        raise Refusal(f"isolation unavailable: {sandbox_primitive()} cannot establish its sandbox "
                      f"here (rc={probe.returncode}: {probe.stderr.strip()[-200:]}); the eye "
                      f"cannot execute unbounded instead")


def command_script(command: str, root: pathlib.Path, actor: str) -> tuple[pathlib.Path, bytes]:
    """Pure expected path/bytes; reconstructing evidence never creates it."""
    if not isinstance(command, str):
        raise Refusal("the Bash command is not a string")
    env = (f"{SCRATCH_ENV}={shlex.quote(str(root))} "
           f"{ACTOR_ENV}={shlex.quote(actor)} "
           f"TMPDIR={shlex.quote(str(root / 'tmp'))} "
           f"TMPPREFIX={shlex.quote(str(root / 'tmp' / 'zsh'))} "
           f"PYTHONDONTWRITEBYTECODE=1")
    # Re-export after the shell's startup file (~/.zshenv, $BASH_ENV); keep here-doc staging within the owned scratch.
    body = f"export {env}\n{command}\n".encode("utf-8")
    return root / (".fleet-command." + hashlib.sha256(body).hexdigest() + ".zsh"), body


def verify_command_script(command: str, root: pathlib.Path, actor: str) -> None:
    """Require the producer's regular script, without following an actor's symlink."""
    script, body = command_script(command, root, actor)
    try:
        fd = os.open(script, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as source:
            metadata = os.fstat(source.fileno())
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_size != len(body)
                    or source.read(len(body) + 1) != body):
                raise Refusal("the owned command script does not match its tool call")
    except OSError as error:
        raise Refusal(f"the owned command script is unavailable: {error}") from error


def wrapped_command(command: str, root: pathlib.Path, actor: str, *, context: dict | None = None) -> str:
    """Pure shell line: the same OS boundary executes an owned script, not inline code.

    Claude's headless permission parser can ask again for complex inline `zsh -c`
    programs after the hook allows them. A script operand avoids that inline safety
    check; the unchanged sandbox (Seatbelt, or bwrap on Linux) remains mandatory for every
    execution.
    """
    script, _ = command_script(command, root, actor)
    if context is not None:
        return shlex.join([context["shell"], str(script)])
    return shlex.join([*sandbox_argv(root), EYE_SHELL, str(script)])


def prepare_command(command: str, root: pathlib.Path, actor: str, *, context: dict | None = None) -> str:
    """Create only inside the minted root; refuse existing altered files or symlinks."""
    wrapped = wrapped_command(command, root, actor, **({"context": context} if context else {}))
    script, body = command_script(command, root, actor)
    if context is not None:
        # Project and invocation hooks may publish the same command concurrently.
        # A create-once hard link exposes only the completely written private file.
        fd, staging = tempfile.mkstemp(prefix=".fleet-staging-command.", dir=root)
        try:
            with os.fdopen(fd, "wb") as target:
                target.write(body)
            try:
                os.link(staging, script, follow_symlinks=False)
            except FileExistsError:
                pass
            verify_command_script(command, root, actor)
        except OSError as error:
            raise Refusal(f"the owned command script could not be published: {error}") from error
        finally:
            os.unlink(staging)
        return wrapped
    try:
        fd = os.open(script, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        verify_command_script(command, root, actor)
    except OSError as error:
        raise Refusal(f"the owned command script could not be created: {error}") from error
    else:
        try:
            with os.fdopen(fd, "wb") as target:
                target.write(body)
        except OSError as error:
            raise Refusal(f"the owned command script could not be written: {error}") from error
    return wrapped


# ---------------------------------------------------------------------------
# the hook decision
# ---------------------------------------------------------------------------

def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": f"REVIEW EYE BOUNDARY: {reason}"}}


def _project_dir(data: dict) -> pathlib.Path:
    raw = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd")
    if not isinstance(raw, str) or not raw:
        raise Refusal("neither CLAUDE_PROJECT_DIR nor cwd names the project")
    return pathlib.Path(raw)


def _record_dispatch(data: dict) -> None:
    """Append the harness-observed identity of a starting subagent to the session ledger.

    Best effort and never a deny: the ledger is evidence for the record, and a
    SubagentStart hook cannot block a start anyway."""
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not SAFE_ID.match(session_id):
        return
    try:
        context = None
        if os.environ.get("FLEET_CROSS_HARNESS_REVIEW_CONTEXT") or os.environ.get("FLEET_CROSS_HARNESS_REVIEW_SHA256"):
            import cross_harness_review as cross
            context = cross.load(_project_dir(data), session_id,
                                 canonical_actor(data.get("agent_type"), _project_dir(data)))
        path = ledger_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open("a", encoding="utf-8") as ledger:
            ledger.write(json.dumps({"event": "SubagentStart",
                                     "agent_type": data.get("agent_type"),
                                     "agent_id": data.get("agent_id"),
                                     "cwd": data.get("cwd"),
                                     **record_fields(data),
                                     **({"cross_context_sha256": os.environ[cross.DIGEST_ENV]}
                                        if context else {})},
                                    sort_keys=True) + "\n")
    except (OSError, Refusal, Unproven):
        return


def decide(data: dict) -> dict | None:
    """The hook's JSON output for one tool call, or None to pass through.

    Raises Refusal for every condition under which the eye must not act."""
    event = data.get("hook_event_name")
    if event == "SubagentStart":
        _record_dispatch(data)
        return None
    if event != "PreToolUse":
        # Only the two bound events reach this hook. Anything else is a payload
        # this module does not understand, and a payload it does not understand
        # is not allowed to pass: for an eye that would be unbounded execution.
        raise Refusal(f"unexpected hook event {event!r}; only PreToolUse and SubagentStart are bound")
    agent_type = data.get("agent_type")
    if agent_type is None:
        return None  # the parent session: unbounded by design
    if not isinstance(agent_type, str) or not agent_type:
        raise Refusal("agent_type is present but not a name")
    agent_type = canonical_actor(agent_type, _project_dir(data))
    context = None
    if os.environ.get("FLEET_CROSS_HARNESS_REVIEW_CONTEXT") or os.environ.get("FLEET_CROSS_HARNESS_REVIEW_SHA256"):
        import cross_harness_review as cross
        try:
            context = cross.load(_project_dir(data), data.get("session_id"), agent_type)
        except (OSError, ValueError, Unproven) as error:
            raise Refusal(str(error)) from error
    if context is None and not is_bounded(_project_dir(data), agent_type):
        return None
    session_id, agent_id = data.get("session_id"), data.get("agent_id")
    if not isinstance(session_id, str) or not isinstance(agent_id, str):
        raise Refusal("the harness supplied no session_id/agent_id to own a scratch root by")
    root = scratch_root(session_id, agent_id)
    tool = data.get("tool_name")
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        raise Refusal("tool_input is not a mapping")
    if context is not None and tool in READ_ONLY_TOOLS:
        return None
    if tool == BASH_TOOL:
        created = ensure_scratch(root)
        if context is None:
            establish_sandbox(root)
        updated = dict(tool_input)
        updated["command"] = prepare_command(tool_input.get("command"), root, agent_type,
                                             **({"context": context} if context else {}))
        output = {"hookEventName": "PreToolUse",
                  # `updatedInput` takes effect only with an explicit decision
                  # (measured on 2.1.263); the OS boundary, not the prompt, is
                  # the control on the rewritten command.
                  "permissionDecision": "allow",
                  "updatedInput": updated}
        if context is not None:
            output["additionalContext"] = (
                f"Cross-harness review identity and scratch established for {agent_type}: "
                f"{SCRATCH_ENV}={root}; OS sandbox NOT_VERIFIED: {context['os_boundary']['reason']}. "
                "Review only the immutable candidate; create working copies in your owned scratch.")
        elif created:
            output["additionalContext"] = (
                f"REVIEW EYE BOUNDARY established for {agent_type}: {SCRATCH_ENV}={root} is "
                f"the only writable location; the subject checkout is read-only to you.")
        return {"hookSpecificOutput": output}
    if tool in PATH_TOOLS:
        raise Refusal(f"{tool} is a harness file write the boundary cannot decide at write "
                      f"time; write through Bash, inside {SCRATCH_ENV}")
    raise Refusal(f"tool {tool!r} is not covered by the boundary; an eye may not use it")


def run_hook(stdin_text: str | None = None) -> tuple[dict | None, int]:
    """(json to print or None, exit status). Never raises.

    Reads stdin ITSELF when given nothing, inside the envelope: an undecodable
    byte on stdin used to raise before the envelope existed, which exited 1 --
    a non-blocking error, i.e. the call proceeded. Measured by the Codex eye."""
    try:
        if stdin_text is None:
            stdin_text = sys.stdin.buffer.read().decode("utf-8")
        data = json.loads(stdin_text)
        if not isinstance(data, dict):
            raise Refusal("hook input is not a JSON object")
        return decide(data), 0
    except Refusal as refusal:
        return _deny(str(refusal)), 0
    except Exception as error:  # noqa: BLE001 -- an exception here would fail OPEN
        return _deny(f"internal failure, refusing rather than passing through: "
                     f"{type(error).__name__}: {error}"), 0


# ---------------------------------------------------------------------------
# check: the binding, the class, the primitive
# ---------------------------------------------------------------------------

def _frontmatter_tools(path: pathlib.Path) -> str | None:
    sys.path.insert(0, str(FLEETLIB_PARENT))
    from fleetlib.codex_twin import claude_frontmatter  # noqa: E402
    fields = claude_frontmatter(_normalised(path.read_text(encoding="utf-8")), str(path))
    return fields.get("tools")


#: The sentinel `declared_grants` returns for a contract that grants EVERY tool.
#: It is NOT the empty set: "this contract named no tools" and "this contract may
#: use nothing" are opposite facts, and reading the first as the second is what
#: let an actor holding every tool look harmless to a grant check.
UNRESTRICTED = None


def declared_grants(path: pathlib.Path) -> frozenset[str] | None:
    """The tools a contract grants, or `UNRESTRICTED` when it grants every tool.

    THE ONE PLACE THIS PROJECT DECIDES WHAT A CONTRACT MAY DO.
    The retired implementer boundary used to answer the same question with a
    hand-rolled line scanner and a DENYLIST, and the two disagreed exactly where it
    mattered: a contract with no `tools:` line is granted every tool by the harness,
    and the scanner reported "no grants at all", so an actor holding `Bash`, `Write`
    and `Edit` passed a check meant to catch it. One parser, one meaning.

    Parsing is `fleetlib.codex_twin.claude_frontmatter`, the project's only
    frontmatter authority, and it is STRICT: a frontmatter carrying anything but
    plain `key: value` lines raises rather than being half-read, so a YAML block
    list or any other shape this project does not use is refused by the parser
    instead of being silently reinterpreted here. Callers turn that raise into a
    refusal; nobody guesses a grant.

    The caller supplies the policy -- which grants it tolerates. This supplies the fact.
    """
    tools = _frontmatter_tools(path)
    if tools is None or not tools.strip():
        return UNRESTRICTED
    granted = frozenset(t.strip() for t in tools.split(",") if t.strip())
    # A line that NAMES no tool once parsed -- `tools: ,` or `tools: ,,,` -- establishes
    # no restricted grant set, so it means the same as an absent line and NOT "this
    # contract may use nothing". The empty set would be read by both callers as a
    # harmless actor: the same fail-open this function exists to close, one spelling
    # further along. Whenever the declaration does not establish a real restriction,
    # the answer is UNRESTRICTED.
    return granted or UNRESTRICTED


def _bound(entries: object, matcher: str | None, command: str | None = None) -> bool:
    """True when an entry binds `command` synchronously. An `async` hook cannot deny
    or rewrite a call, so it is not a binding at all.

    Reading a settings binding is one question: the retired implementer boundary
    answered it with a second copy until that copy drifted."""
    wanted = HOOK_COMMAND if command is None else command
    for entry in entries or []:
        if not isinstance(entry, dict) or entry.get("matcher", None) != matcher:
            continue
        for hook in entry.get("hooks") or []:
            if (isinstance(hook, dict) and hook.get("type") == "command"
                    and hook.get("command") == wanted and not hook.get("async")):
                return True
    return False


def binding_violations(root: pathlib.Path) -> list[str]:
    """Why `.claude/settings.json` does not bind this hook exactly, if it does not.

    Both bindings are required: PreToolUse is the boundary, SubagentStart is
    the only producer of the dispatch ledger -- the harness-observed record of
    which actor ran, and the one leg of review identity that is not prose."""
    path = root / SETTINGS_PATH
    if not path.is_file():
        return [f"{SETTINGS_PATH} is absent; the boundary is not bound"]
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"{SETTINGS_PATH} is unreadable: {error}"]
    hooks = settings.get("hooks") or {}
    violations = []
    if settings.get("disableAllHooks"):
        violations.append(f"{SETTINGS_PATH} sets disableAllHooks; no hook runs, so nothing binds")
    if not _bound(hooks.get("PreToolUse"), MATCHER):
        violations.append(f"{SETTINGS_PATH} binds no synchronous PreToolUse hook with matcher "
                          f"{MATCHER!r} and command {HOOK_COMMAND!r}")
    if not _bound(hooks.get("SubagentStart"), None):
        violations.append(f"{SETTINGS_PATH} binds no SubagentStart hook with command "
                          f"{HOOK_COMMAND!r}; the dispatch ledger would have no producer")
    return violations


def class_violations(root: pathlib.Path) -> list[str]:
    """Every REVIEW_EYE contract whose grants exceed what the boundary covers."""
    violations: list[str] = []
    seen: set[str] = set()
    for found in roster(root):
        path, relative, text = found.path, found.relative, found.text
        if found.problem:
            violations.append(f"{relative} {found.problem}; no actor of this roster can be "
                              f"classified while it stands")
            continue
        if found.name != path.stem:
            violations.append(f"{relative} declares name {found.name!r}, not its file stem; the "
                              f"harness would dispatch it under a name this file does not carry")
        if path.stem in seen:
            violations.append(f"{relative} declares a name another contract declares; the "
                              f"harness would dispatch one of them under it")
        seen.add(path.stem)
        role, _ = declared_role(text)
        if path.stem in EXPECTED_EYES and role != BOUNDED_ROLE:
            violations.append(f"{relative} is a pinned review eye but declares {role or 'no valid role'}; "
                              f"leaving the class is a decision recorded in EXPECTED_EYES, not an edit here")
        if role != BOUNDED_ROLE:
            continue
        try:
            granted = declared_grants(path)
        except Exception as error:  # noqa: BLE001 -- name it, do not guess
            violations.append(f"{relative} frontmatter unreadable: {error}")
            continue
        if granted is UNRESTRICTED:
            violations.append(f"{relative} declares REVIEW_EYE with no `tools` line, which "
                              f"grants every tool; an eye may hold only "
                              f"{', '.join(sorted(EYE_TOOLS))}")
            continue
        uncovered = [t for t in sorted(granted) if t not in EYE_TOOLS]
        if uncovered:
            violations.append(f"{relative} declares REVIEW_EYE and grants "
                              f"{', '.join(uncovered)}, which an eye may not hold")
    for missing in sorted(EXPECTED_EYES - seen):
        violations.append(f"{AGENTS_DIR}/{missing}.md is a pinned review eye and is absent")
    return violations


def primitive_violations() -> list[str]:
    """The sandbox primitive on this host, measured both ways at check time."""
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        inside, outside = base / "inside", base / "outside"
        inside.mkdir()
        outside.mkdir()
        try:
            argv = sandbox_argv(inside)
        except Refusal as refusal:
            return [str(refusal)]
        problems: list[str] = []
        for target, expect_ok, label in ((inside / "x", True, "inside its root"),
                                         (outside / "x", False, "outside its root")):
            result = subprocess.run([*argv, "/usr/bin/touch", str(target)],
                                    capture_output=True, text=True)
            if NESTED_SANDBOX_MARK in result.stderr:
                return ["sandbox primitive: not measurable from inside a sandbox (nested "
                        "sandbox_apply refused); run check from the unbounded parent session, "
                        "never from an eye"]
            if (result.returncode == 0) != expect_ok or target.exists() != expect_ok:
                problems.append(f"sandbox primitive: a write {label} was "
                                f"{'refused' if expect_ok else 'permitted'} "
                                f"(rc={result.returncode}, exists={target.exists()}, "
                                f"stderr={result.stderr.strip()[-200:]!r})")
    return problems


def check(root: pathlib.Path) -> list[str]:
    return binding_violations(root) + class_violations(root) + primitive_violations()


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["scratch-root"]:
        try:
            print(scratch_base())
            return 0
        except (ValueError, OSError) as error:
            print(f"Fleet scratch: {error}", file=sys.stderr)
            return 2
    if args == ["hook"]:
        output, status = run_hook()
        if output is not None:
            try:
                sys.stdout.write(json.dumps(output) + "\n")
                sys.stdout.flush()
            except Exception:  # noqa: BLE001 -- the last resort blocks rather than proceeds
                return 2
        return status
    root = REPO
    if args[:1] == ["check"] and (len(args) == 1 or (len(args) == 3 and args[1] == "--root")):
        if len(args) == 3:
            root = pathlib.Path(args[2]).resolve()
        violations = check(root)
        for v in violations:
            print(f"  FAIL  {v}")
        if violations:
            print(f"REVIEW EYE BOUNDARY: REFUSED -- {len(violations)} problem(s)")
            return 1
        eyes = [c.name for c in roster(root) if declared_role(c.text)[0] == BOUNDED_ROLE]
        print(f"  ok    {SETTINGS_PATH} binds the hook on {MATCHER}")
        print(f"  ok    bounded eyes ({len(eyes)}): {', '.join(eyes) or '-'}; every grant covered")
        print(f"  ok    sandbox primitive refuses outside a root and permits inside it")
        print("REVIEW EYE BOUNDARY: BOUND")
        return 0
    print("usage: review_eye_boundary.py hook | scratch-root | check [--root PATH]")
    return 2


if __name__ == "__main__":
    sys.exit(main())
