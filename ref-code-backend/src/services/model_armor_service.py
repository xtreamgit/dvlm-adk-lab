import os
from typing import Any, Dict, Optional

from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1
from google.protobuf.json_format import MessageToDict


class ModelArmorService:
    @staticmethod
    def is_enabled() -> bool:
        return os.getenv("MODEL_ARMOR_ENABLED", "false").lower() == "true"

    @staticmethod
    def _client(location: str) -> modelarmor_v1.ModelArmorClient:
        return modelarmor_v1.ModelArmorClient(
            transport="rest",
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{location}.rep.googleapis.com",
            ),
        )

    @staticmethod
    def _resolve_template_name(
        *, project_id: str, location: str, template_id: str
    ) -> str:
        return f"projects/{project_id}/locations/{location}/templates/{template_id}"

    @staticmethod
    def sanitize_user_prompt(
        *, text: str, project_id: str, location: str, template_id: str
    ) -> Dict[str, Any]:
        client = ModelArmorService._client(location)
        request = modelarmor_v1.SanitizeUserPromptRequest(
            name=ModelArmorService._resolve_template_name(
                project_id=project_id,
                location=location,
                template_id=template_id,
            ),
            user_prompt_data=modelarmor_v1.DataItem(text=text),
        )
        response = client.sanitize_user_prompt(request=request)
        return MessageToDict(response._pb, preserving_proto_field_name=True)

    @staticmethod
    def sanitize_model_response(
        *, text: str, project_id: str, location: str, template_id: str
    ) -> Dict[str, Any]:
        client = ModelArmorService._client(location)
        request = modelarmor_v1.SanitizeModelResponseRequest(
            name=ModelArmorService._resolve_template_name(
                project_id=project_id,
                location=location,
                template_id=template_id,
            ),
            model_response_data=modelarmor_v1.DataItem(text=text),
        )
        response = client.sanitize_model_response(request=request)
        return MessageToDict(response._pb, preserving_proto_field_name=True)

    @staticmethod
    def default_config() -> Dict[str, Optional[str]]:
        return {
            "project_id": os.getenv("MODEL_ARMOR_PROJECT_ID") or os.getenv("PROJECT_ID"),
            "location": os.getenv("MODEL_ARMOR_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEXAI_LOCATION"),
            "template_id": os.getenv("MODEL_ARMOR_TEMPLATE_ID"),
        }
