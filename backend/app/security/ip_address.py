import ipaddress

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extract and validate the direct client IP address.

    Forwarded headers are intentionally not trusted here.
    They require a configured trusted-proxy deployment.
    """

    client = request.client

    if client is None:
        raise ValueError("Client IP address is unavailable.")

    try:
        address = ipaddress.ip_address(client.host)
    except ValueError:
        raise ValueError("Invalid client IP address.")

    return str(address)