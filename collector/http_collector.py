"""
A simple HTTP collector for the HttpMonitor pack.
"""
import httpx
import time

from ssonez.daemons.collector_daemon import CollectorDaemon


class HttpCollector(CollectorDaemon):
    """
    A collector that performs a simple HTTP GET request to a target.
    """
    name = "HttpCollector"

    async def collect(self, device, context):
        """
        Collects data for a given device.
        """
        ip_address = context.get('ip_address')
        if not ip_address:
            return

        # Get zProperties for this device
        port = context.get('zHttpPort', 80)
        path = context.get('zHttpPath', '/')
        protocol = 'https' if port == 443 else 'http'
        url = f"{protocol}://{ip_address}:{port}{path}"

        start_time = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=10.0)

            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Create datapoints
            context.add_datapoint('http_status_code', response.status_code)
            context.add_datapoint('http_response_time', response_time_ms)

            if response.is_success:
                context.add_event(
                    summary=f"HTTP check successful for {url}",
                    severity='clear'
                )
            else:
                context.add_event(
                    summary=f"HTTP check failed for {url} with status {response.status_code}",
                    severity='warning'
                )

        except httpx.RequestError as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            context.add_datapoint('http_response_time', response_time_ms)
            context.add_event(
                summary=f"HTTP request failed for {url}: {str(e)}",
                severity='critical'
            )
