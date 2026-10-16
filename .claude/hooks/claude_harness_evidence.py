"""Facts exposed by Claude's process and transcript, without policy inference."""
from __future__ import annotations
import json
import pathlib
import os
import re
import subprocess
import sys

UNRESOLVED = "unresolved"
MEASURED_VERSION = "2.1.278"


def _process_argv(pid: int) -> list[str]:
    """Read argument boundaries from the OS, never from shell command text."""
    if sys.platform == "darwin":
        import ctypes
        import struct
        libc = ctypes.CDLL("libc.dylib", use_errno=True)
        mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2
        size = ctypes.c_size_t(1024 * 1024)
        buf = ctypes.create_string_buffer(size.value)
        if libc.sysctl(mib, 3, buf, ctypes.byref(size), None, 0):
            raise OSError(ctypes.get_errno(), "process arguments unavailable")
        raw = buf.raw[:size.value]
        argc = struct.unpack_from("i", raw)[0]
        pos = raw.index(b"\0", 4) + 1  # Skip executable path, not environment.
        while pos < len(raw) and raw[pos] == 0:
            pos += 1
        parts = raw[pos:].split(b"\0", argc)
        if argc < 1 or len(parts) <= argc:
            raise ValueError("incomplete process argument record")
        return [part.decode("utf-8", "surrogateescape") for part in parts[:argc]]
    if sys.platform.startswith("linux"):
        raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
        return [part.decode("utf-8", "surrogateescape") for part in raw.rstrip(b"\0").split(b"\0")]
    raise OSError("no measured process argument reader on this platform")


#: The name a native-installer versioned Claude binary carries (`2.1.296`).
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+)+")


def _is_claude_executable(executable: str) -> bool:
    """`claude`, or the versioned binary the native installer runs a session as
    (`~/.local/share/claude/versions/<ver>`). Measured 2026-10-10 on Claude Code 2.1.296: a session
    the harness continues in its daemon runs as `.../versions/2.1.296 ... --plugin-dir D`, under a
    `claude --bg-pty-host <sock> ... -- <that command>` wrapper; matching only `claude` skipped
    the session and took the wrapper, whose own arguments end at `--`, so no projection counted.
    The versioned form is admitted only in the account's native installation directory: a
    version-shaped executable under any other root is not Claude, so it can never stand between
    the hook and the session and hide that session's `--agents` (final review of
    `claude-owner-daemon-session`, ledger L1)."""
    path = pathlib.Path(executable)
    if path.name == "claude":
        return True
    return (path.parent == pathlib.Path.home() / ".local" / "share" / "claude" / "versions"
            and _VERSION.fullmatch(path.name) is not None)


def owning_claude_argv() -> list[str] | None:
    """The argv of the nearest owning Claude invocation, or None when no ancestor is one.

    The hook's actual process ancestry is the boundary. A direct non-harness invocation
    (for example the public hook CLI's fixture caller) has no owning Claude invocation.
    Unreadable ancestry raises instead of asserting what the invocation carries. The nearest
    ancestor is the session process itself, so a wrapper above it is never read; and no caller
    reads a wrapper's arguments after `--`, which are another command's, not its own.
    """
    pid = os.getppid()
    for _ in range(32):
        if pid <= 1:
            return None
        argv = _process_argv(pid)
        if argv and _is_claude_executable(argv[0]):
            return argv
        result = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)],
                                capture_output=True, text=True, check=True)
        parent = int(result.stdout.strip())
        if parent == pid:
            raise ValueError("cyclic process ancestry")
        pid = parent
    raise ValueError("owning invocation not reached")


def cli_definitions_present() -> bool:
    """Presence only in the nearest owning Claude invocation; never resolve its definitions.

    A direct non-harness invocation carries no Claude in-memory policy. Unreadable ancestry
    raises instead of asserting that shadowing is absent.
    """
    argv = owning_claude_argv()
    if argv is None:
        return False
    args = argv[1:argv.index("--")] if "--" in argv else argv[1:]
    return any(arg == "--agents" or arg.startswith("--agents=") for arg in args)



def ancestry_shadowed() -> bool:
    """`cli_definitions_present`, failing closed: unobservable ancestry counts as shadowed,
    because the effective definition is not known either."""
    try:
        return cli_definitions_present()
    except (OSError, ValueError, subprocess.SubprocessError):
        return True

