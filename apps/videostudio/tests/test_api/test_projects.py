from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "checks" in data


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Sistema Video AI Automatico" in data["app"]


@pytest.mark.asyncio
async def test_create_project(client):
    resp = await client.post("/api/v1/projects/", json={
        "title": "Test Progetto",
        "description": "Una descrizione di test",
        "language": "it",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Progetto"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client):
    await client.post("/api/v1/projects/", json={"title": "Lista Test 1"})
    await client.post("/api/v1/projects/", json={"title": "Lista Test 2"})

    resp = await client.get("/api/v1/projects/")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 2
    assert "has_next" in data
    assert "has_prev" in data
    assert "total_pages" in data


@pytest.mark.asyncio
async def test_get_project(client):
    create = await client.post("/api/v1/projects/", json={"title": "Get Test"})
    pid = create.json()["id"]

    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Test"


@pytest.mark.asyncio
async def test_get_project_not_found(client):
    resp = await client.get("/api/v1/projects/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client):
    create = await client.post("/api/v1/projects/", json={"title": "Update Test"})
    pid = create.json()["id"]

    resp = await client.patch(f"/api/v1/projects/{pid}", json={"title": "Aggiornato"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Aggiornato"


@pytest.mark.asyncio
async def test_delete_project(client):
    create = await client.post("/api/v1/projects/", json={"title": "Delete Test"})
    pid = create.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{pid}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pagination_projects(client):
    for i in range(25):
        await client.post("/api/v1/projects/", json={"title": f"Page Test {i}"})

    resp = await client.get("/api/v1/projects/?page=1&page_size=10")
    data = resp.json()
    assert len(data["items"]) == 10
    assert data["total"] >= 25
    assert data["total_pages"] >= 3
    assert data["has_next"] is True
    assert data["has_prev"] is False

    resp2 = await client.get("/api/v1/projects/?page=3&page_size=10")
    data2 = resp2.json()
    assert data2["has_next"] is False
    assert data2["has_prev"] is True
