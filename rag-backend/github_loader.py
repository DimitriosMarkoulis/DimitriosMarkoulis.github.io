import base64
import json
import os
from pathlib import Path
from typing import Any

import httpx

PROJECT_SOURCES_PATH = Path(__file__).parent / "project_sources.json"


def load_project_sources() -> dict[str, Any]:
    with PROJECT_SOURCES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def fetch_repo_file(repo: str, path: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_headers())

    if response.status_code == 404:
        return None
    response.raise_for_status()

    payload = response.json()
    if payload.get("encoding") != "base64" or "content" not in payload:
        return None

    raw = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
    return raw


def build_metadata_text(project: dict[str, Any]) -> str:
    tags = ", ".join(project.get("tags", []))
    return "\n".join(
        [
            f"Project: {project['name']}",
            f"Category: {project.get('category', 'Unknown')}",
            f"Status: {project.get('status', 'Unknown')}",
            f"Repository: {project.get('url', '')}",
            f"Positioning: {project.get('positioning', '')}",
            f"Tags: {tags}",
        ]
    )


def chunk_text(text: str, max_chars: int = 1400, overlap: int = 180) -> list[str]:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        chunk = cleaned[start:end]
        chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


async def collect_project_documents() -> list[dict[str, Any]]:
    source_config = load_project_sources()
    documents: list[dict[str, Any]] = []

    for project in source_config["projects"]:
        metadata_text = build_metadata_text(project)
        documents.append(
            {
                "project": project["name"],
                "repo": project["repo"],
                "url": project.get("url", ""),
                "category": project.get("category", ""),
                "status": project.get("status", ""),
                "source_path": "project_metadata",
                "text": metadata_text,
            }
        )

        for file_path in project.get("files", []):
            raw_text = await fetch_repo_file(project["repo"], file_path)
            if not raw_text:
                continue

            for idx, chunk in enumerate(chunk_text(raw_text)):
                documents.append(
                    {
                        "project": project["name"],
                        "repo": project["repo"],
                        "url": project.get("url", ""),
                        "category": project.get("category", ""),
                        "status": project.get("status", ""),
                        "source_path": file_path,
                        "chunk_id": idx,
                        "text": f"{metadata_text}\n\nSource file: {file_path}\n\n{chunk}",
                    }
                )

    return documents
