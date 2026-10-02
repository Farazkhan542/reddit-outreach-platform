"""Reddit API approval guide: readiness checks, step list, and a generated request draft.

Checks mirror what Reddit's App Review looks at under the Responsible Builder Policy:
a specific use case, narrow scope, minimal scopes, human oversight, consent for DMs,
a privacy policy, an established account, honest commercial classification.
"""

from typing import Literal

from pydantic import BaseModel

from app.models import ApiAccessApplication, PostingMode, SubredditRule, TenantConfig

LINKS = {
    "policy": "https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy",
    "wiki": "https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki",
    "data_api_terms": "https://redditinc.com/policies/data-api-terms",
    "developer_terms": "https://redditinc.com/policies/developer-terms",
    "apps": "https://www.reddit.com/prefs/apps",
}

FREE_TIER_QPM = 100
MAX_FOCUSED_SUBREDDITS = 15


class GuideStep(BaseModel):
    id: str
    title: str
    body: str
    link: str | None = None
    link_label: str | None = None


STEPS: list[GuideStep] = [
    GuideStep(
        id="read_policy",
        title="Read the Responsible Builder Policy and Data API Terms",
        body="Reviewers judge your request against these. Note the rules on spam, duplicate content, "
        "bot disclosure, consent before private messages, and no mixed-use accounts.",
        link=LINKS["policy"],
        link_label="Open the policy",
    ),
    GuideStep(
        id="prepare_account",
        title="Use a dedicated, established Reddit account",
        body="Apply from the account the app will run under, with a verified email and real history. "
        "Throwaway or brand-new accounts are a common rejection reason. Don't use it for personal browsing.",
    ),
    GuideStep(
        id="publish_pages",
        title="Publish a website and privacy policy",
        body="The privacy policy should say what Reddit data you store, why, for how long, and how users "
        "can ask for deletion. A public product page makes the request credible.",
    ),
    GuideStep(
        id="pass_check",
        title="Pass the readiness check",
        body="Click 'Check now' and fix every failing item. Warnings are allowed but weaken the request.",
    ),
    GuideStep(
        id="submit_request",
        title="Submit ONE access request",
        body="Open the Reddit Data API Wiki, follow its 'contact us' link to the request form, choose the "
        "Developer category, and paste the generated request below. For the free tier, describe it as "
        "non-commercial development/testing; if anyone will pay or use it, it must be a commercial request. "
        "Never file multiple requests or register extra accounts for the same use case; that is prohibited.",
        link=LINKS["wiki"],
        link_label="Open the Data API Wiki",
    ),
    GuideStep(
        id="wait_and_respond",
        title="Wait for review and answer follow-ups",
        body="Expect days to several weeks with no published timeline. Commercial requests are routed to "
        "Reddit's Data API team for a contract discussion. Keep building on mock data meanwhile.",
    ),
    GuideStep(
        id="after_approval",
        title="After approval: register the app and go live",
        body="Create a 'web app' at reddit.com/prefs/apps with redirect URI "
        "https://<your-domain>/api/v1/auth/reddit/callback, put the client ID/secret in .env, "
        "and set REDDIT_MODE=live.",
        link=LINKS["apps"],
        link_label="Reddit app preferences",
    ),
]

STEP_IDS = {s.id for s in STEPS}


class CheckItem(BaseModel):
    id: str
    title: str
    status: Literal["pass", "warn", "fail"]
    detail: str
    fix: str | None = None


class CheckResult(BaseModel):
    ready: bool
    score: int  # 0-100
    items: list[CheckItem]


def scopes_for(app: ApiAccessApplication) -> list[str]:
    if app.posting_mode == PostingMode.manual:
        return ["identity", "read"]
    return ["identity", "read", "submit", "privatemessages"]


def estimated_qpm(config: TenantConfig) -> float:
    # Roughly one listing + one search call per subreddit per poll.
    subs = max(len(config.subreddits or []), 1)
    return round(subs * 2 / max(config.poll_interval_minutes, 1), 2)


