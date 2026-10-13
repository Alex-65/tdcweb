"""The canonical Fleet identity of a Claude subagent that runs under a session projection.

A Fleet runtime projection is a session-local Claude plugin named `fp`, loaded
with `--plugin-dir`, whose agents carry the policy catalog's model and effort for the stable
source agents of one project. The harness names such a child `fp:<source-agent>`
in every record it writes -- `SubagentStart`/`SubagentStop` and in-child tool-hook payloads,
`meta.json`, `attributionAgent`, `toolUseResult` (measured on Claude Code 2.1.281). Fleet
policy, observability and review records stay on the SOURCE name, so this module is the ONE
place that maps the runtime name back, and the one place that decides when it may not.

    canonical_identity(raw, project_dir)              live: provenance from `claude --plugin-dir`
    canonical_identity(raw, project_dir, provenance)  an already verified provenance
    recorded_identity(raw, row)        post-hoc: what a live hook recorded at the time

THE RULE. A name without the reserved prefix is returned unchanged, so ordinary agents and
foreign `plugin:name` agents keep exactly their behaviour: a foreign plugin agent is never
turned into a Fleet agent. A name under the prefix is accepted only when the ONE projection the
owning session loaded verifies and maps it to a source agent whose live contract it reproduces.
Everything else under the prefix -- malformed, unknown, no projection, a projection changed
after it was written, or a child under the RETIRED `fleet-projection:` prefix of a session
started before the rename -- raises `Unproven`. Callers decide what that costs: the OS write
boundaries refuse, the launch boundary refuses, runtime evidence reports UNPROVEN.

TWO PROJECTION KINDS (work item `policy-session-refresh-cut-1`).
* A SESSION PROJECTION is what the launcher issues now: one stable plugin directory per session,
  `<cache>/<project>/sessions/<id>/plugin`, beside its `fp.session.json`. Each agent in it is
  content-addressed: `fp:<agent>-<digest>`, where `<digest>` is the first 16 hex digits of the
  SHA-256 of the projected definition (`session_definition`). The governed dispatch boundary
  resolves the CURRENT policy at every launch, derives those bytes, writes the file if the session
  lacks it, and dispatches that exact name -- so a policy change moves only the agents it changes,
  and an already-running child keeps the name, and therefore the bytes, it was launched under.
* A LEGACY PROJECTION -- one directory per whole projection, named by its `projection_id`, with
  an `fp.provenance.json` -- is still proven, unchanged, for a session started before that work
  item, so its governed launches keep working until it is restarted. Nothing issues one any more.

WHY THE OWNING PROCESS AND NOT AN ENVIRONMENT MARKER. `--plugin-dir` on the owning `claude`
invocation is what the session actually loaded; an environment variable is inherited by any
nested process and can outlive the session that set it. Every hook, including those firing
inside a child, reaches that invocation through its own process ancestry (measured).

STDLIB ONLY, and copied wherever the hooks that import it are copied.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import importlib.util
import stat
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass

from claude_harness_evidence import owning_claude_argv

PLUGIN_NAME = "fp"
PREFIX = f"{PLUGIN_NAME}:"
PROVENANCE_FILE = f"{PLUGIN_NAME}.provenance.json"
#: Runtime-name prefixes a Fleet projection carried before, RESERVED so they never read as a
#: foreign plugin's: a session started before the rename still names its children
#: `fleet-projection:<agent>`, and returned unchanged such a name matches no contract, so neither
#: OS boundary would confine it. Every reading refuses it instead; the session must restart.
RETIRED_PREFIXES = ("fleet-projection:",)
MANIFEST_FILE = ".claude-plugin/plugin.json"
SCHEMA = "fleet-claude-projection/1"
#: THE SESSION PROJECTION. Its record sits beside the plugin directory, never inside it, so the
#: plugin's file set stays closed to the manifest and the agents.
SESSION_SCHEMA = "fleet-claude-session/1"
SESSION_FILE = "fp.session.json"
SESSION_PLUGIN_DIR = "plugin"
SESSIONS_DIR = "sessions"
#: How many hex digits of the projected definition's SHA-256 a runtime name carries.
DIGEST_CHARS = 16
_RUNTIME_SUFFIX = re.compile(rf"-([0-9a-f]{{{DIGEST_CHARS}}})\Z")
#: Where session projections are issued. Derived state, never an authority; outside every
#: repository. The launcher creates sessions here and the dispatch boundary writes only here.
CACHE_ENV = "FLEET_PROJECTION_CACHE"
DEFAULT_CACHE = pathlib.Path.home() / ".cache" / "fleet" / "claude-projections"
#: The harness's own record of which agent types the session has LOADED: a transcript attachment,
#: rewritten as a delta whenever the loaded set changes (initial load, `/reload-plugins`).
#: Measured on Claude Code 2.1.288: on disk before the `PreToolUse` hook of the next `Agent` call.
LISTING_ATTACHMENT = "agent_listing_delta"
RELOAD_ACTION = "/reload-plugins"
#: The session a hook runs for, as the harness sets it in every hook's environment (measured on
#: 2.1.288: equal to the payload's `session_id`); the Bash tool's processes inherit it. It names
#: the transcript whose listing says what that session loaded -- a reading that can only make a
#: launch wait for a reload, never let an unloaded one through (the harness refuses a name it
#: has not loaded).
SESSION_ID_ENV = "CLAUDE_CODE_SESSION_ID"
CONFIG_DIR_ENV = "CLAUDE_CONFIG_DIR"
_SESSION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{7,63}\Z")
#: A source agent name: one safe path segment, which a `:` can never be part of.
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
PROJECTION_ID = re.compile(r"[0-9a-f]{64}\Z")
#: The announcement source a projected child's policy is read from: the canon's own named-policy
#: source (`CANON.md` §Work's line, and `launch_evidence.SRC_POLICY`, which this module cannot
#: import), so the line an actor copies from `preview` is the canonical line and the frozen one.
SRC_PROJECTION = "project agent policy"
#: The label a projected launch was announced under before it took the canon's. Ledger rows that
#: carry it are still on every managed account (session 349ecb8b on prjmgmt-dwh: 26 of them), and
#: a child launched under it may stop after the redeploy, so the runtime verdict keeps reading it.
LEGACY_SRC_PROJECTION = "fleet runtime projection"
PLUGIN_DIR_FLAG = "--plugin-dir"
#: Loads a plugin from a URL, whose content no hook can enumerate.
PLUGIN_URL_FLAG = "--plugin-url"
#: Session agent definitions, which outrank plugin agents of the same name.
AGENTS_FLAG = "--agents"
#: Where a project's stable source agents live; the projection must reproduce them.
AGENTS_DIR = ".claude/agents"
#: Where a host's Fleet policy lives: the catalog, its resolver and the checkout index, deployed
#: together by the `fleet-policy-catalog` surface. An environment override exists for a session
#: the operator starts against another policy copy; a Bash child cannot reach a hook's
#: environment, which is the owning `claude` process's.
POLICY_DIR_ENV = "FLEET_POLICY_DIR"
DEFAULT_POLICY_DIR = pathlib.Path.home() / ".local" / "fleet" / "policy"
CATALOG_FILE = "fleet-policy-catalog.json"
RESOLVER_FILE = "fleet_policy_resolve.py"
CHECKOUTS_FILE = "fleet-claude-checkouts.json"
CHECKOUTS_SCHEMA = "fleet-claude-checkouts/1"
#: THE REVIEW-POINT POLICY PIN: the line a review brief carries naming the one installed policy
#: revision its WHOLE review point resolves under -- initial, repair and closure rounds, every
#: eye, both harnesses. A Codex intent carries each brief line behind `review_brief `. Any line
#: that starts as a pin and is not exactly one revision id refuses; it is never skipped.
_PIN_LINE = re.compile(r"^(?:review_brief )?POLICY-REVISION:(.*)$", re.MULTILINE)
#: A policy revision id: the deployed resolver's `CATALOG_ID_RE`, which cannot be imported here.
POLICY_REVISION = re.compile(r"policy-[0-9a-f]{16}")
_PIN_VALUE = re.compile(rf" ({POLICY_REVISION.pattern})")
#: The role a contract declares (`review_eye_boundary` classifies with this same line). Only a
#: REVIEW_EYE launch obeys a pin: every other governed dispatch resolves the current policy.
ROLE_LINE = re.compile(r"^DOCUMENTATION-REVIEW-ROLE: (\S+)$", re.MULTILINE)
REVIEW_EYE_ROLE = "REVIEW_EYE"
#: Source frontmatter a plugin agent cannot carry: Claude Code drops these for plugin agents, so a
#: projection of an agent declaring one would run with less than its source contract states.
UNSUPPORTED_KEYS = ("permissionMode", "hooks", "mcpServers")
#: A catalog-selected model or effort, as it may appear on its one projected line.
POLICY_VALUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
#: The ONLY lines a projected definition may differ from its source contract in: the policy the
#: catalog selects. Everything else -- tool grants, roles, body -- is the source's behaviour.
POLICY_KEYS = ("tier", "model", "effort")
#: The closed manifest of a projection plugin: no component paths, so no hooks, MCP servers,
#: commands or skills can ride along under a proven identity.
MANIFEST_KEYS = frozenset({"name", "version", "description"})
#: The frontmatter keys a projected definition must state exactly as its provenance entry does:
#: the harness runs the FILE, and the announcement and every verdict read the PROVENANCE.
_DECLARED = {key: re.compile(rf"^{key}:[ \t]*(\S+)[ \t]*$", re.MULTILINE)
             for key in ("name", "model", "effort")}
_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):")


class Unproven(ValueError):
    """A projected (`fp:*`, or retired-prefix) identity whose canonical source cannot be proven."""


@dataclass(frozen=True)
class Identity:
    canonical: str
    runtime: str
    projection_id: str | None = None

    def record(self) -> dict:
        """The launch-time evidence a later post-hoc reading needs; empty when unprojected."""
        if self.projection_id is None:
            return {}
        return {"canonical_agent": self.canonical, "runtime_agent": self.runtime,
                "projection_id": self.projection_id, "identity": "PROVEN"}


def is_projected(raw: object) -> bool:
    """A name under the Fleet projection prefix, current or retired: this module's to prove."""
    return isinstance(raw, str) and raw.startswith((PREFIX, *RETIRED_PREFIXES))


