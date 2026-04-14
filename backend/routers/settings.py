from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException

from database import db
from models.audit_models import User, UserRole
from models.settings_models import (
    OpenRouterSettingsDocument,
    OpenRouterSettingsResponse,
    OpenRouterSettingsUpdate,
    OpenRouterVerifyRequest,
)
from routers.auth import get_current_user
from services.ai_service import (
    get_openrouter_runtime_settings,
    list_openrouter_models,
    mask_api_key,
    verify_openrouter_credentials,
)

router = APIRouter(prefix="/api")


def _ensure_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can manage AI settings")


def _build_settings_response(runtime: dict, available_models: list[dict] | None = None, model_exists: bool | None = None) -> OpenRouterSettingsResponse:
    return OpenRouterSettingsResponse(
        has_api_key=bool(runtime.get("api_key")),
        masked_api_key=mask_api_key(runtime.get("api_key", "")),
        model=runtime.get("model") or "",
        settings_source=runtime.get("settings_source", "unset"),
        verified_at=runtime.get("verified_at"),
        key_label=runtime.get("key_label"),
        key_limit_remaining=runtime.get("key_limit_remaining"),
        key_usage=runtime.get("key_usage"),
        last_verified_model_exists=model_exists,
        available_models=available_models or [],
    )


@router.get("/settings/ai/openrouter", response_model=OpenRouterSettingsResponse)
async def get_openrouter_settings(current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    runtime = await get_openrouter_runtime_settings(db)
    return _build_settings_response(runtime)


@router.put("/settings/ai/openrouter", response_model=OpenRouterSettingsResponse)
async def update_openrouter_settings(data: OpenRouterSettingsUpdate, current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    model = data.model.strip()
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")

    existing = await db.app_settings.find_one({"key": "openrouter"}, {"_id": 0})
    api_key = data.api_key.strip()
    if not api_key and existing and existing.get("api_key"):
        api_key = existing["api_key"]

    verification = None
    if api_key:
        try:
            verification = await verify_openrouter_credentials(api_key, model=model)
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            raise HTTPException(status_code=400, detail=f"OpenRouter verification failed: {detail}")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"OpenRouter verification failed: {exc}")

    document = OpenRouterSettingsDocument(
        api_key=api_key,
        model=model,
        key_label=verification["key_info"]["label"] if verification else None,
        key_limit_remaining=verification["key_info"]["limit_remaining"] if verification else None,
        key_usage=verification["key_info"]["usage"] if verification else None,
        verified_at=datetime.now(timezone.utc) if verification else None,
        updated_by=current_user.id,
    ).model_dump()

    await db.app_settings.update_one({"key": "openrouter"}, {"$set": document}, upsert=True)
    runtime = await get_openrouter_runtime_settings(db)
    return _build_settings_response(
        runtime,
        available_models=verification["available_models"] if verification else [],
        model_exists=verification["model_exists"] if verification else None,
    )


@router.post("/settings/ai/openrouter/verify")
async def verify_openrouter_settings(data: OpenRouterVerifyRequest, current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    runtime = await get_openrouter_runtime_settings(db)
    api_key = data.api_key.strip() or runtime.get("api_key", "")
    model = (data.model or runtime.get("model") or "").strip() or None
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required for verification")

    try:
        verification = await verify_openrouter_credentials(api_key, model=model)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"OpenRouter verification failed: {detail}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OpenRouter verification failed: {exc}")

    return {
        "verified": True,
        "masked_api_key": mask_api_key(api_key),
        "model": model,
        "model_exists": verification["model_exists"],
        "key_info": verification["key_info"],
        "available_models": verification["available_models"],
    }


@router.get("/settings/ai/openrouter/models")
async def get_openrouter_models(current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    runtime = await get_openrouter_runtime_settings(db)
    api_key = runtime.get("api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key is not configured")

    try:
        models = await list_openrouter_models(api_key)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Failed to load OpenRouter models: {detail}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to load OpenRouter models: {exc}")

    return {"items": models}
