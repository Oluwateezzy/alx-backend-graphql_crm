import os
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """Logs a heartbeat message and optionally checks GraphQL endpoint"""
    log_file = "/tmp/crm_heartbeat_log.txt"
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Basic heartbeat log
    message = f"{timestamp} CRM is alive\n"

    try:
        # Optional GraphQL health check
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=2,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql("""query { hello }""")
        result = client.execute(query)

        if result.get("hello"):
            message += f"{timestamp} GraphQL endpoint responsive: {result['hello']}\n"
        else:
            message += f"{timestamp} GraphQL endpoint check failed\n"

    except Exception as e:
        message += f"{timestamp} GraphQL check error: {str(e)}\n"

    # Write to log file
    with open(log_file, "a") as f:
        f.write(message)
