import requests

def http_get(url: str, params: dict = None):
    """
    Send an HTTP GET request.

    Returns:
        dict: A dictionary containing:
            - "status_code" (int): The HTTP response status code.
            - "result" (str): The raw response body as text or parsed JSON response if the response is JSON, else None.

    Raises:
        requests.RequestException: If the request fails (e.g., timeout, connection error).
    """
    try:
        response = requests.get(url, params=params, timeout=10)

        return {
            "status_code": response.status_code,
            "result": (response.json() if "application/json" in response.headers.get("Content-Type", "") else response.text)
        }

    except requests.RequestException as e:
        raise e
