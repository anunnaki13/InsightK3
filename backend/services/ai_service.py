"""Centralized AI service using OpenRouter's OpenAI-compatible API."""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx

DEFAULT_OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL_ANALYSIS = os.environ.get("OPENROUTER_MODEL_ANALYSIS", "google/gemini-2.0-flash-001")
DEFAULT_MODEL_RISK = os.environ.get("OPENROUTER_MODEL_RISK", "anthropic/claude-3.5-haiku")
DEFAULT_MODEL_REPORT = os.environ.get("OPENROUTER_MODEL_REPORT", "google/gemini-2.0-flash-001")


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "https://insight-k3.local"),
        "X-Title": os.environ.get("OPENROUTER_APP_NAME", "InsightK3"),
    }


def _ensure_api_key(api_key: str) -> None:
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")


def mask_api_key(api_key: str) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 10:
        return "*" * len(api_key)
    return f"{api_key[:6]}...{api_key[-4:]}"


async def get_openrouter_runtime_settings(db) -> dict[str, Any]:
    stored = await db.app_settings.find_one({"key": "openrouter"}, {"_id": 0})
    if stored:
        return {
            "api_key": stored.get("api_key", ""),
            "model": stored.get("model") or DEFAULT_MODEL_ANALYSIS,
            "base_url": DEFAULT_OPENROUTER_BASE_URL,
            "settings_source": "database",
            "verified_at": stored.get("verified_at"),
            "key_label": stored.get("key_label"),
            "key_limit_remaining": stored.get("key_limit_remaining"),
            "key_usage": stored.get("key_usage"),
        }

    env_api_key = os.environ.get("OPENROUTER_API_KEY", "")
    fallback_model = DEFAULT_MODEL_ANALYSIS or DEFAULT_MODEL_RISK or DEFAULT_MODEL_REPORT
    return {
        "api_key": env_api_key,
        "model": fallback_model,
        "base_url": DEFAULT_OPENROUTER_BASE_URL,
        "settings_source": "environment" if env_api_key else "unset",
        "verified_at": None,
        "key_label": None,
        "key_limit_remaining": None,
        "key_usage": None,
    }


async def verify_openrouter_credentials(api_key: str, model: str | None = None) -> dict[str, Any]:
    _ensure_api_key(api_key)

    async with httpx.AsyncClient(timeout=30.0) as client:
        key_response = await client.get(
            f"{DEFAULT_OPENROUTER_BASE_URL}/key",
            headers=_headers(api_key),
        )
        key_response.raise_for_status()
        key_data = (key_response.json() or {}).get("data", {})

        models_response = await client.get(
            f"{DEFAULT_OPENROUTER_BASE_URL}/models",
            headers=_headers(api_key),
        )
        models_response.raise_for_status()
        models = (models_response.json() or {}).get("data", [])

    available_model_ids = {item.get("id") for item in models if item.get("id")}
    return {
        "key_info": {
            "label": key_data.get("label") or key_data.get("name"),
            "limit_remaining": key_data.get("limit_remaining"),
            "usage": key_data.get("usage"),
            "is_free_tier": key_data.get("is_free_tier"),
        },
        "model_exists": model in available_model_ids if model else None,
        "available_models": [
            {
                "id": item.get("id"),
                "name": item.get("name") or item.get("id"),
                "context_length": item.get("context_length"),
                "pricing": item.get("pricing", {}),
            }
            for item in models
            if item.get("id")
        ],
    }


async def list_openrouter_models(api_key: str) -> list[dict[str, Any]]:
    verification = await verify_openrouter_credentials(api_key)
    return verification["available_models"]


def _encode_file_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")


def _build_analysis_content(
    clause_title: str,
    clause_description: str,
    knowledge_base: str,
    documents: list[dict[str, Any]],
    additional_context: str = "",
) -> list[dict[str, Any]]:
    context_block = f"KONTEKS TAMBAHAN: {additional_context}\n\n" if additional_context else ""

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Kamu adalah asisten AI untuk auditor SMK3. Analisis dokumen evidence berikut "
                "terhadap persyaratan klausul.\n\n"
                f"KLAUSUL: {clause_title}\n"
                f"DESKRIPSI: {clause_description}\n\n"
                "KNOWLEDGE BASE (dokumen/evidence yang seharusnya ada):\n"
                f"{knowledge_base}\n\n"
                f"{context_block}"
                "Nilai kesesuaian dokumen yang diupload dengan dokumen yang diminta.\n\n"
                "Berikan respons HANYA dalam format berikut (jangan tambahkan teks lain):\n"
                "STATUS: [Sesuai / Belum Sesuai]\n"
                "SKOR: [angka 0-100]\n"
                "ALASAN: [penjelasan dokumen mana yang sudah ada dan mana yang kurang]\n"
                "FEEDBACK_POSITIF: [dokumen yang sudah sesuai]\n"
                "SARAN_PERBAIKAN: [dokumen yang masih perlu dilengkapi]"
            ),
        }
    ]

    for doc in documents:
        filename = doc.get("filename", "unknown")
        mime_type = doc.get("mime_type", "application/octet-stream")
        binary = doc.get("content", b"")

        if mime_type.startswith("image/") and binary:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{_encode_file_to_base64(binary)}"},
                }
            )
            continue

        content.append(
            {
                "type": "text",
                "text": f"[Dokumen: {filename} | MIME: {mime_type} | ukuran: {len(binary)} bytes]",
            }
        )

    return content


def _extract_message_content(response_json: dict[str, Any]) -> str:
    message = response_json["choices"][0]["message"]["content"]
    if isinstance(message, str):
        return message

    if isinstance(message, list):
        parts: list[str] = []
        for item in message:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part)

    return str(message)