def _files(plugin_dir: pathlib.Path) -> dict[str, str]:
    """{relative path: sha256} of every file in the plugin but the provenance itself.

    A symlink or any non-regular entry is refused: what the digest covers must be exactly what
    the harness reads, and a link could point anywhere after the digest was taken."""
    files: dict[str, str] = {}
    for current, dirs, names in os.walk(plugin_dir, followlinks=False):
        for entry in (*dirs, *names):
            mode = os.lstat(os.path.join(current, entry)).st_mode
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise Unproven(f"{os.path.join(current, entry)} is not a regular file or "
                               "directory")
        for name in names:
            path = pathlib.Path(current, name)
            relative = path.relative_to(plugin_dir).as_posix()
            if relative != PROVENANCE_FILE:
                files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


#: THE FRONTMATTER BLOCK AS CLAUDE CODE READS IT. Measured in the 2.1.281 executable: its agent
#: loader strips a byte-order mark and matches `^---\s*\n([\s\S]*?)---\s*\n?`. Fleet reads a
#: definition with exactly that recogniser, after the same BOM strip and with line endings
#: translated as a text read translates them, so a file Claude loads is never one Fleet skips
#: (closure regression R1) and both see the same frontmatter.
_FRONTMATTER = re.compile(r"---\s*\n([\s\S]*?)---\s*\n?")


def _normalised(text: str) -> str:
    return text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


def _split(text: str) -> tuple[list[str], str]:
    """(frontmatter lines, body) of an agent definition, or `Unproven` without frontmatter."""
    match = _FRONTMATTER.match(_normalised(text))
    if match is None:
        raise Unproven("an agent definition carries no frontmatter block")
    front = match.group(1).removesuffix("\n")
    return (front.split("\n") if front else []), _normalised(text)[match.end():]


def behaviour(text: str) -> tuple[tuple[str, ...], str]:
    """A definition less the policy lines a projection replaces: what the agent DOES."""
    front, body = _split(text)
    kept = tuple(line for line in front
                 if not (match := _KEY.match(line)) or match.group(1) not in POLICY_KEYS)
    return kept, body


def projected_definition(source: str, model: str, effort: str) -> str:
    """THE projected definition of a source contract: every line but the policy lines kept as
    written, and the catalog's model and effort -- each one plain token on one line -- in their
    place. The generator writes exactly this; `_prove` accepts nothing else."""
    if not (POLICY_VALUE.match(model) and POLICY_VALUE.match(effort)) or "---" in model + effort:
        raise Unproven(f"model {model!r} / effort {effort!r} is not a plain policy token")
    front, body = _split(source)
    kept = [line for line in front
            if not ((match := _KEY.match(line)) and match.group(1) in POLICY_KEYS)]
    return "---\n" + "\n".join([*kept, f"model: {model}", f"effort: {effort}"]) + "\n---\n" + body


def declared_keys(text: str) -> set[str]:
    """The top-level frontmatter keys a definition declares."""
    return {match.group(1) for line in _split(text)[0] if (match := _KEY.match(line))}


def _named(front: list[str], body: str, name: str) -> str:
    """The definition `front` + `body` with its one `name:` line saying exactly `name`."""
    lines = [i for i, line in enumerate(front) if (m := _KEY.match(line)) and m.group(1) == "name"]
    if len(lines) != 1:
        raise Unproven(f"a projected definition must carry exactly one name line ({len(lines)})")
    front = [*front[:lines[0]], f"name: {name}", *front[lines[0] + 1:]]
    return "---\n" + "\n".join(front) + "\n---\n" + body


def session_definition(projected: str, agent: str) -> tuple[str, str, str]:
    """(runtime base `<agent>-<digest>`, full digest, file text) of one projected definition.

    THE CONTENT ADDRESS. The digest is taken over the projected definition with its name line
    written `name: <agent>`, and the file carries `name: <agent>-<digest>`: so the name the
    harness loads it under is a function of every byte it loads, and a file can be re-proven from
    its own bytes alone (`_session_agent`)."""
    front, body = _split(projected)
    digest = hashlib.sha256(_named(front, body, agent).encode("utf-8")).hexdigest()
    base = f"{agent}-{digest[:DIGEST_CHARS]}"
    return base, digest, _named(front, body, base)


def split_runtime_base(base: str) -> tuple[str, str]:
    """(agent, digest prefix) of a session runtime base `<agent>-<16 hex>`, or `Unproven`."""
    match = _RUNTIME_SUFFIX.search(base)
    agent = base[:match.start()] if match else ""
    if match is None or not SAFE_NAME.match(agent) or not SAFE_NAME.match(base):
        raise Unproven(f"{base!r} is not <one safe source-agent name>-<{DIGEST_CHARS} hex digits>")
    return agent, match.group(1)


def _session_agent(path: pathlib.Path) -> dict:
    """The verified content of one session agent file: it must be a regular file whose declared
    name is its own file stem, whose bytes are exactly the content address that name states, and
    whose policy channel is one plain model line and one effort line."""
    if not stat.S_ISREG(path.lstat().st_mode):
        raise Unproven(f"{path} is not a regular file")
    text = path.read_bytes().decode("utf-8")
    front, body = _split(text)
    base = path.name.removesuffix(".md")
    agent, prefix = split_runtime_base(base)
    if _named(front, body, base) != text:
        raise Unproven(f"{path} is not in the one form a session projection writes")
    expected_base, digest, _text = session_definition(text, agent)
    if expected_base != base or digest[:DIGEST_CHARS] != prefix:
        raise Unproven(f"{path} does not hash to the name it carries; it changed after it was "
                       "written")
    declared = "\n".join(front)
    values = {key: _DECLARED[key].findall(declared) for key in ("model", "effort")}
    if any(len(found) != 1 for found in values.values()):
        raise Unproven(f"{path} does not declare exactly one model and one effort line")
    carried = declared_keys(text) & {"tier", *UNSUPPORTED_KEYS}
    if carried:
        raise Unproven(f"{path} carries {sorted(carried)}, which a projected definition may not")
    # `canonical` is the definition as the source agent's own name declares it: what a behaviour
    # comparison with the live source contract reads.
    return {"agent": agent, "digest": digest, "model": values["model"][0],
            "effort": values["effort"][0], "text": text, "canonical": _named(front, body, agent)}


def cache_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get(CACHE_ENV) or DEFAULT_CACHE)


