from tests.conftest import login


async def _setup_org(client, email="owner@a.com", org="Acme Furniture"):
    headers = await login(client, email, org)
    await client.put(
        "/api/v1/config",
        headers=headers,
        json={"niche": "furniture", "subreddits": ["furniture"], "keywords": ["table"], "intent_threshold": 0.3},
    )
    return headers


async def test_health(client):
    res = await client.get("/api/health")
    assert res.json()["reddit_mode"] == "mock"


async def test_interpret_niche(client):
    headers = await login(client, "owner@a.com", "Acme")
    res = await client.post("/api/v1/config/interpret", headers=headers, json={"description": "I sell refurbished phones"})
    assert res.status_code == 200
    assert res.json()["niche"] == "mobile phones"


async def test_pipeline_review_and_send(client):
    headers = await _setup_org(client)

    run = (await client.post("/api/v1/pipeline/run", headers=headers)).json()
    assert run["drafts"] > 0

    queue = (await client.get("/api/v1/replies", headers=headers)).json()
    assert len(queue) == run["drafts"]
    assert all(r["status"] == "pending_review" for r in queue)

    reply_id = queue[0]["id"]
    await client.patch(f"/api/v1/replies/{reply_id}", headers=headers, json={"final_body": "Edited reply"})
    sent = (await client.post(f"/api/v1/replies/{reply_id}/approve", headers=headers)).json()
    assert sent["status"] == "sent"
    assert sent["final_body"] == "Edited reply"

    stats = (await client.get("/api/v1/analytics", headers=headers)).json()
    assert stats["replies_sent"] == 1


async def test_subreddit_rule_blocks_drafts(client):
    headers = await _setup_org(client)
    await client.put(
        "/api/v1/config/subreddit-rules", headers=headers, json={"subreddit": "furniture", "allows_commercial_replies": False}
    )
    run = (await client.post("/api/v1/pipeline/run", headers=headers)).json()
    assert run["drafts"] == 0
    assert run["skipped_by_rules"] == run["qualified"]


async def test_tenant_isolation(client):
    a = await _setup_org(client, "owner@a.com", "Org A")
    await client.post("/api/v1/pipeline/run", headers=a)
    a_reply = (await client.get("/api/v1/replies", headers=a)).json()[0]

    b = await login(client, "owner@b.com", "Org B")
    assert (await client.get("/api/v1/leads", headers=b)).json() == []
    assert (await client.get("/api/v1/replies", headers=b)).json() == []
    res = await client.post(f"/api/v1/replies/{a_reply['id']}/approve", headers=b)
    assert res.status_code == 404


async def test_member_permissions(client):
    owner = await _setup_org(client)
    await client.post("/api/v1/org/members", headers=owner, json={"email": "rep@a.com"})
    member = await login(client, "rep@a.com")

    assert (await client.get("/api/v1/config", headers=member)).status_code == 403
    assert (await client.post("/api/v1/pipeline/run", headers=member)).status_code == 403

    await client.post("/api/v1/pipeline/run", headers=owner)
    # Round-robin splits drafts between owner and member; member sees only their own.
    all_replies = (await client.get("/api/v1/replies", headers=owner)).json()
    mine = (await client.get("/api/v1/replies", headers=member)).json()
    assert 0 < len(mine) < len(all_replies) or len(all_replies) == 1