def _parse_analysis_response(raw: str) -> dict[str, Any]:
    result = {
        "score": 0.0,
        "status": "Belum Sesuai",
        "reasoning": "",
        "feedback": "",
        "improvement_suggestions": "",
    }

    for line in raw.strip().splitlines():
        line = line.strip()
        upper_line = line.upper()

        if upper_line.startswith("STATUS:"):
            value = line.split(":", 1)[1].strip().lower()
            result["status"] = "Sesuai" if "sesuai" in value and "belum" not in value else "Belum Sesuai"
        elif upper_line.startswith("SKOR:"):
            try:
                score_text = "".join(char for char in line.split(":", 1)[1] if char.isdigit() or char == ".")
                result["score"] = min(100.0, float(score_text))
            except ValueError:
                pass
        elif upper_line.startswith("ALASAN:"):
            result["reasoning"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("FEEDBACK_POSITIF:"):
            result["feedback"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("SARAN_PERBAIKAN:"):
            result["improvement_suggestions"] = line.split(":", 1)[1].strip()

    if not result["reasoning"]:
        result["reasoning"] = raw[:1000]

    if result["score"] >= 70:
        result["status"] = "Sesuai"

    return result


async def analyze_document_evidence(
    db,
    clause_title: str,
    clause_description: str,
    knowledge_base: str,
    documents: list[dict[str, Any]],
    additional_context: str = "",
) -> dict[str, Any]:
    runtime = await get_openrouter_runtime_settings(db)
    api_key = runtime["api_key"]
    _ensure_api_key(api_key)

    payload = {
        "model": runtime["model"] or DEFAULT_MODEL_ANALYSIS,
        "max_tokens": 1500,
        "messages": [
            {
                "role": "user",
                "content": _build_analysis_content(
                    clause_title=clause_title,
                    clause_description=clause_description,
                    knowledge_base=knowledge_base,
                    documents=documents,
                    additional_context=additional_context,
                ),
            }
        ],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f'{runtime["base_url"]}/chat/completions',
            headers=_headers(api_key),
            json=payload,
        )
        response.raise_for_status()

    return _parse_analysis_response(_extract_message_content(response.json()))


async def assess_risk_item(
    db,
    risk_title: str,
    risk_description: str,
    area: str,
    category: str,
    existing_controls: str = "",
) -> dict[str, Any]:
    runtime = await get_openrouter_runtime_settings(db)
    api_key = runtime["api_key"]
    _ensure_api_key(api_key)

    prompt = f"""Kamu adalah risk assessor K3 senior untuk unit pembangkit PLTU.
Berikan penilaian risiko untuk item berikut.

JUDUL RISIKO: {risk_title}
DESKRIPSI: {risk_description}
AREA: {area}
KATEGORI: {category}
PENGENDALIAN YANG SUDAH ADA: {existing_controls if existing_controls else "Belum ada"}

Berikan respons HANYA dalam format berikut:
LIKELIHOOD: [1-5]
IMPACT: [1-5]
PENGENDALIAN_ELIMINASI: [saran eliminasi]
PENGENDALIAN_SUBSTITUSI: [saran substitusi]
PENGENDALIAN_ENGINEERING: [saran engineering control]
PENGENDALIAN_ADMINISTRASI: [saran prosedur/pelatihan]
PENGENDALIAN_APD: [APD yang diperlukan]
ALASAN: [penjelasan singkat penilaian]"""

    payload = {
        "model": runtime["model"] or DEFAULT_MODEL_RISK,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f'{runtime["base_url"]}/chat/completions',
            headers=_headers(api_key),
            json=payload,
        )
        response.raise_for_status()

    raw = _extract_message_content(response.json())
    result = {
        "likelihood": 3,
        "impact": 3,
        "control_elimination": "",
        "control_substitution": "",
        "control_engineering": "",
        "control_administrative": "",
        "control_ppe": "",
        "reasoning": "",
    }

    for line in raw.strip().splitlines():
        line = line.strip()
        upper_line = line.upper()
        if upper_line.startswith("LIKELIHOOD:"):
            try:
                result["likelihood"] = int(line.split(":", 1)[1].strip()[0])
            except (ValueError, IndexError):
                pass
        elif upper_line.startswith("IMPACT:"):
            try:
                result["impact"] = int(line.split(":", 1)[1].strip()[0])
            except (ValueError, IndexError):
                pass
        elif upper_line.startswith("PENGENDALIAN_ELIMINASI:"):
            result["control_elimination"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("PENGENDALIAN_SUBSTITUSI:"):
            result["control_substitution"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("PENGENDALIAN_ENGINEERING:"):
            result["control_engineering"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("PENGENDALIAN_ADMINISTRASI:"):
            result["control_administrative"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("PENGENDALIAN_APD:"):
            result["control_ppe"] = line.split(":", 1)[1].strip()
        elif upper_line.startswith("ALASAN:"):
            result["reasoning"] = line.split(":", 1)[1].strip()

    return result


async def generate_risk_summary(area_data: list[dict[str, Any]], period: str) -> str:
    _ensure_api_key()

    payload = {
        "model": MODEL_REPORT,
        "max_tokens": 600,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Kamu adalah K3 manager di PLTU yang menulis laporan ringkasan risiko untuk manajemen.\n"
                    "Buat narasi ringkasan kondisi risiko K3 unit berdasarkan data berikut.\n"
                    "Gunakan bahasa formal tapi mudah dipahami. Maksimal 300 kata.\n\n"
                    f"PERIODE: {period}\n"
                    f"DATA RISIKO PER AREA:\n{area_data}\n\n"
                    "Fokuskan pada: area dengan risiko tertinggi, tren perubahan, dan rekomendasi prioritas aksi."
                ),
            }
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()

    return _extract_message_content(response.json())