def run_checks(
    app: ApiAccessApplication, config: TenantConfig, rules: list[SubredditRule]
) -> CheckResult:
    items: list[CheckItem] = []

    def add(id_, title, ok, detail, fix=None, warn=False):
        status = "pass" if ok else ("warn" if warn else "fail")
        items.append(CheckItem(id=id_, title=title, status=status, detail=detail, fix=None if ok else fix))

    desc_len = len((config.product_description or "").strip())
    add(
        "use_case",
        "Specific use case",
        bool(config.niche) and desc_len >= 40,
        f"Niche: '{config.niche or '-'}', product description {desc_len} chars.",
        "Fill in Niche config with a niche and a product description of at least 40 characters.",
    )

    subs = config.subreddits or []
    add(
        "scope",
        "Narrow subreddit scope",
        0 < len(subs) <= MAX_FOCUSED_SUBREDDITS,
        f"{len(subs)} subreddits configured.",
        "Add a focused list of subreddits." if not subs
        else f"Trim to {MAX_FOCUSED_SUBREDDITS} or fewer; broad scope reads like mass scraping.",
        warn=len(subs) > MAX_FOCUSED_SUBREDDITS,
    )

    rule_names = {r.subreddit for r in rules}
    missing = [s for s in subs if s.lower().removeprefix("r/") not in rule_names]
    add(
        "subreddit_rules",
        "Subreddit self-promotion rules recorded",
        bool(subs) and not missing,
        "All subreddits have a rule on file." if subs and not missing
        else f"Missing rules for: {', '.join(missing) or 'no subreddits configured'}.",
        "Read each subreddit's rules and record them under Niche config -> subreddit rules.",
        warn=True,
    )

    scopes = scopes_for(app)
    add(
        "scopes",
        "Minimal OAuth scopes",
        app.posting_mode == PostingMode.manual,
        f"Requested scopes: {' '.join(scopes)}.",
        "Switch posting mode to 'manual' (members post approved replies themselves) to request "
        "read-only scopes; write access to submit/DM gets much more scrutiny.",
        warn=True,
    )

    add(
        "human_review",
        "Human approval before any action",
        True,
        "Enforced in code: every draft is pending_review until a person approves it.",
    )
    add(
        "dm_consent",
        "No unsolicited private messages",
        True,
        "Enforced in code: drafts are public comments; DMs are never the first touch.",
    )

    add(
        "privacy_policy",
        "Privacy policy published",
        app.privacy_policy_url.startswith("https://"),
        app.privacy_policy_url or "No privacy policy URL.",
        "Publish a privacy policy (https) covering Reddit data storage, retention and deletion."
        + ("" if app.is_commercial else " Optional for free-tier testing, but it strengthens the request."),
        warn=not app.is_commercial,
    )
    add(
        "website",
        "Public website",
        app.website_url.startswith("https://"),
        app.website_url or "No website URL.",
        "Add an https product page describing the tool.",
        warn=True,
    )
    add(
        "contact",
        "Company and contact details",
        bool(app.company_name and app.contact_email and app.app_name),
        f"{app.app_name or '-'} by {app.company_name or '-'} <{app.contact_email or '-'}>",
        "Fill in app name, company name and contact email.",
    )

    if not app.reddit_username:
        add("account", "Established Reddit account", False, "No Reddit username.",
            "Enter the dedicated account you will apply from.")
    else:
        add(
            "account",
            "Established Reddit account",
            app.reddit_account_age_days >= 30,
            f"u/{app.reddit_username}, {app.reddit_account_age_days} days old.",
            "Use an account older than 30 days with genuine activity; new accounts look like throwaways.",
            warn=True,
        )

    add(
        "tier",
        "Access tier declared honestly",
        True,
        "Commercial access: requires a contract with Reddit's Data API team."
        if app.is_commercial
        else "Free tier: internal development and testing only. No customers, no revenue, no customer "
        "data. Switch to commercial and file a new request before anyone pays or uses it.",
    )

    qpm = estimated_qpm(config)
    add(
        "volume",
        "Call volume within limits",
        qpm <= FREE_TIER_QPM,
        f"Estimated ~{qpm} requests/minute (free tier limit {FREE_TIER_QPM}).",
        "Increase the poll interval or reduce subreddits.",
    )

    add(
        "retention",
        "Data retention limit stated",
        0 < app.data_retention_days <= 365,
        f"Reddit data kept {app.data_retention_days} days.",
        "Set a retention period of 365 days or less and honor deletions.",
        warn=True,
    )

    weights = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    score = round(100 * sum(weights[i.status] for i in items) / len(items))
    return CheckResult(ready=all(i.status != "fail" for i in items), score=score, items=items)


