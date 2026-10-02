from tests.conftest import login


async def test_fresh_org_is_not_ready(client):
    headers = await login(client, "owner@a.com", "Acme")
    guide = (await client.get("/api/v1/approval", headers=headers)).json()
    assert guide["application"]["is_commercial"] is False
    assert guide["check"]["ready"] is False
    assert len(guide["steps"]) == 7
    assert "non-commercial" in guide["request_text"]


async def test_free_tier_becomes_ready(client):
    headers = await login(client, "owner@a.com", "Acme")
    await client.put(
        "/api/v1/config",
        headers=headers,
        json={
            "niche": "furniture",
            "product_description": "Handmade solid-wood dining tables and chairs, shipped nationwide.",
            "subreddits": ["furniture", "HomeImprovement"],
        },
    )
    guide = (
        await client.put(
            "/api/v1/approval",
            headers=headers,
            json={
                "app_name": "LeadDesk",
                "company_name": "Acme",
                "contact_email": "owner@a.com",
                "reddit_username": "acme_dev",
                "reddit_account_age_days": 400,
                "steps_done": ["read_policy", "bogus"],
            },
        )
    ).json()
    assert guide["application"]["steps_done"] == ["read_policy"]

    check = (await client.post("/api/v1/approval/check", headers=headers)).json()
    failing = [i["id"] for i in check["items"] if i["status"] == "fail"]
    assert check["ready"], failing
    assert "identity read" in guide["request_text"]
    assert "r/furniture" in guide["request_text"]


async def test_commercial_requires_privacy_policy(client):
    headers = await login(client, "owner@a.com", "Acme")
    await client.put("/api/v1/approval", headers=headers, json={"is_commercial": True})
    check = (await client.post("/api/v1/approval/check", headers=headers)).json()
    privacy = next(i for i in check["items"] if i["id"] == "privacy_policy")
    assert privacy["status"] == "fail"


async def test_member_cannot_access(client):
    owner = await login(client, "owner@a.com", "Acme")
    await client.post("/api/v1/org/members", headers=owner, json={"email": "rep@a.com"})
    member = await login(client, "rep@a.com")
    assert (await client.get("/api/v1/approval", headers=member)).status_code == 403
