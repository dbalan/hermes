import requests

HERMES_API_URL = "https://api.my-deliveries.de/tnt/parcelservice/parceldetails/{}"
HERMES_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Referer": "https://www.myhermes.de/",
}

class HermesPackage:
    def __init__(self, id, status, attributes=None) -> None:
        self.id = id
        self.status = status
        self.attributes = attributes

    def __str__(self) -> str:
        return f"HermesPackage(id={self.id}, status={self.status}, attributes={self.attributes})"
    @staticmethod
    def from_response(id, resp):
        status = resp.get("status", {})
        if not status:
            raise ValueError("Invalid response")

        package_status = status.get("parcelStatus", None)

        # get attributes
        attributes = {"longText": status.get("text", {}).get("longText", "UNKNOWN")}

        forecast = resp.get("forecast", {})
        if forecast:
            attributes["deliveryDate"] = forecast.get("deliveryDate", "UNKNOWN")

        return HermesPackage(
            id=id,
            status = package_status,
            attributes = attributes
        )

def track_package(package_id: str) -> HermesPackage:
    response = requests.get(
        HERMES_API_URL.format(package_id),
        headers=HERMES_API_HEADERS,
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"API returned {response.status_code}")
    response = response.json()
    return HermesPackage.from_response(package_id, response)