def forked_skill_execution(transcript: pathlib.Path, session: str, child: str) -> str | None:
    """Exact post-execution Skill receipt; never infer a pre-dispatch launch or child ID."""
    matches = []
    for row in _transcript_records(transcript):
        result = row.get("toolUseResult")
        if not (isinstance(result, dict) and result.get("status") == "forked"
                and result.get("agentId") == child and row.get("sessionId") == session
                and row.get("version") == MEASURED_VERSION):
            continue
        content = (row.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                identity = item.get("tool_use_id")
                if isinstance(identity, str) and tool_call_version({
                        "transcript_path": str(transcript), "session_id": session,
                        "tool_use_id": identity, "tool_name": "Skill"}) == MEASURED_VERSION:
                    matches.append(identity)
    return matches[0] if len(matches) == 1 else None

def _transcript_records(transcript: pathlib.Path | None,
                        start_prompt_id: str | None = None,
                        end_prompt_ids: tuple[str, ...] = ()) -> tuple[dict, ...]:
    """Readable records in one execution slice; reactivation starts at its coordinator prompt."""
    if transcript is None or not transcript.is_file():
        return ()
    found, active = [], start_prompt_id is None
    try:
        with transcript.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record_ = json.loads(line)
                except ValueError:
                    continue
                prompt = record_.get("promptId") if record_.get("type") == "user" else None
                if active and prompt in end_prompt_ids and prompt != start_prompt_id:
                    break
                if not active and prompt == start_prompt_id:
                    active = True
                if active:
                    found.append(record_)
    except OSError:
        return ()
    return tuple(found)


def _tool_result_prompt(transcript: pathlib.Path, tool_use_id: str | None) -> str:
    """Unique child-owned fork boundary joined to the launch's exact tool-use ID."""
    matches = []
    for record_ in _transcript_records(transcript):
        content = (record_.get("message") or {}).get("content")
        if record_.get("type") == "user" and isinstance(content, list) and any(
                isinstance(item, dict) and item.get("type") == "tool_result"
                and item.get("tool_use_id") == tool_use_id for item in content):
            prompt = record_.get("promptId")
            if isinstance(prompt, str):
                matches.append(prompt)
    return matches[0] if len(matches) == 1 else UNRESOLVED


def tool_call_version(payload: dict) -> str | None:
    """Version on this exact call/current prompt, never an older session invocation.

    PreToolUse can precede the assistant call's transcript flush. Its exact prompt_id
    joins the already-written user record in that case, including after session resume.
    """
    if not all(isinstance(payload.get(key), str) for key in
               ("transcript_path", "session_id", "tool_use_id")):
        return None
    raw = payload.get("transcript_path")
    path = pathlib.Path(raw) if isinstance(raw, str) else None
    matches, prompts = [], []
    for record_ in _transcript_records(path):
        if (payload.get("prompt_id") and record_.get("type") == "user"
                and record_.get("sessionId") == payload.get("session_id")
                and record_.get("promptId") == payload.get("prompt_id")):
            prompts.append(record_.get("version"))
        content = (record_.get("message") or {}).get("content")
        if record_.get("type") == "assistant" and record_.get("sessionId") == \
                payload.get("session_id") and isinstance(content, list) and any(
                    isinstance(item, dict) and item.get("type") == "tool_use"
                    and item.get("id") == payload.get("tool_use_id")
                    and item.get("name") == payload.get("tool_name") for item in content):
            matches.append(record_.get("version"))
    values = matches or prompts
    if not values or not all(isinstance(value, str) and value for value in values):
        return None
    versions = set(values)
    return next(iter(versions)) if len(versions) == 1 else None


def transcript_models(transcript: pathlib.Path | None,
                      start_prompt_id: str | None = None,
                      end_prompt_ids: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Every runtime-recorded assistant response model in one execution slice."""
    found = []
    for record_ in _transcript_records(transcript, start_prompt_id, end_prompt_ids):
        model = (record_.get("message") or {}).get("model")
        if record_.get("type") == "assistant" and isinstance(model, str) and model:
            found.append(model)
    return tuple(found)


def parent_model(transcript: pathlib.Path | None) -> str:
    """The latest model the parent actually ran, from its response sequence.

    A generic child inherits the parent's model, so the honest way to announce it is to read
    what the parent is recorded as using rather than to restate a configured default. The
    last assistant turn wins: a session whose model was switched mid-conversation inherits the
    current one, not the one it opened with. Unreadable means `unresolved`, never a guess.
    """
    found = transcript_models(transcript)
    return found[-1] if found else UNRESOLVED


def transcript_efforts(transcript: pathlib.Path | None,
                       start_prompt_id: str | None = None,
                       end_prompt_ids: tuple[str, ...] = ()) -> tuple[str | None, ...]:
    """The runtime-recorded effort of every assistant response `transcript_models` reads, in the
    same order: its `perTurnEffort`, or None where the harness recorded none for that response.

    THE HARNESS'S OWN PER-RESPONSE RECORD. Claude 2.1.278 left it null on every record; measured
    on 2026-10-08 over the 160 most recent child transcripts on this account (2.1.285-2.1.293),
    116 carry it on every assistant response and 44 on none -- never part of one child -- and on
    `prjmgmt-dwh` (2.1.292) all 2110 child responses of session `349ecb8b` carry it, each equal to
    the governed policy of its agent. A None is a genuine absence and is never filled in.
    """
    found: list[str | None] = []
    for record_ in _transcript_records(transcript, start_prompt_id, end_prompt_ids):
        model = (record_.get("message") or {}).get("model")
        if record_.get("type") == "assistant" and isinstance(model, str) and model:
            value = record_.get("perTurnEffort")
            found.append(value if isinstance(value, str) and value else None)
    return tuple(found)


def call_efforts(transcript: pathlib.Path | None) -> dict[str, str]:
    """For every tool call in `transcript`, the `perTurnEffort` of the ONE assistant response
    that made it, in one pass: what an inheriting child launched by that call inherits. A call
    recorded by more than one response, or by a response that recorded no effort, is left out --
    the parent's later responses are never read in its place (review C1)."""
    seen: dict[str, list[str | None]] = {}
    for record_ in _transcript_records(transcript):
        content = (record_.get("message") or {}).get("content")
        if record_.get("type") != "assistant" or not isinstance(content, list):
            continue
        effort = record_.get("perTurnEffort")
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use" \
                    and isinstance(item.get("id"), str):
                seen.setdefault(item["id"], []).append(
                    effort if isinstance(effort, str) and effort else None)
    return {call: found[0] for call, found in seen.items() if len(found) == 1 and found[0]}


def transcript_effort(transcript: pathlib.Path | None,
                      start_prompt_id: str | None = None,
                      end_prompt_ids: tuple[str, ...] = ()) -> str:
    """The requested/configured effort metadata at transcript top level.

    This is not per-response execution telemetry: that is `transcript_efforts`, which a 2.1.278
    transcript leaves null while it still writes this. Callers label this value configured and
    never put it in the runtime effort field.
    """
    found = UNRESOLVED
    for record_ in _transcript_records(transcript, start_prompt_id, end_prompt_ids):
        value = record_.get("effort")
        if isinstance(value, str) and value:
            found = value
    return found




def announcement_lines(transcript: pathlib.Path | None,
                       agent_tool: str) -> dict[str, list[str]]:
    """For every recorded tool call, the assistant text lines written before it, in ONE pass.

    That is what the operator was shown just before the call: every non-empty assistant text
    line since the previous user record OR the previous `agent_tool` call, in order, up to the
    call itself -- so a call's own announcement is the LAST of them, and parallel calls each
    need their own line right before them: one line cannot announce two of them, and a line
    written before an EARLIER call in the same message is not this call's. Read at `Stop`: at
    `PreToolUse` the calling message is not on disk yet (measured, Claude Code 2.1.280).
    """
    found: dict[str, list[str]] = {}
    lines: list[str] = []
    for record_ in _transcript_records(transcript):
        content = (record_.get("message") or {}).get("content")
        if record_.get("type") == "user":
            lines = []
        elif record_.get("type") == "assistant" and isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text":
                    lines += [line for line in item.get("text", "").splitlines() if line.strip()]
                elif item.get("type") == "tool_use" and isinstance(item.get("id"), str):
                    found[item["id"]] = list(lines)
                    if item.get("name") == agent_tool:
                        lines = []
    return found


def visible_announcement(lines: list[str] | None, expected: str | None) -> str:
    """MATCH only when the LAST line written before the call EQUALS `expected`, the line the
    boundary derived for that very launch: content and placement, no field judged on its own.
    MISSING when no written line names that agent, MISMATCH otherwise, `unresolved` when there
    is no line to expect or the call is not on disk. Reported, never enforced.
    """
    if expected is None or lines is None:
        return UNRESOLVED
    if lines and lines[-1] == expected:
        return "MATCH"
    agent = next((part for part in expected.split(" | ") if part.startswith("agent: ")), None)
    return "MISMATCH" if any(line.startswith("agent launch | ") and agent in line.split(" | ")
                             for line in lines) else "MISSING"
