"""Installer agent guide (discoverability).

An autonomous agent that just generated a Migratis app shouldn't need to be told
out-of-band how to install it. This module is the single source of truth for the
install procedure, surfaced two ways so the prose and the machine form never
drift:

  - the base OpenAPI ``info.description`` (any client reading the schema gets it
    for free) — ``render_installer_guide_markdown()``;
  - machine-actionable JSON at ``GET /installer/agent-guide`` (and linked from
    ``GET /installer/status``) — ``build_installer_guide()``.

This is the base-side companion to the Migratis generator's ``/agent-guide``: the
generator tells the agent how to design+generate; this tells it how to land the
resulting package into the running app.
"""

BASE_PATH = "/backend/api/installer"

OVERVIEW = (
    "Install a Migratis-generated app package into THIS running base checkout. "
    "You already hold the generated ZIP, so no round-trip to a Migratis instance "
    "is needed: POST the ZIP here and it is applied through the same code path a "
    "human install uses — pre-flight Python compile validation, then a deferred "
    "database migrate + i18n seed. Treat the install as asynchronous."
)

# Default gate is loopback; an explicit token flips it to header auth.
AUTH = (
    "Loopback-only by default: only callers on the same host (127.0.0.1/::1) are "
    "accepted, so the endpoint is never reachable across the network without "
    "configuration. If INSTALLER_AGENT_TOKEN is set on the server, send a "
    "matching 'X-Installer-Token' header instead. No Migratis bearer token is "
    "involved here — that authenticates the generator, not the installer."
)

PROCEDURE = [
    {
        "step": 1, "name": "install", "method": "POST",
        "path": "/installer/install-package",
        "body": "Send the generated ZIP in any one of: multipart/form-data with "
                "a file field named 'package' (plus an optional 'config' field, a "
                "JSON string); application/json {\"package_b64\": \"<base64>\", "
                "\"config\": {...}}; or the raw ZIP bytes as the request body "
                "(with ?config=<json> on the query string).",
        "config": "Optional install-time config: {\"admin\": {\"email\": ..., "
                  "\"password\": ...}, \"email\": {...}, \"stripe\": {...}}. Admin "
                  "creation is deferred until the user tables exist. Omit it "
                  "entirely for a bare install.",
        "purpose": "Apply the package: writes app source + settings patch + "
                   "frontend module, then defers migrate+seed.",
    },
    {
        "step": 2, "name": "await", "method": None, "path": None,
        "purpose": "The 200 is asynchronous. If the response has "
                   "\"migrate_deferred\": true / \"restart_required\": true, the "
                   "migrate + seed run on the next backend reload (dev "
                   "autoreloader does this automatically) or restart (prod) — NOT "
                   "on the 200. The app is not live yet at that point.",
    },
    {
        "step": 3, "name": "verify", "method": "GET",
        "path": "/installer/installed",
        "purpose": "Poll until the newly installed module appears, rather than "
                   "assuming success from the 200.",
    },
]

UPGRADES = {
    "method": "POST", "path": "/installer/upgrade-package",
    "purpose": "In-place upgrade from a newer package. Destructive changes need "
               "explicit consent: without confirm the response is 409 with "
               "'needs_confirmation' + a row-count 'preview'. Set confirm in the "
               "config (or ?confirm=1 for a raw body) to apply data-loss changes. "
               "Surface the preview to your principal; do not auto-confirm.",
}

RESPONSES = {
    "200": "Applied. Read migrate_deferred / restart_required and act per step 2.",
    "422": "The package failed pre-flight Python compile validation. Fix the "
           "generation; do not retry the same bytes.",
    "409": "(upgrade-package) destructive changes pending — resend with confirm.",
    "403": "Endpoint gate failed: not a loopback caller and no/bad "
           "X-Installer-Token (the body's `reason` spells out the fix). This is "
           "NOT a missing-credential error you can solve with a token you "
           "already have — your Migratis bearer/PAT is never accepted here. "
           "Call from the base host (127.0.0.1) or configure "
           "INSTALLER_AGENT_TOKEN. See auth.",
    "400": "Malformed body — missing/!undecodable package or invalid config JSON.",
}

RULES = [
    "You already hold the ZIP; do not re-fetch it from Migratis — POST it here.",
    "A 403 from these endpoints means the loopback/token gate refused the "
    "CALLER, not that credentials are missing: never present your Migratis "
    "bearer/PAT to the installer. Retry from the base host (127.0.0.1) or have "
    "the operator set INSTALLER_AGENT_TOKEN.",
    "Treat install as asynchronous: re-check /installer/installed after the "
    "reload/restart instead of trusting the 200.",
    "On 422, the generated package does not compile — report it and regenerate; "
    "do not work around the validator.",
    "For upgrades, never auto-confirm a destructive change — surface the preview.",
    "The installer must be enabled (GET /installer/status -> {enabled:true}); if "
    "disabled, the install endpoints are unmounted.",
]


def build_installer_guide():
    """The install procedure + rules as a structured, machine-actionable dict."""
    return {
        "overview": OVERVIEW,
        "base_path": BASE_PATH,
        "auth": AUTH,
        "procedure": PROCEDURE,
        "upgrades": UPGRADES,
        "responses": RESPONSES,
        "rules": RULES,
    }


def render_installer_guide_markdown():
    """The same guide as Markdown, for the base OpenAPI ``info.description``."""
    lines = ["# Migratis base — installer agent lane", "", OVERVIEW, "",
             "## Authentication", AUTH, "", "## Procedure"]
    for s in PROCEDURE:
        if s["method"]:
            head = f"{s['step']}. **{s['name']}** — `{s['method']} {s['path']}`: {s['purpose']}"
        else:
            head = f"{s['step']}. **{s['name']}** — {s['purpose']}"
        lines.append(head)
        if s.get("body"):
            lines.append(f"   - body: {s['body']}")
        if s.get("config"):
            lines.append(f"   - config: {s['config']}")
    lines += ["", "## Upgrades",
              f"- `{UPGRADES['method']} {UPGRADES['path']}` — {UPGRADES['purpose']}",
              "", "## Response codes"]
    for code, meaning in RESPONSES.items():
        lines.append(f"- **{code}** — {meaning}")
    lines += ["", "## Rules"]
    for r in RULES:
        lines.append(f"- {r}")
    lines.append("")
    return "\n".join(lines)
