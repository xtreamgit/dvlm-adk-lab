"""Model Armor security routes.

Provides direct Model Armor sanitization endpoints for testing and learning.
"""

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from middleware.iap_auth_middleware import get_current_user_iap
from models.user import User
from services.model_armor_service import ModelArmorService


router = APIRouter(prefix="/api/security/model-armor", tags=["Model Armor"])


class _ModelArmorConfig(BaseModel):
    project_id: Optional[str] = None
    location: Optional[str] = None
    template_id: Optional[str] = None


class SanitizePromptRequest(BaseModel):
    text: str = Field(..., min_length=1)
    config: Optional[_ModelArmorConfig] = None


class SanitizeResponseRequest(BaseModel):
    text: str = Field(..., min_length=1)
    config: Optional[_ModelArmorConfig] = None


def _resolve_config(override: Optional[_ModelArmorConfig]) -> Dict[str, Optional[str]]:
    base = ModelArmorService.default_config()
    if not override:
        return base
    if override.project_id:
        base["project_id"] = override.project_id
    if override.location:
        base["location"] = override.location
    if override.template_id:
        base["template_id"] = override.template_id
    return base


@router.get("/status")
async def model_armor_status(current_user: User = Depends(get_current_user_iap)):
    cfg = ModelArmorService.default_config()
    return {
        "enabled": ModelArmorService.is_enabled(),
        "project_id": cfg.get("project_id"),
        "location": cfg.get("location"),
        "template_id_configured": bool(cfg.get("template_id")),
    }


@router.post("/sanitize-prompt")
async def sanitize_prompt(
    payload: SanitizePromptRequest,
    current_user: User = Depends(get_current_user_iap),
) -> Dict[str, Any]:
    if not ModelArmorService.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model Armor is disabled. Set MODEL_ARMOR_ENABLED=true.",
        )

    cfg = _resolve_config(payload.config)
    if not cfg.get("project_id") or not cfg.get("location") or not cfg.get("template_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Model Armor config missing. Set MODEL_ARMOR_PROJECT_ID (or PROJECT_ID), "
                "MODEL_ARMOR_LOCATION (or GOOGLE_CLOUD_LOCATION/VERTEXAI_LOCATION), and MODEL_ARMOR_TEMPLATE_ID."
            ),
        )

    try:
        return {
            "request": {"text": payload.text},
            "sanitization": ModelArmorService.sanitize_user_prompt(
                text=payload.text,
                project_id=cfg["project_id"],
                location=cfg["location"],
                template_id=cfg["template_id"],
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sanitize-response")
async def sanitize_response(
    payload: SanitizeResponseRequest,
    current_user: User = Depends(get_current_user_iap),
) -> Dict[str, Any]:
    if not ModelArmorService.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model Armor is disabled. Set MODEL_ARMOR_ENABLED=true.",
        )

    cfg = _resolve_config(payload.config)
    if not cfg.get("project_id") or not cfg.get("location") or not cfg.get("template_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Model Armor config missing. Set MODEL_ARMOR_PROJECT_ID (or PROJECT_ID), "
                "MODEL_ARMOR_LOCATION (or GOOGLE_CLOUD_LOCATION/VERTEXAI_LOCATION), and MODEL_ARMOR_TEMPLATE_ID."
            ),
        )

    try:
        return {
            "request": {"text": payload.text},
            "sanitization": ModelArmorService.sanitize_model_response(
                text=payload.text,
                project_id=cfg["project_id"],
                location=cfg["location"],
                template_id=cfg["template_id"],
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