def build_request_text(app: ApiAccessApplication, config: TenantConfig) -> str:
    subs = ", ".join(f"r/{s.removeprefix('r/')}" for s in (config.subreddits or [])) or "(none configured yet)"
    manual = app.posting_mode == PostingMode.manual
    posting = (
        "The app never posts on its own. Approved replies are copied by the team member and posted "
        "manually from their own account, so we only request read access."
        if manual
        else "Approved replies are posted via the API from the reviewing team member's own connected "
        "account, only after explicit human approval of that specific reply."
    )
    if not app.is_commercial:
        return _free_tier_request(app, config, subs)
    return f"""Category: Developer - commercial use

App name: {app.app_name or "<app name>"}
Company: {app.company_name or "<company>"}
Website: {app.website_url or "<website>"}
Privacy policy: {app.privacy_policy_url or "<privacy policy URL>"}
Contact: {app.contact_email or "<email>"}
Reddit account: u/{app.reddit_username or "<username>"}

What the app does:
{app.app_name or "Our app"} helps {config.niche or "<niche>"} businesses find Reddit posts where people are \
actively asking for product recommendations, and helps a human team member write a genuinely helpful, \
post-specific reply. Product context: {config.product_description or "<product description>"}

How it uses Reddit:
- Reads new public posts in a small, fixed set of subreddits: {subs}.
- An AI model scores each post for purchase intent and drafts a reply grounded in that post's content. \
Drafts are never templated or reused across threads.
- Every draft goes to a human review queue. Nothing is posted without explicit approval by a named person, \
and each approval is logged.
- {posting}
- We never send unsolicited private messages; contact starts as a public comment and moves to DMs only \
if the user asks.
- We check and record each subreddit's self-promotion rules and skip communities that disallow commercial replies.

Scopes requested: {" ".join(scopes_for(app))}
Expected volume: about {estimated_qpm(config)} requests/minute (polling every {config.poll_interval_minutes} minutes).
Data handling: we store only the post fields needed for review (title, body, author, permalink) for \
{app.data_retention_days} days, honor deletions, and do not use Reddit data to train AI models or resell it.
"""


def _free_tier_request(app: ApiAccessApplication, config: TenantConfig, subs: str) -> str:
    return f"""Category: Developer - non-commercial use (personal development and testing)

Name: {app.app_name or "<project name>"}
Contact: {app.contact_email or "<email>"}
Reddit account: u/{app.reddit_username or "<username>"}
Website / repo: {app.website_url or "<optional>"}

What I'm building:
A prototype tool that reads public posts in a few subreddits, uses an AI model to identify posts where \
someone is asking for {config.niche or "<niche>"} recommendations, and drafts a helpful reply for me to \
review. This request is for internal development and testing only: there are no users or customers, it is \
not monetized, and no data is shared with anyone.

How it uses Reddit:
- Reads new public posts in a small, fixed set of subreddits: {subs}.
- Runs under this single account. Scopes requested: {" ".join(scopes_for(app))} (read-only).
- It does not post, vote or send messages. Any reply I decide to write, I post manually myself.
- Expected volume: about {estimated_qpm(config)} requests/minute, well under the free-tier limit.

Data handling: post data is kept for at most {app.data_retention_days} days for testing, deleted content \
is removed, and Reddit data is not used to train AI models or resold.

If this becomes a commercial product, I will file a separate commercial access request before any \
commercial use.
"""
