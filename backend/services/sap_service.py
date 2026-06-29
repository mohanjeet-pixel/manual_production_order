import requests
from requests.auth import HTTPBasicAuth

from backend.core.config import SAP_API_URL, SAP_USERNAME, SAP_PASSWORD
from backend.core.logger import get_logger

logger = get_logger("sap_service")


def call_sap_and_normalize(material: str, plant: str, quantity: float) -> dict:
    payload = {
        "MATERIAL": material,
        "PLANT": plant,
        "QUANTITY": str(int(quantity)),
        "UNIT": "nos",
    }
    logger.info(f"SAP API call | material={material} plant={plant} qty={quantity}")
    response = requests.post(
        SAP_API_URL,
        json=payload,
        auth=HTTPBasicAuth(SAP_USERNAME, SAP_PASSWORD),
        timeout=300,
    )
    response.raise_for_status()
    return _normalize(response.json())


def _normalize(api_response: dict) -> dict:
    messages = []
    order_saved = None

    for msg in api_response.get("MESSAGES", []):
        text = msg.get("MESSAGE_TEXT", "").strip()
        if "Order number" in text and "saved" in text:
            order_saved = text
        messages.append({
            "no":   msg.get("MESSAGE_NO"),
            "type": msg.get("MESSAGE_TYPE"),
            "text": text,
        })

    return {
        "material":    api_response.get("MATERIAL"),
        "plant":       api_response.get("PLANT"),
        "quantity":    int(api_response.get("QUANTITY", 0)),
        "unit":        "nos",
        "messages":    messages,
        "order_saved": order_saved,
    }