def load_session(plugin_dir: pathlib.Path) -> dict:
    """The verified state of one SESSION projection plugin directory, or `Unproven`.

    It must be a real directory named `plugin` under the projection cache, beside a session
    record of this schema; its file set is closed to the manifest and agent files, and every
    agent file verifies by its own content address (`_session_agent`)."""
    plugin_dir = pathlib.Path(plugin_dir)
    try:
        if not stat.S_ISDIR(plugin_dir.lstat().st_mode) or plugin_dir.name != SESSION_PLUGIN_DIR:
            raise Unproven(f"{plugin_dir} is not a real `{SESSION_PLUGIN_DIR}` directory")
        real, cache = os.path.realpath(plugin_dir), os.path.realpath(cache_dir())
        if not real.startswith(cache + os.sep):
            raise Unproven(f"{plugin_dir} is not a session projection under the projection cache "
                           f"{cache}; only Fleet issues one")
        session = json.loads((plugin_dir.parent / SESSION_FILE).read_text(encoding="utf-8"))
        manifest = json.loads((plugin_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        if not (isinstance(session, dict) and session.get("schema") == SESSION_SCHEMA
                and isinstance(session.get("project"), str)
                and isinstance(session.get("startup"), dict)
                and isinstance(session.get("startup_agents"), list)):
            raise Unproven(f"{plugin_dir.parent / SESSION_FILE} is not a {SESSION_SCHEMA} record")
        if not (isinstance(manifest, dict) and manifest.get("name") == PLUGIN_NAME
                and set(manifest) <= MANIFEST_KEYS):
            raise Unproven(f"{plugin_dir} does not carry the closed {PLUGIN_NAME!r} manifest "
                           f"({sorted(MANIFEST_KEYS)})")
        agents = {}
        for current, dirs, names in os.walk(plugin_dir, followlinks=False):
            relative = pathlib.Path(current).relative_to(plugin_dir).as_posix()
            for entry in (*dirs, *names):
                path = pathlib.Path(current, entry)
                mode = path.lstat().st_mode
                allowed = {".": {".claude-plugin", "agents"}, ".claude-plugin": {"plugin.json"}}
                if relative == "agents":
                    if not (stat.S_ISREG(mode) and entry.endswith(".md")):
                        raise Unproven(f"{path} is not an agent file")
                    info = _session_agent(path)
                    agents[entry.removesuffix(".md")] = info
                elif entry not in allowed.get(relative, ()) or not (
                        stat.S_ISDIR(mode) if entry in (".claude-plugin", "agents")
                        else stat.S_ISREG(mode)):
                    raise Unproven(f"{path} is not part of a session projection, whose file set "
                                   "is closed to its manifest and its agents")
    except (OSError, ValueError) as exc:
        if isinstance(exc, Unproven):
            raise
        raise Unproven(f"{plugin_dir}: session projection unreadable ({exc})") from exc
    return {"kind": "session", "plugin": plugin_dir, "project": session["project"],
            "startup": session["startup"], "startup_agents": session["startup_agents"],
            "agents": agents}


def materialize(plugin_dir: pathlib.Path, base: str, text: str) -> None:
    """Make `agents/<base>.md` hold exactly `text` in a session plugin directory, or `Unproven`.

    Created once, by a hard link from a file written beside the plugin, so no reader ever sees a
    partial agent and two concurrent dispatches converge on one file. A file already there with
    other bytes is never overwritten: the harness may already have loaded it under that name."""
    target = pathlib.Path(plugin_dir) / "agents" / f"{base}.md"
    data = text.encode("utf-8")
    descriptor, staged = tempfile.mkstemp(prefix=".agent-", dir=pathlib.Path(plugin_dir).parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
        os.chmod(staged, 0o644)
        try:
            os.link(staged, target)
        except FileExistsError:
            pass
    finally:
        os.unlink(staged)
    if not stat.S_ISREG(target.lstat().st_mode) or target.read_bytes() != data:
        raise Unproven(f"{target} holds other bytes than the projection it is named for")


def session_transcript() -> pathlib.Path | None:
    """This session's own transcript, or None when the environment names no single one."""
    session = os.environ.get(SESSION_ID_ENV) or ""
    if not _SESSION_ID.match(session):
        return None
    config = pathlib.Path(os.environ.get(CONFIG_DIR_ENV) or pathlib.Path.home() / ".claude")
    found = list((config / "projects").glob(f"*/{session}.jsonl"))
    return found[0] if len(found) == 1 else None


def harness_listing(transcript: pathlib.Path | str | None) -> set[str]:
    """The agent types the harness has LOADED in this session, by its own transcript record: the
    `agent_listing_delta` attachments folded in order, restarting at each initial listing.
    Empty when the transcript is absent or unreadable -- never a guess that something loaded."""
    loaded: set[str] = set()
    try:
        with open(transcript or "", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if LISTING_ATTACHMENT not in line:
                    continue
                try:
                    attachment = json.loads(line).get("attachment")
                except (ValueError, AttributeError, RecursionError):
                    continue
                if not (isinstance(attachment, dict)
                        and attachment.get("type") == LISTING_ATTACHMENT):
                    continue
                if attachment.get("isInitial"):
                    loaded = set()
                added, removed = attachment.get("addedTypes"), attachment.get("removedTypes")
                loaded |= {a for a in added if isinstance(a, str)} if isinstance(added, list) else set()
                loaded -= set(removed) if isinstance(removed, list) else set()
    except (OSError, ValueError):
        return set()
    return loaded


def _roster(project_dir: pathlib.Path) -> list[tuple[pathlib.Path, bytes]]:
    """Every file Claude Code loads as an agent of `project_dir`, and nothing else.

    MEASURED IN THE 2.1.281 EXECUTABLE: the loader lists `*.md` RECURSIVELY under the agent
    directory, hidden and git-ignored files included and symbolic links followed (`rg --files
    --hidden --follow --no-ignore --glob *.md`), and takes a file whose frontmatter `_split`
    recognises. A file without one (a README, notes) is not an agent; every file that has one is
    here, where the strict reader either reads it or refuses -- never skips it."""
    files, seen = [], set()
    for current, dirs, names in os.walk(pathlib.Path(project_dir) / AGENTS_DIR, followlinks=True):
        real = os.path.realpath(current)
        if real in seen:  # a link cycle: already listed
            dirs[:] = []
            continue
        seen.add(real)
        dirs.sort()
        for name in sorted(names):
            if name.endswith(".md"):
                raw = pathlib.Path(current, name).read_bytes()
                if _FRONTMATTER.match(_normalised(raw.decode("utf-8", "replace"))):
                    files.append((pathlib.Path(current, name), raw))
    return files


def source_definitions(project_dir: pathlib.Path) -> dict[str, str]:
    """THE ONE ROSTER READER: every live source contract of `project_dir`, by the name it
    DECLARES; `Unproven` when an agent file is not UTF-8, declares a name twice, or declares no
    single safe name, because such a roster has no single answer."""
    found: dict[str, str] = {}
    for path, raw in _roster(project_dir):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise Unproven(f"{path.name} is not UTF-8") from exc
        names = _DECLARED["name"].findall("\n".join(_split(text)[0]))
        if len(names) != 1 or not SAFE_NAME.match(names[0]) or names[0] in found:
            raise Unproven(f"{path.name} does not declare one safe name of its own ({names})")
        found[names[0]] = text
    return found


def source_definition(project_dir: pathlib.Path, name: str) -> str:
    """The ONE live source contract of `project_dir` that declares `name: <name>`."""
    found = source_definitions(project_dir)
    if name not in found:
        raise Unproven(f"no source contract under {AGENTS_DIR} of {project_dir} declares name "
                       f"{name!r}")
    return found[name]


def harness_name_key(name: str) -> str:
    """The key Claude Code matches a requested `subagent_type` by when no agent has the exact
    name. MEASURED ON 2.1.281 (the `tengu_subagent_type_normalized` branch of its executable):
    `name.normalize("NFKC").toLowerCase()` with white space, dash punctuation and `_` removed --
    so `probe_hi`, `PROBE-HI` and `probehi` all dispatch the agent `probe-hi`."""
    folded = unicodedata.normalize("NFKC", name).lower()
    return "".join(c for c in folded
                   if not (c.isspace() or c == "_" or unicodedata.category(c) == "Pd"))


def roster_names(project_dir: pathlib.Path) -> set[str]:
    """Every name an agent file of `project_dir` may be LOADED under, read as permissively as the
    harness might: quotes stripped, undecodable bytes replaced. Used only to decide that a launch
    concerns the roster at all; the strict reader then decides whether it may proceed."""
    names = set()
    for _path, raw in _roster(project_dir):
        front = "\n".join(_split(raw.decode("utf-8", "replace"))[0])
        names |= {value.strip().strip("\"'") for value in
                  re.findall(r"^name[ \t]*:(.*)$", front, re.MULTILINE)}
    return {name for name in names if name}


def projection_id_for(plugin_dir: pathlib.Path, provenance: dict) -> str:
    """THE projection identity: the plugin's file digests and its provenance, less the id."""
    body = {key: value for key, value in provenance.items() if key != "projection_id"}
    document = {"files": _files(pathlib.Path(plugin_dir)), "provenance": body}
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def load_provenance(plugin_dir: pathlib.Path) -> dict:
    """The verified provenance of one projection plugin directory, or `Unproven`."""
    plugin_dir = pathlib.Path(plugin_dir)
    try:
        if not stat.S_ISDIR(plugin_dir.lstat().st_mode):
            raise Unproven(f"{plugin_dir} is not a real directory; a symlinked projection "
                           "root can be retargeted after the session loaded it")
        provenance = json.loads((plugin_dir / PROVENANCE_FILE).read_text(encoding="utf-8"))
        manifest = json.loads((plugin_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        if not (isinstance(provenance, dict) and isinstance(manifest, dict)):
            raise Unproven("provenance or plugin manifest is not a JSON object")
        if provenance.get("schema") != SCHEMA or provenance.get("plugin") != PLUGIN_NAME \
                or manifest.get("name") != PLUGIN_NAME or not set(manifest) <= MANIFEST_KEYS:
            raise Unproven(f"not a {SCHEMA} projection of plugin {PLUGIN_NAME!r} with a closed "
                           f"manifest ({sorted(MANIFEST_KEYS)})")
        claimed, sources = provenance.get("projection_id"), provenance.get("sources")
        if not isinstance(claimed, str) or not PROJECTION_ID.match(claimed) \
                or not isinstance(sources, dict):
            raise Unproven("provenance carries no well-formed projection_id and sources")
        if projection_id_for(plugin_dir, provenance) != claimed:
            raise Unproven(f"projection {claimed[:12]} no longer matches its own digest; it "
                           "changed after it was generated")
        present = {path.relative_to(plugin_dir).as_posix() for path in plugin_dir.rglob("*")}
        closed = {".claude-plugin", MANIFEST_FILE, "agents", PROVENANCE_FILE} | {
            entry.get("file") for entry in sources.values() if isinstance(entry, dict)}
        if present != closed:
            raise Unproven(f"projection {claimed[:12]} carries {sorted(present - closed)} and "
                           f"lacks {sorted(map(str, closed - present))}; its file set is closed "
                           "to the manifest, the provenance and the agents it names")
        definitions = {}
        for name, entry in sources.items():
            if not (isinstance(name, str) and SAFE_NAME.match(name) and isinstance(entry, dict)
                    and entry.get("runtime_name") == PREFIX + name
                    and all(isinstance(entry.get(key), str) and entry.get(key)
                            for key in ("file", "model", "effort", "tier"))):
                raise Unproven(f"provenance entry {name!r} is malformed")
            definition = plugin_dir / entry["file"]
            text = definition.read_text(encoding="utf-8")
            front = "\n".join(_split(text)[0])
            wanted = {"name": name, "model": entry["model"], "effort": entry["effort"]}
            if definition.parent != plugin_dir / "agents" or any(
                    pattern.findall(front) != [wanted[key]] for key, pattern in _DECLARED.items()):
                raise Unproven(f"provenance entry {name!r} does not match the name, model and "
                               f"effort the plugin agent in {entry['file']} declares")
            definitions[name] = text
    except (OSError, ValueError) as exc:
        if isinstance(exc, Unproven):
            raise
        raise Unproven(f"{plugin_dir}: projection provenance unreadable ({exc})") from exc
    # The verified definitions travel with the provenance, so the source binding compares the
    # bytes this call verified and never a second read of the directory.
    return {**provenance, "_definitions": definitions}


def plugin_dirs(argv: list[str]) -> list[pathlib.Path]:
    """Every `--plugin-dir` an owning invocation's argv names, in order."""
    args = argv[1:argv.index("--")] if "--" in argv else argv[1:]
    found = []
    for i, arg in enumerate(args):
        if arg == PLUGIN_DIR_FLAG and i + 1 < len(args):
            found.append(args[i + 1])
        elif arg.startswith(PLUGIN_DIR_FLAG + "="):
            found.append(arg.split("=", 1)[1])
    return [pathlib.Path(value) for value in found]


def active_projection() -> dict:
    """The verified state of the ONE projection the owning session loaded, or `Unproven`: a
    session projection (`load_session`, `kind` "session") or, for a session started before
    session projections, a legacy one (`load_provenance`)."""
    plugin_dir = _active_plugin_dir()
    if os.path.lexists(plugin_dir / PROVENANCE_FILE):
        return load_provenance(plugin_dir)
    return load_session(plugin_dir)


def _active_plugin_dir() -> pathlib.Path:
    """The ONE `fp` plugin directory the owning session loaded, or `Unproven`."""
    try:
        argv = owning_claude_argv()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise Unproven(f"the owning Claude invocation is unobservable ({exc})") from exc
    if argv is None:
        raise Unproven("no owning Claude invocation, so no projection was loaded")
    args = argv[1:argv.index("--")] if "--" in argv else argv[1:]
    if any(arg == AGENTS_FLAG or arg.startswith(AGENTS_FLAG + "=") for arg in args):
        raise Unproven(f"the owning invocation defines agents by {AGENTS_FLAG}, which outrank "
                       "plugin agents, so the projected definition is not proven to be the one "
                       "that runs")
    if any(arg == PLUGIN_URL_FLAG or arg.startswith(PLUGIN_URL_FLAG + "=") for arg in args):
        raise Unproven(f"the owning invocation loads a plugin by {PLUGIN_URL_FLAG}, which cannot "
                       "be enumerated, so no count of loaded projections is complete")
    # EVERY plugin source is enumerated or the count is refused: a `.zip`, a folder of plugins
    # or an unreadable manifest could hold a second projection this count would never see.
    candidates = []
    for directory in plugin_dirs(argv):
        if not directory.is_absolute():
            raise Unproven(f"--plugin-dir {directory} is relative; a projection is loaded by "
                           "absolute path")
        try:
            manifest = json.loads((directory / MANIFEST_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Unproven(f"--plugin-dir {directory} carries no readable plugin manifest of its "
                           f"own, so the plugins it loads cannot be enumerated ({exc})") from exc
        if not isinstance(manifest, dict) or not isinstance(manifest.get("name"), str):
            raise Unproven(f"--plugin-dir {directory} carries a manifest with no plugin name")
        if manifest["name"] == PLUGIN_NAME:
            candidates.append(directory)
    if len(candidates) != 1:
        raise Unproven(f"the owning Claude invocation loaded {len(candidates)} "
                       f"{PLUGIN_NAME} plugin directories; exactly one is required")
    return candidates[0]


def policy_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get(POLICY_DIR_ENV) or DEFAULT_POLICY_DIR)


#: The machine identity Fleet's runner registers a macOS executor by.
_MAC_UUID = re.compile(r'"IOPlatformUUID"\s*=\s*"([0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12})"')


def account_identity() -> tuple[str, str]:
    """(machine_id_sha256, home) of the account this process runs as, by THE SAME rule Fleet's
    runner registers an executor by (`console/collector/remote/src/identity.py`), so an index
    scope naming an account matches exactly the account Fleet registered. This module is
    deployed alone and cannot import the runner, hence the restatement. Anything it cannot
    establish is `Unproven`, never "some other account"."""
    home = os.environ.get("HOME")
    if not home or not home.startswith("/") or home != os.path.normpath(home) or "\0" in home:
        raise Unproven("this account's home is not established ($HOME)")
    try:
        if os.uname().sysname == "Linux":
            raw = pathlib.Path("/etc/machine-id").read_bytes().strip()
            if not re.fullmatch(rb"[0-9a-f]{32}", raw):
                raise ValueError("/etc/machine-id is not 32 lowercase hex digits")
        elif os.uname().sysname == "Darwin":
            out = subprocess.run(["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                 timeout=10, check=False)
            match = _MAC_UUID.search(out.stdout) if out.returncode == 0 else None
            if match is None:
                raise ValueError("no IOPlatformUUID")
            raw = match.group(1).encode("ascii")
        else:
            raise ValueError(f"unsupported platform {os.uname().sysname}")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise Unproven(f"this host's machine identity cannot be established ({exc})") from exc
    return "sha256:" + hashlib.sha256(raw).hexdigest(), home


def _read_checkout_index(path: pathlib.Path) -> tuple[dict, dict | None]:
    """(checkouts, account scopes or None) of a checkout index; `Unproven` if it is malformed.

    An index without `accounts` predates the account scope, and every path in it applies to
    every account that holds it -- the reading it always had, which governs MORE, never less."""
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
        checkouts = index["checkouts"]
        if index.get("schema") != CHECKOUTS_SCHEMA or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in checkouts.items()):
            raise ValueError("not a checkout index")
        scopes = index["accounts"] if "accounts" in index else None
        if "accounts" in index and not (isinstance(scopes, dict) and all(
                isinstance(scope, dict) and isinstance(scope.get("machine_id_sha256"), str)
                and isinstance(scope.get("home"), str)
                and isinstance(scope.get("checkouts"), list)
                and all(isinstance(p, str) and p in checkouts for p in scope["checkouts"])
                for scope in scopes.values())):
            raise ValueError("malformed account scopes")
        if scopes is not None and {p for scope in scopes.values()
                                   for p in scope["checkouts"]} != set(checkouts):
            # Every indexed path belongs to some account: a scope table that leaves one out
            # would make its owner read it as foreign.
            raise ValueError("account scopes do not cover every indexed checkout")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise Unproven(f"{path}: the checkout index cannot be read ({exc})") from exc
    return checkouts, scopes


def governed_root(project_dir: pathlib.Path | str) -> tuple[pathlib.Path, str] | None:
    """(checkout root, project id) of the Fleet-governed checkout `project_dir` lies in, or None.

    The NEAREST indexed ancestor that is THIS account's checkout wins, because checkouts nest
    (`/data1/projects` holds the `/data1/projects/CriptoTread` checkout of another project), a
    session started below its checkout's root is still that checkout's, and a path another
    account's target names (`/data1/argus` on mioh1, a directory of another kind on dwh) is not
    a checkout here. Nothing about the path itself is consulted: a governed checkout whose
    directory is missing, unreadable or not a Git repository stays governed. No index deployed
    means nothing is governed; an index that cannot be read, or an account identity that cannot
    be established or that no scope lists where a scope must be matched, is `Unproven`, never
    "not governed"."""
    path = policy_dir() / CHECKOUTS_FILE
    if not os.path.lexists(path):
        return None
    checkouts, scopes = _read_checkout_index(path)
    # `mine` is the set of paths that are checkouts HERE (None: an unscoped index, every path);
    # `refusal` is why this account cannot tell, raised only if the walk reaches an indexed path.
    mine: set[str] | None = None
    refusal: Unproven | None = None
    resolve: set[str] = set(checkouts)
    if scopes is not None:
        try:
            identity = account_identity()
            listed = [scope for scope in scopes.values()
                      if (scope["machine_id_sha256"], scope["home"]) == identity]
            if not listed:
                # The index is installed only on accounts it lists, so an account it does not
                # list has drifted from its registration (or the index is wrong): it cannot
                # tell its own checkouts, and that is not "none".
                raise Unproven(f"{path}: this account ({identity[1]}) is listed in no scope "
                               "of the checkout index; re-register it or redeploy the index")
            mine = resolve = {p for scope in listed for p in scope["checkouts"]}
        except Unproven as exc:
            refusal, mine = exc, set()
    # An indexed checkout that is itself a symlink is also reached by its physical spelling,
    # which a caller whose directory is already resolved presents. Resolving a key only ADDS a
    # spelling; a key that cannot be resolved keeps its own. Only this account's keys are
    # resolved when it is known which they are, so another account's paths cost nothing.
    spellings = {key: key for key in checkouts}
    for key in sorted(resolve):
        spellings.setdefault(os.path.realpath(key), key)
    for start in (pathlib.Path(os.path.abspath(project_dir)),
                  pathlib.Path(os.path.realpath(project_dir))):
        for candidate in (start, *start.parents):
            key = spellings.get(str(candidate))
            if key is None:
                continue
            if refusal is not None:
                raise refusal
            if mine is not None and key not in mine:
                continue
            return candidate, checkouts[key]
    return None


def _resolver():
    """The deployed resolver beside the catalog: the one reader of what a tier resolves to."""
    path = policy_dir() / RESOLVER_FILE
    spec = importlib.util.spec_from_file_location("fleet_policy_resolve", path)
    if spec is None or spec.loader is None:
        raise Unproven(f"{path}: no policy resolver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_policy(project: str, agent: str, revision: str | None = None) -> dict:
    """{catalog_id, tier, model, effort} the CURRENT catalog -- or the exact retained
    `revision` -- selects for one project agent."""
    return resolve_policy_for(project, agent, "claude", "agent_definition", revision=revision)


def installed_policy(revision: str | None = None) -> dict:
    """THE installed policy catalog: CURRENT, or the exact retained `revision`, verified by the
    deployed resolver (`load_policy`). A missing, corrupt or mismatched revision raises; nothing
    is fetched, rebuilt or substituted.

    A DEPLOYED RESOLVER THAT PREDATES THE STORE (no `load_policy`) cannot have activated a
    revision: the push that installs the store installs that resolver in the same session,
    before it moves the pointer. Its CURRENT is therefore the legacy catalog beside it -- the
    rollout window in which this module is newer than the account's policy files -- and the one
    exact revision such an account holds is that catalog, whose id `load_catalog` re-derives
    from its bytes: a pin naming any other revision refuses."""
    resolver = _resolver()
    if not hasattr(resolver, "load_policy"):
        catalog = resolver.load_catalog(policy_dir() / CATALOG_FILE)
        if revision is not None and catalog["catalog_id"] != revision:
            raise Unproven(f"the installed policy resolver predates the revision store and this "
                           f"account holds only {catalog['catalog_id']}, so policy revision "
                           f"{revision} cannot be resolved here")
        return catalog
    return resolver.load_policy(policy_dir(), revision)


def policy_revision(revision: str | None = None) -> str:
    """The proven id of the CURRENT installed policy, or of `revision` once it is proven
    retained and intact -- what a review point pins (`tools/verify_full.py`) and re-proves
    (`tools/review_closure.py`). Every failure to prove raises `Unproven`."""
    try:
        return installed_policy(revision)["catalog_id"]
    except BaseException as exc:  # noqa: BLE001 -- an unprovable pin refuses, never guesses
        raise Unproven(f"policy revision {revision or 'current'} cannot be proven on this "
                       f"account ({type(exc).__name__}: {exc})") from exc


def policy_pin(text: object) -> str | None:
    """The one policy revision `text` (a brief, an Agent prompt, a Codex intent) pins, None when
    it carries no pin line, `Unproven` when a pin line is malformed or two disagree."""
    if not isinstance(text, str):
        return None
    pinned = set()
    for value in _PIN_LINE.findall(text):
        match = _PIN_VALUE.fullmatch(value)
        if match is None:
            raise Unproven(f"a POLICY-REVISION line does not name one policy revision: {value!r}")
        pinned.add(match.group(1))
    if len(pinned) > 1:
        raise Unproven(f"the brief pins {len(pinned)} different policy revisions "
                       f"{sorted(pinned)}: a review point has exactly one")
    return next(iter(pinned), None)


def review_pin(source: str, prompt: object) -> str | None:
    """The revision a launch of the agent whose contract is `source` must resolve under: the
    prompt's pin for a REVIEW_EYE contract, None (CURRENT) for every other agent."""
    if ROLE_LINE.findall(source) != [REVIEW_EYE_ROLE]:
        return None
    return policy_pin(prompt)


def resolve_delicate_for(harness: str, path: str) -> dict:
    """{catalog_id, tier, model, effort} of the CURRENT installed policy's delicate escalation on
    one (harness, dispatch path), for an agent the catalog need not register."""
    catalog = installed_policy()
    resolver = _resolver()
    if hasattr(resolver, "resolve_delicate"):
        resolved = resolver.resolve_delicate(catalog, harness, path)
        return {"catalog_id": catalog["catalog_id"], "tier": resolved["tier"],
                "model": resolved["model"], "effort": resolved["effort"]}
    # A RESOLVER THAT PREDATES THE STORE has no project-free entry point; its catalog, verified
    # by its own `load_catalog`, is read exactly as its `resolve(..., delicate=True)` reads it.
    capability = catalog["harnesses"].get(harness, {}).get("paths", {}).get(path)
    if not isinstance(capability, dict) or capability.get("delicate_dispatch") != "SUPPORTED":
        raise Unproven(f"delicate dispatch is UNSUPPORTED on harness {harness!r} path {path!r}")
    tier = catalog["delicate_tier"]
    row = catalog["tiers"][tier].get(harness)
    if not isinstance(row, dict):
        raise Unproven(f"tier {tier!r} declares no row for harness {harness!r}")
    return {"catalog_id": catalog["catalog_id"], "tier": tier, "model": row["model"],
            "effort": row["effort"] if capability.get("effort") == "PINNABLE" else None}


def resolve_policy_for(project: str, agent: str, harness: str, path: str, *,
                       delicate: bool = False, revision: str | None = None) -> dict:
    """{catalog_id, tier, model, effort} the CURRENT catalog selects for one (project, agent,
    harness, dispatch path[, delicate?]). THE SAME RESOLVER the Claude governed launch uses
    (`canonical/policy/fleet_policy_resolve.py`), parameterised by harness and path so a
    governed Codex launch shares one meaning of a tier with the governed Claude launch rather
    than a second resolver that happens to agree with it today. `delicate=True` resolves the
    catalog's configured `delicate_tier` instead of the ordinary project/agent mapping,
    whatever tier was assigned, exactly as the resolver's own `--delicate` does for a
    non-governed dispatch -- so a governed delicate launch shares that ONE meaning too, rather
    than a second delicate source (`tools/tiers.yaml`) the catalog cannot govern. Raises
    `TierError` (from the resolver module) on any unresolvable coordinate -- unknown project,
    agent, harness, path or tier, or a delicate dispatch the harness/path does not support --
    exactly as `resolve_policy` above always has for the Claude case. `revision` None is the
    CURRENT installed policy; a revision id is that exact retained revision, or a refusal."""
    resolver = _resolver()
    catalog = installed_policy(revision)
    resolved = resolver.resolve(catalog, project, agent, harness, path, delicate=delicate)
    return {"catalog_id": catalog["catalog_id"], "tier": resolved["tier"],
            "model": resolved["model"], "effort": resolved["effort"]}


def canonical_identity(raw: str, project_dir: pathlib.Path | str | None = None,
                       provenance: dict | None = None) -> Identity:
    """The canonical identity of a runtime subagent name, or `Unproven` for a projected one
    that cannot be proven. `provenance` None reads the live, verified active projection.

    A projected definition is its source agent only when it DOES what the live source contract
    of `project_dir` does: every line but the policy lines, and the body, equal. A projection
    that grants another tool, carries another role or another body, or predates a change to the
    source, is not that agent, whatever its own provenance says."""
    if not is_projected(raw):
        return Identity(raw, raw)
    return _fail_closed(raw, lambda: _prove(raw, project_dir, provenance))


def _fail_closed(raw: str, verify):
    """Run one projected-identity verification. ANY failure inside it is a failure to prove:
    a verification that crashes must never reach a launch hook as an error that lets the launch
    proceed, so every exception but `Unproven` itself becomes one."""
    try:
        return verify()
    except Unproven:
        raise
    # BaseException: the deployed resolver is executed here, and a `SystemExit` escaping it would
    # end the hook with a NON-blocking status -- a launch that starts unproven (measured).
    except BaseException as exc:  # noqa: BLE001 -- the fail-closed boundary of this module
        raise Unproven(f"{raw!r} could not be verified ({type(exc).__name__}: {exc})") from exc


def _refuse_retired(raw: str) -> None:
    if raw.startswith(RETIRED_PREFIXES):
        raise Unproven(f"{raw!r} carries a retired projection prefix: its session was started "
                       f"before the projection was renamed {PLUGIN_NAME!r}; restart it")


def _prove(raw: str, project_dir: pathlib.Path | str | None, provenance: dict | None) -> Identity:
    _refuse_retired(raw)
    name = raw[len(PREFIX):]
    if not SAFE_NAME.match(name):
        raise Unproven(f"{raw!r} is not {PREFIX}<one safe source-agent name>")
    provenance = active_projection() if provenance is None else provenance
    if provenance.get("kind") == "session":
        return _prove_session(raw, project_dir, provenance)
    entry = provenance.get("sources", {}).get(name)
    if not isinstance(entry, dict) or entry.get("runtime_name") != raw:
        raise Unproven(f"{raw!r} is not a source agent of projection "
                       f"{str(provenance.get('projection_id'))[:12]}")
    if project_dir is None:
        raise Unproven(f"{raw!r} names no project whose source contract it could be bound to")
    # PROVEN AGAINST THE ROSTER THE BOUNDARIES CLASSIFY: the session's own project directory,
    # never an indexed ancestor -- a nested checkout proven against its root's contract would be
    # classified against its own roster and pass unbounded (review finding L5).
    projected = provenance.get("_definitions", {}).get(name, "")
    if behaviour(projected) != behaviour(source_definition(pathlib.Path(project_dir), name)):
        raise Unproven(f"{raw!r} does not reproduce the live source contract of {name!r}; "
                       f"only {', '.join(POLICY_KEYS)} may differ")
    # The policy channel is exactly one plain model line and one effort line (checked against the
    # provenance by `load_provenance`): a `tier:` line could carry a multi-line value the line
    # comparison above drops, so a projection carries none.
    carried = declared_keys(projected)
    if "tier" in carried or carried & set(UNSUPPORTED_KEYS):
        raise Unproven(f"{raw!r} carries {sorted(carried & {'tier', *UNSUPPORTED_KEYS})}, which "
                       "a projected definition may not")
    return Identity(name, raw, provenance["projection_id"])


def _prove_session(raw: str, project_dir: pathlib.Path | str | None, session: dict) -> Identity:
    """`fp:<agent>-<digest>` against a verified session projection: the file of that exact name
    is in it (and so already verified by its own content address), and it does what the live
    source contract of `project_dir` does. No policy is re-resolved here, so a child launched
    under one policy stays proven after the catalog moves on: its name pins its bytes."""
    base = raw[len(PREFIX):]
    agent, _prefix = split_runtime_base(base)
    info = session["agents"].get(base)
    if info is None:
        raise Unproven(f"{raw!r} is not an agent of this session's projection "
                       f"{session['plugin']}")
    if project_dir is None:
        raise Unproven(f"{raw!r} names no project whose source contract it could be bound to")
    source = source_definition(pathlib.Path(project_dir), agent)
    # The source's own name line, which `source_definitions` proved declares `agent`, spelled as
    # the session file's canonical form spells it (`name:  x`, `name:x` are the same agent).
    if behaviour(info["canonical"]) != behaviour(_named(*_split(source), agent)):
        raise Unproven(f"{raw!r} does not reproduce the live source contract of {agent!r}; "
                       f"only {', '.join(POLICY_KEYS)} may differ")
    return Identity(agent, raw, info["digest"])


#: THE MATERIALIZED FLEET WRITE BOUNDARY a governed checkout may carry, and the CURRENCY AND
#: BINDING contract `boundary_problems` holds it to. `tools/review_eye_boundary_render.py`
#: materializes it into a project's own `.claude/hooks`; this module has no access to that
#: renderer on a managed account (deployed alone, stdlib only), so its paths, commands and
#: matchers are spelled here as literals -- pinned equal to the renderer's own constants by a
#: test, so neither drifts silently. The dispatch layer that used to be materialized beside it
#: (the P1-0 implementer boundary and a project-local copy of the launch hook) is retired: the
#: Fleet-managed user-level launch binding enforces governed launches in a checkout that binds
#: no launch hook of its own (work item `policy-control-plane-cut-4-binding-fail-closed-and-p1-residue`).
BOUNDARY_HOOKS_DIR = ".claude/hooks"
#: The review-eye layer: the hook itself (its one per-roster substitution normalised out before
#: comparison, below) and the two modules it imports at runtime. `fleetlib/{__init__,codex_twin}.py`
#: is excluded: the renderer's own `check` reads it for its OWN parsing, but the hook never
#: imports it at runtime, so it carries no currency requirement here.
REVIEW_EYE_LAYER = ("review_eye_boundary.py", "claude_projection_identity.py",
                    "claude_harness_evidence.py")
#: `review_eye_boundary.MATCHER`, a fixed alphabetic join of `COVERED_TOOLS`.
_REVIEW_EYE_MATCHER = "^(Bash|Edit|MultiEdit|NotebookEdit|Write)$"
_REVIEW_EYE_COMMAND = f'python3 -B "$CLAUDE_PROJECT_DIR/{BOUNDARY_HOOKS_DIR}/review_eye_boundary.py" hook'
#: The renderer's one intentional per-roster substitution in `review_eye_boundary.py`: normalised
#: out of both the materialized file and the reference before a currency comparison, so a render
#: that differs only in which contracts it names as eyes is still CURRENT. Same regex as
#: `review_eye_boundary_render.EXPECTED_EYES_STATEMENT`; pinned equal by a test.
_EXPECTED_EYES_STATEMENT = re.compile(r"^EXPECTED_EYES = frozenset\(\{[^}]*\}\)\n", re.MULTILINE)
_EXPECTED_EYES_PLACEHOLDER = "EXPECTED_EYES = frozenset(<per-roster>)\n"


def _currency_bytes(name: str, data: bytes) -> bytes:
    """`data`, with `review_eye_boundary.py`'s one per-roster substitution normalised away."""
    if name != "review_eye_boundary.py":
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return _EXPECTED_EYES_STATEMENT.sub(lambda _match: _EXPECTED_EYES_PLACEHOLDER,
                                        text).encode("utf-8")


def _member_problem(hooks_dir: pathlib.Path, name: str) -> str | None:
    """None when `hooks_dir / name` is CURRENT: a regular file whose bytes equal the reference
    module of the same name beside this one. Anything else -- missing, a symlink or other
    non-regular entry, unreadable, stale -- is a problem string; never raises."""
    path = hooks_dir / name
    try:
        target_mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        return f"{path} is missing ({exc})"
    except OSError as exc:
        return f"{path} cannot be inspected ({exc})"
    if not stat.S_ISREG(target_mode):
        return (f"{path} is not a regular file; a symlink or other non-regular entry could be "
               "retargeted after this check ran")
    reference = pathlib.Path(__file__).resolve().parent / name
    try:
        reference_bytes = reference.read_bytes()
    except OSError as exc:
        return f"{reference}: no reference copy to verify {path} against ({exc})"
    try:
        target_bytes = path.read_bytes()
    except OSError as exc:
        return f"{path}: unreadable ({exc})"
    if _currency_bytes(name, target_bytes) != _currency_bytes(name, reference_bytes):
        return (f"{path} does not equal its current reference {reference}; re-render this "
               "checkout's boundaries")
    return None


def _layer_carried(hooks_dir: pathlib.Path, members: tuple[str, ...]) -> bool:
    """True when ANY member exists, as a file or a symlink -- `lstat` succeeds regardless of
    what kind of entry is there; `_member_problem` above decides whether that entry is current.
    Only a member that is really ABSENT leaves a layer uncarried: a directory that cannot be
    searched says nothing about what it holds, so it counts as carried and fails closed."""
    for name in members:
        try:
            hooks_dir.joinpath(name).lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError:
            return True
        return True
    return False


def _settings_object(path: pathlib.Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _disables_hooks(root: pathlib.Path) -> bool:
    return any(_settings_object(root / rel).get("disableAllHooks")
              for rel in (".claude/settings.json", ".claude/settings.local.json"))


def _hook_bound(entries: object, matcher: str | None, command: str) -> bool:
    """True when a synchronous command hook binds `command` on `matcher`: the exact shape
    `review_eye_boundary._bound` requires."""
    for entry in entries if isinstance(entries, list) else ():
        if not isinstance(entry, dict) or entry.get("matcher", None) != matcher:
            continue
        for hook in entry.get("hooks") or []:
            if (isinstance(hook, dict) and hook.get("type") == "command"
                    and hook.get("command") == command and not hook.get("async")):
                return True
    return False


#: THE SOURCE LAYOUT: the repository that OWNS these boundaries binds them straight from its
#: `tools/` directory (`review_eye_boundary._layout`) rather than from a materialized
#: `.claude/hooks`. Governed like any other project (work item `claude-fleet-governed-roster`),
#: it owes the same bindings and the same hook-enabled state -- review findings F2/S1: without
#: this, such a checkout was admitted as carrying no boundary at all. No byte currency applies
#: there: those files ARE the reference a materialized copy is compared against, and a working
#: checkout is routinely ahead of the bundle an account has installed.
SOURCE_BOUNDARY_DIR = "tools"


def _source_bindings() -> tuple[tuple[str, str | None, str], ...]:
    """The review-eye bindings of the source layout: the materialized layer's own bindings with
    `.claude/hooks` replaced by `tools`, so the two can never disagree."""
    command = _REVIEW_EYE_COMMAND.replace(f"/{BOUNDARY_HOOKS_DIR}/", f"/{SOURCE_BOUNDARY_DIR}/")
    return (("PreToolUse", _REVIEW_EYE_MATCHER, command), ("SubagentStart", None, command))


def boundary_problems(root: pathlib.Path | str) -> list[str]:
    """Every reason the materialized Fleet write boundaries `root` carries would not confine a
    projected identity: a stale or symlinked member, a missing or disabled binding. Never raises
    -- a read failure anywhere IS a problem, so a checkout this cannot fully inspect fails closed.

    A checkout carrying the boundary in neither `.claude/hooks` nor the source layout's `tools/`
    returns `[]`: it has no boundary to disagree with, and is admitted unchanged. The source
    layout owes its bindings and hook-enabled state (`SOURCE_BOUNDARY_DIR`), not byte currency.
    Carrying the materialized layer means every one of its members must be CURRENT (a regular
    file, byte-equal to the reference copy beside this module) and every one of its bindings
    must be present and enabled. Called by `claude_runtime_projection.generate` at issuance
    and by `_launch_policy` at every governed named launch, so a `.claude/hooks` reset mid-session
    or a manual `--plugin-dir` bypass is caught at the moment of use, not only at issuance."""
    try:
        checkout = pathlib.Path(root)
        hooks_dir = checkout / BOUNDARY_HOOKS_DIR
        review_eye_carried = _layer_carried(hooks_dir, REVIEW_EYE_LAYER)
        source_dir = checkout / SOURCE_BOUNDARY_DIR
        source_eye = _layer_carried(source_dir, ("review_eye_boundary.py",))
        if not (review_eye_carried or source_eye):
            return []
        problems: list[str] = []
        if _disables_hooks(checkout):
            problems.append(f"{checkout}: disableAllHooks is set; no Fleet write boundary "
                            "would run")
        settings = _settings_object(checkout / ".claude" / "settings.json")
        hooks = settings.get("hooks") if isinstance(settings.get("hooks"), dict) else {}
        for event, matcher, command in (_source_bindings() if source_eye else ()):
            if not _hook_bound(hooks.get(event), matcher, command):
                where = f"{event} {matcher}" if matcher else event
                problems.append(f"{checkout}/.claude/settings.json does not bind {where} "
                                f"to {command}")
        if review_eye_carried:
            problems += [p for name in REVIEW_EYE_LAYER
                        if (p := _member_problem(hooks_dir, name)) is not None]
            if not _hook_bound(hooks.get("PreToolUse"), _REVIEW_EYE_MATCHER, _REVIEW_EYE_COMMAND):
                problems.append(f"{checkout}/.claude/settings.json does not bind PreToolUse "
                                f"{_REVIEW_EYE_MATCHER} to {_REVIEW_EYE_COMMAND}")
            if not _hook_bound(hooks.get("SubagentStart"), None, _REVIEW_EYE_COMMAND):
                problems.append(f"{checkout}/.claude/settings.json does not bind SubagentStart "
                                f"to {_REVIEW_EYE_COMMAND}")
        return problems
    except Exception as exc:  # noqa: BLE001 -- fail closed: an inspection failure IS a problem
        return [f"{root}: boundary currency could not be inspected "
               f"({type(exc).__name__}: {exc})"]


def payload_project(payload: dict) -> str | None:
    """The project a hook payload runs in, in the order every Fleet hook reads it."""
    return os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or None


def record_fields(payload: dict) -> dict:
    """Launch-time evidence for one hook payload's runtime name, never raising: a live hook
    records what it proved, or that it could not prove it, and a later reading trusts nothing
    else."""
    raw = payload.get("agent_type")
    if not is_projected(raw):
        return {}
    try:
        return canonical_identity(raw, payload_project(payload)).record()
    except Unproven as exc:
        return {"runtime_agent": raw, "identity": f"UNPROVEN: {exc}"}


def recorded_identity(raw: str, row: dict | None) -> Identity:
    """Post-hoc: the identity a live hook proved for `raw` and recorded in `row`, or
    `Unproven`. An unprefixed name needs no record and is returned unchanged."""
    if not is_projected(raw):
        return Identity(raw, raw)
    row = row if isinstance(row, dict) else {}
    canonical, projection = row.get("canonical_agent"), row.get("projection_id")
    if not (row.get("identity") == "PROVEN" and row.get("runtime_agent") == raw
            and isinstance(canonical, str)
            and isinstance(projection, str) and PROJECTION_ID.match(projection)
            # a legacy runtime name, or a session one whose digest IS the recorded projection
            and raw in (PREFIX + canonical,
                        f"{PREFIX}{canonical}-{projection[:DIGEST_CHARS]}")):
        raise Unproven(f"{raw!r} has no launch-time proof recorded "
                       f"({row.get('identity') or 'no record'})")
    return Identity(canonical, raw, projection)


def child_identity(raw: object, row: dict | None, unresolved: str) -> tuple[str, dict]:
    """(the name a runtime reading compares, the identity evidence it carries) for one child.

    A projected name counts only as the source a live hook proved and recorded in `row`; one
    without that proof reads as `unresolved`, so no verdict can pass on it, and the evidence says
    why. An unprojected name is returned as it is, with no evidence to add."""
    if not isinstance(raw, str) or not raw:
        return unresolved, {}
    if not is_projected(raw):
        return raw, {}
    try:
        identity = recorded_identity(raw, row)
    except Unproven as exc:
        return unresolved, {"runtime_agent": raw, "identity": f"UNPROVEN: {exc}"}
    return identity.canonical, identity.record()


def launch_policy(name: str, project_dir: pathlib.Path | str, prompt: object = None) -> dict | None:
    """THE decision for one named `Agent` launch: None where no projection governs it, else the
    proven projection's policy for it, else `Unproven` -- the launch hook refuses.

    * An unprojected name outside a Fleet-governed checkout, or one no source contract of the
      checkout declares (a built-in, a plugin agent), is None: its launch is not this module's.
    * A SOURCE name in a governed checkout is launched only through the session's projection:
      the result carries `rewrite`, the runtime name the hook dispatches instead, and a session
      without a valid projection is refused before dispatch rather than run on the legacy fields
      of the source file.
    * A RUNTIME name (`fp:<name>`) is proven the same way; one under a retired prefix is refused.
    In a governed checkout the projection must also be FOR that project and CURRENT. A SESSION
    projection is made current here, per agent (`_session_launch`): the policy in force is
    resolved now, its exact definition is written into the session if missing, and the launch
    goes to that content-addressed name -- refused, with the operator's one action, while the
    harness has not loaded it yet (`session_transcript`, `harness_listing`). A LEGACY projection
    must have been generated from the catalog in force, whole, as before.

    THE POLICY IN FORCE is the CURRENT installed policy, except for a REVIEW_EYE contract whose
    `prompt` pins a review point's revision (`review_pin`): that launch resolves the exact
    retained revision, and refuses when it is missing or unverifiable -- never the current one."""
    return _fail_closed(name, lambda: _launch_policy(name, project_dir, prompt))


def _launch_policy(name: str, project_dir: pathlib.Path | str, prompt: object = None) -> dict | None:
    projected = is_projected(name)
    _refuse_retired(name)  # before any projection is read: the reason is the session's age
    governed = governed_root(project_dir)
    if not projected:
        if governed is None:
            return None
        # WHICH ROSTER AGENT THE HARNESS WOULD DISPATCH: exact, or by its normalised key. A
        # name no agent file may be loaded under (a built-in, a plugin agent) is not ours; a
        # near-miss the harness would still resolve onto a source or runtime agent is refused,
        # since it would run that agent without this proof (review finding L6).
        loaded = roster_names(governed[0])
        if name not in loaded:  # EXACT FIRST: the harness dispatches an exact name as itself
            key = harness_name_key(name)
            targets = sorted(target for n in loaded
                             for target in (n, PREFIX + n, *(old + n for old in RETIRED_PREFIXES))
                             if harness_name_key(target) == key)
            # ANY spelling that folds under a reserved Fleet prefix may reach a projection agent
            # the session has loaded -- a session runtime name `fp:<n>-<digest>`, one whose source
            # has since gone, one planted in the plugin -- and none of those is in the roster this
            # check reads (review F2). Only the exact prefix reaches the proof; the rest refuse.
            targets += sorted(f"{prefix}<agent>" for prefix in (PREFIX, *RETIRED_PREFIXES)
                              if key.startswith(harness_name_key(prefix)))
            if not targets:
                return None
            raise Unproven(f"{name!r} is not an agent name here, but Claude Code would dispatch "
                           f"it as one of {targets}; launch that agent by its exact name")
        if name not in source_definitions(governed[0]):
            raise Unproven(f"{name!r} is loaded from an agent file that does not declare it as "
                           "one safe name")
    if governed is not None:
        # BEFORE PROVING THE PROJECTION, and only for a launch this module owns (a source or
        # runtime name; a built-in or plugin agent returned None above): a governed checkout
        # whose own materialized write boundaries cannot confine a projected agent must refuse
        # every projected/rewritten named launch at the moment of use, not only when the
        # projection was issued -- a
        # `git checkout`/`reset` of the tracked `.claude/hooks` mid-session, or a manual
        # `claude --plugin-dir <projection>` that never called `generate`, would otherwise reach
        # a stale or unbound boundary this check alone catches.
        problems = boundary_problems(governed[0])
        if problems:
            raise Unproven(f"{governed[0]}: materialized write boundaries are stale, unbound or "
                           "disabled, so a projected agent could run unconfined: "
                           + "; ".join(problems))
    provenance = active_projection()
    if provenance.get("kind") == "session":
        return _session_launch(name, projected, governed, project_dir, provenance, prompt)
    runtime = name if projected else PREFIX + name
    identity = canonical_identity(runtime, project_dir, provenance)
    entry = provenance["sources"][identity.canonical]
    if governed is not None:
        project = governed[1]
        if provenance.get("project") != project:
            raise Unproven(f"projection {identity.projection_id[:12]} is for project "
                           f"{provenance.get('project')!r}, not {project!r}")
        revision = review_pin(source_definition(pathlib.Path(project_dir), identity.canonical),
                              prompt)
        current = resolve_policy(project, identity.canonical, revision)
        recorded = {"catalog_id": provenance.get("catalog_id"), "tier": entry["tier"],
                    "model": entry["model"], "effort": entry["effort"]}
        if recorded != current:
            raise Unproven(f"projection {identity.projection_id[:12]} is stale: it carries "
                           f"{recorded}, the catalog in force selects {current}")
    fields = {"agent": identity.canonical, "tier": entry["tier"], "model": entry["model"],
              "effort": entry["effort"], "source": SRC_PROJECTION, **identity.record()}
    return fields if projected else {**fields, "rewrite": runtime}


def _session_launch(name: str, projected: bool, governed: tuple[pathlib.Path, str] | None,
                    project_dir: pathlib.Path | str, session: dict, prompt: object = None) -> dict:
    """`_launch_policy` on a SESSION projection: resolve, derive, write, then dispatch exactly.

    Per agent, never per catalog: an agent whose projected bytes did not change keeps its name,
    which the harness has already loaded, whatever else in the catalog moved."""
    if governed is None:
        raise Unproven(f"{name!r} names a session projection agent outside a Fleet-governed "
                       "checkout, where no policy can be resolved for it")
    project = governed[1]
    if session["project"] != project:
        raise Unproven(f"this session's projection {session['plugin']} is for project "
                       f"{session['project']!r}, not {project!r}")
    agent = split_runtime_base(name[len(PREFIX):])[0] if projected else name
    source = source_definition(pathlib.Path(project_dir), agent)
    unsupported = sorted(declared_keys(source) & set(UNSUPPORTED_KEYS))
    if unsupported:
        raise Unproven(f"source agent {agent!r} declares {unsupported}, which a plugin agent "
                       "cannot carry")
    revision = review_pin(source, prompt)
    try:
        policy = resolve_policy(project, agent, revision)
    except BaseException as exc:  # noqa: BLE001 -- an unverifiable policy refuses, never guesses
        raise Unproven(f"the policy in force for {project}/{agent} "
                       f"({'pinned revision ' + revision if revision else 'current'}) cannot be "
                       f"resolved ({type(exc).__name__}: {exc})") from exc
    base, _digest, text = session_definition(
        projected_definition(source, policy["model"], policy["effort"]), agent)
    runtime = PREFIX + base
    if projected and name != runtime:
        raise Unproven(f"{name!r} is not what the policy in force projects for {agent!r} "
                       f"(tier {policy['tier']}, model {policy['model']}, effort "
                       f"{policy['effort']}: {runtime!r}); launch {agent!r} by its source name")
    materialize(session["plugin"], base, text)
    session = load_session(session["plugin"])  # the whole plugin, re-verified after the write
    identity = canonical_identity(runtime, project_dir, session)
    if base not in session["startup_agents"] and runtime not in harness_listing(
            session_transcript()):
        degraded = session["startup"].get("status") != "OK"
        raise Unproven(
            f"{runtime!r} (tier {policy['tier']}, model {policy['model']}, effort "
            f"{policy['effort']}: the policy in force for {agent!r}) is written to this session's "
            "projection but Claude Code has "
            f"not loaded it yet. Run {RELOAD_ACTION}, then launch {agent!r} again"
            + (f" (this session started with a degraded projection: "
               f"{'; '.join(session['startup'].get('reasons') or [])})" if degraded else ""))
    fields = {"agent": agent, "tier": policy["tier"], "model": policy["model"],
              "effort": policy["effort"], "source": SRC_PROJECTION,
              "policy_revision": policy["catalog_id"], **identity.record()}
    return fields if projected else {**fields, "rewrite": runtime}


#: THE USER-LEVEL BINDING (work item `claude-projection-hook-prerequisite`). Fleet binds
#: `agent_launch.py` in each managed account's own `~/.claude/settings.json` so every Claude session
#: on the account runs it, governed or not. It must enforce the projection where a checkout IS
#: governed and change nothing where none is: canon §Work's named-policy refusals (a per-call
#: `model` on a named agent, a contract without `model:`) stay with a project that binds the hook
#: itself. WHICH INVOCATION IS THE USER BINDING is decided by two facts together: the variable its
#: registered command sets, AND the script running from the Fleet-managed directory -- a variable
#: alone is inherited by every process below the session, so it would turn a project's own binding
#: into a user binding and silence it (review F1, second part).
SCOPE_ENV = "FLEET_AGENT_LAUNCH_SCOPE"
USER_SCOPE = "user"
USER_BINDING_DIR = pathlib.PurePosixPath(".local/fleet/claude-projection")
UNENFORCED = "user-scope launch, named policy not enforced outside a governed checkout"
#: THE FAIL-CLOSED LAUNCH BINDING (work item `policy-control-plane-cut-4-binding-fail-closed-and-
#: p1-residue`). Measured: Claude Code 2.1.288 runs a hook command through `/bin/sh -c`, and the
#: owned Codex 0.159.2 through the account's login shell `-c`; both block a launch ONLY on exit 2
#: (Codex: with a reason on stderr). Exit 1, 127, a signal death and a harness timeout are all
#: non-blocking, so a launch hook that cannot even start -- a syntax error, a truncated or missing
#: file, a missing interpreter -- would let the launch run with no Fleet enforcement, and no guard
#: inside the hook can help when the file holding it does not run. The binding itself is
#: therefore the last boundary: exit 0 passes through as the hook's allow, exit 2 passes through
#: unchanged as its own governed refusal, and every other outcome becomes exit 2 with
#: `HOOK_FAILED` on stderr. Strict POSIX, so `sh`, `dash`, `bash` and `zsh` read it alike. The
#: command never CONTAINS `HOOK_FAILED` as one string (the echo joins two words): Claude Code
#: quotes the whole bound command in every hook error it shows, so a literal there would put the
#: failure banner beside a legitimate governed refusal (measured live, work item above).
#: `console/fleetlib/claude_hooks.py` and `codex_hooks.py` (which cannot import this module)
#: render the same bytes for the user-level bindings; a test pins the two equal.
HOOK_FAILED = "FLEET AGENT HOOK FAILED"
#: The launcher's LAST line. A launcher truncated at a statement boundary is still valid Python:
#: it would run to its end without deciding and exit 0, which no exit status can tell from an
#: allow (review F1). Any truncation removes this line, so the binding refuses to run a file whose
#: last line is anything else -- the same class as a missing file. Old bindings ignore it, so the
#: launcher carrying it deploys before the binding that requires it.
LAUNCHER_END = "# fleet-agent-launch: end"


def fail_closed_command(script_word: str, invocation: str) -> str:
    """The bound command: run `invocation` (which names the launcher as `"$f"`) only when
    `script_word` names a readable regular file whose last line is `LAUNCHER_END`, and let only
    its exit 0 and exit 2 through."""
    return (f'f={script_word}; if [ -f "$f" ] && [ -r "$f" ] '
            f'&& [ "$(tail -n 1 "$f")" = "{LAUNCHER_END}" ]; then {invocation}; s=$?; '
            'else s=incomplete; fi; case $s in 0|2) exit $s;; esac; '
            'echo "FLEET AGENT HOOK" "FAILED: $f did not complete (status $s); launch refused" >&2; '
            'exit 2')


def project_launch_command(relative: str, event: str) -> str:
    """The exact command a project binds its own launch hook `relative` with for `event`: the
    fail-closed form for `PreToolUse`, the one event that can refuse a launch; the plain form for
    the reading events, where exit 2 would wedge or loop the session instead of refusing."""
    if event != "PreToolUse":
        return f'python3 -B "$CLAUDE_PROJECT_DIR/{relative}" hook {event}'
    return fail_closed_command(f'"$CLAUDE_PROJECT_DIR/{relative}"',
                               'python3 -B "$f" hook PreToolUse')


#: The one way a project binds its own launch hook: this repository's `tools/`. Only the exact
#: command counts -- a command that merely NAMES the script proves nothing about what runs (review
#: R1/F1). A Fleet-rendered project's `.claude/hooks/` copy no longer counts: that dispatch layer
#: is retired, so a leftover copy never stands the user binding down.
PROJECT_BINDINGS = ("tools/agent_launch.py",)


def _is_user_binding(script: pathlib.Path | str) -> bool:
    if os.environ.get(SCOPE_ENV) != USER_SCOPE:
        return False
    try:
        return pathlib.Path(script).resolve().parent == (pathlib.Path.home()
                                                         / USER_BINDING_DIR).resolve()
    except OSError:
        return False


def _covers_agent(matcher: object) -> bool:
    if matcher in (None, ""):
        return True  # no matcher: the entry fires for every tool
    try:
        return isinstance(matcher, str) and re.search(matcher, "Agent") is not None
    except (re.error, RecursionError, OverflowError):  # uncompilable: never a binding
        return False


#: What a bound launch hook EXECUTES: the launcher and every module it imports from its own
#: directory. Pinned equal to `agent_launch.py`'s local import closure by a test, so a governed
#: stand-down never vouches for a launcher whose helpers it did not compare.
LAUNCHER_MEMBERS = ("agent_launch.py", "claude_projection_identity.py", "claude_harness_evidence.py",
                    "codex_runtime_evidence.py", "codex_governed_policy.py", "codex_launch.py",
                    "launch_evidence.py")


def _project_launch_bindings(project_dir: pathlib.Path | str, event: str) -> tuple[str, ...]:
    """Every launcher path (`PROJECT_BINDINGS`) the project's tracked settings bind for `event` in
    the exact form, under a matcher that fires on `Agent`, and whose script exists; empty when
    the project does not bind its own launch hook for the event."""
    root = pathlib.Path(project_dir)
    try:
        settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return ()
    bound: list[str] = []
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    entries = hooks.get(event) if isinstance(hooks, dict) else None
    for entry in entries if isinstance(entries, list) else ():
        if not isinstance(entry, dict) or (event == "PreToolUse"
                                           and not _covers_agent(entry.get("matcher"))):
            continue
        inner = entry.get("hooks")
        for hook in inner if isinstance(inner, list) else ():
            # Only a synchronous command hook can refuse a launch: a backgrounded one (`async`, or
            # `asyncRewake`, which Claude Code 2.1.288 documents as implying async), or another type,
            # never owns the boundary however exact its command (review L4).
            synchronous = (isinstance(hook, dict) and hook.get("type") == "command"
                           and not hook.get("async") and not hook.get("asyncRewake"))
            command = hook.get("command") if synchronous else None
            bound += [rel for rel in PROJECT_BINDINGS if rel not in bound
                      and command == project_launch_command(rel, event)
                      and (root / rel).is_file()]
    return tuple(bound)


def _ungoverned(project_dir: pathlib.Path | str) -> bool:
    try:
        return governed_root(project_dir) is None
    except Unproven:  # an index that cannot be read is not "ungoverned"
        return False


def user_scope_stands_down(event: str | None, script: pathlib.Path | str) -> bool:
    """True when THIS invocation is the user binding and the project OWNS the launch boundary for
    the event, so this one does nothing and the two never run twice -- keeping both ran every
    launch, runtime and ledger effect twice (session 4c56884f, 2026-10-02).

    UNGOVERNED: the project's exact binding (`_project_launch_bindings`) is ownership enough; a
    decoy command or a matcher that never fires on `Agent` is not a binding.
    GOVERNED: ownership must be PROVEN, judged here from the Fleet-managed copy: the exact
    launcher every binding executes, and each module it imports beside it (`LAUNCHER_MEMBERS`),
    is byte-current against this tree (`_member_problem`), and the checkout's boundaries have no
    problem. Nothing is inferred from where the launcher sits: a project's own copy judges its
    members against itself, so only this copy can tell a current launcher from a stale, decoy or
    unreadable one. Anything unproven -- an unreadable index included -- keeps this binding
    enforcing the governed refusals (`_launch_policy`) at the moment of use."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or "."
    bound = _project_launch_bindings(project_dir, event or "PreToolUse")
    if not (_is_user_binding(script) and bound):
        return False
    try:
        governed = governed_root(project_dir)
    except Unproven:  # an index that cannot be read is not "ungoverned": keep enforcing
        return False
    if governed is None:
        return True
    root = pathlib.Path(project_dir)
    return not boundary_problems(governed[0]) and not any(
        _member_problem((root / rel).parent, name) for rel in bound for name in LAUNCHER_MEMBERS)


def user_scope_admits(project_dir: pathlib.Path | str, script: pathlib.Path | str) -> bool:
    """True when a named-policy refusal is announced instead of enforced: the user binding,
    outside any Fleet-governed checkout."""
    return _is_user_binding(script) and _ungoverned(project_dir)


def unenforced_launch(payload: dict, harness: str, unresolved: str) -> dict:
    """The announcement of a launch `user_scope_admits`: it proceeds exactly as without the hook."""
    tool_input = payload.get("tool_input")
    name = tool_input.get("subagent_type") if isinstance(tool_input, dict) else None
    return {"harness": harness, "agent": name if isinstance(name, str) and name else "generic",
            "model": unresolved, "effort": unresolved, "source": UNENFORCED}
