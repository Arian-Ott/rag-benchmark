import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from passwords.pw import influx_token, influx_url, org


class LoggingTimeSeries:
    def __init__(self):
        self.write_client = InfluxDBClient(url=influx_url, token=influx_token, org=org)
        self.write_api = self.write_client.write_api(write_options=SYNCHRONOUS)
        self.bucket = "rag-performance-monitor"

    def add_request(self, title: str, request_type: str, body: str):
        point = (
            Point("_measurement").tag("title", title).tag("type", request_type).field("body", body))
        self.write_api.write(bucket=self.bucket, org=org, record=point)

    def add_response(self, title: str, response_type: str, status_code: int, body: str):
        point = (Point("_measurement").tag("title", title).tag("type", response_type).field(
            "status_code", status_code).field("body", body))
        self.write_api.write(bucket=self.bucket, org=org, record=point)


class LoggingMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app
        self.logger = LoggingTimeSeries()

    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        # Process the request
        request_body = await request.body()
        self.logger.add_request("API Call", "request", request_body.decode("utf-8"))

        # Process the response
        response = await call_next(request)

        # Skip logging for HTML responses (like /docs and /redoc)
        if isinstance(response, HTMLResponse):
            return response

        # Log other response types
        response_body = (response.body.decode("utf-8") if isinstance(response,
                                                                     JSONResponse) else "Non-JSON response")
        self.logger.add_response("API Call", "response", response.status_code, response_body)

        # Return the original response
        return response
