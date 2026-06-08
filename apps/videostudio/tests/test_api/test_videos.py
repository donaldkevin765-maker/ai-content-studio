from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_video(client):
    proj = await client.post("/api/v1/projects/", json={"title": "Video Test"})
    pid = proj.json()["id"]

    resp = await client.post("/api/v1/videos/", json={
        "project_id": pid,
        "title": "Test Video",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Video"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_video_invalid_project(client):
    resp = await client.post("/api/v1/videos/", json={
        "project_id": 99999,
        "title": "Orphan Video",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_videos(client):
    proj = await client.post("/api/v1/projects/", json={"title": "List Vid"})
    pid = proj.json()["id"]
    await client.post("/api/v1/videos/", json={"project_id": pid, "title": "V1"})
    await client.post("/api/v1/videos/", json={"project_id": pid, "title": "V2"})

    resp = await client.get("/api/v1/videos/")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_list_videos_by_project(client):
    proj1 = await client.post("/api/v1/projects/", json={"title": "P1"})
    proj2 = await client.post("/api/v1/projects/", json={"title": "P2"})
    await client.post("/api/v1/videos/", json={"project_id": proj1.json()["id"], "title": "V1"})
    await client.post("/api/v1/videos/", json={"project_id": proj2.json()["id"], "title": "V2"})

    resp = await client.get(f"/api/v1/videos/?project_id={proj1.json()['id']}")
    data = resp.json()
    assert all(v["project_id"] == proj1.json()["id"] for v in data["items"])


@pytest.mark.asyncio
async def test_get_video_with_scenes(client):
    proj = await client.post("/api/v1/projects/", json={"title": "Detail"})
    vid = await client.post("/api/v1/videos/", json={
        "project_id": proj.json()["id"], "title": "Detail V"
    })
    vid_id = vid.json()["id"]

    resp = await client.get(f"/api/v1/videos/{vid_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "scenes" in data
    assert isinstance(data["scenes"], list)


@pytest.mark.asyncio
async def test_list_scenes(client):
    proj = await client.post("/api/v1/projects/", json={"title": "Scenes"})
    vid = await client.post("/api/v1/videos/", json={
        "project_id": proj.json()["id"], "title": "Scenes V"
    })

    resp = await client.get(f"/api/v1/videos/{vid.json()['id']}/scenes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_progress(client):
    proj = await client.post("/api/v1/projects/", json={"title": "Prog"})
    vid = await client.post("/api/v1/videos/", json={
        "project_id": proj.json()["id"], "title": "Prog V"
    })

    resp = await client.get(f"/api/v1/videos/{vid.json()['id']}/progress")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_render_invalid_state(client):
    proj = await client.post("/api/v1/projects/", json={"title": "NoRender"})
    vid = await client.post("/api/v1/videos/", json={
        "project_id": proj.json()["id"], "title": "NoRender V"
    })

    resp = await client.post(f"/api/v1/videos/{vid.json()['id']}/render")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_video(client):
    proj = await client.post("/api/v1/projects/", json={"title": "Del Vid"})
    vid = await client.post("/api/v1/videos/", json={
        "project_id": proj.json()["id"], "title": "Del V"
    })

    resp = await client.delete(f"/api/v1/videos/{vid.json()['id']}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_pagination_videos(client):
    proj = await client.post("/api/v1/projects/", json={"title": "Pag Vid"})
    for i in range(15):
        await client.post("/api/v1/videos/", json={
            "project_id": proj.json()["id"], "title": f"PV {i}"
        })

    resp = await client.get("/api/v1/videos/?page=1&page_size=5")
    data = resp.json()
    assert len(data["items"]) == 5
    assert data["has_next"] is True
    assert data["total"] >= 15
