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


def update_low_stock():
    """
    Updates low stock products via GraphQL mutation and logs results.
    Runs every 12 hours via django-crontab.
    Logs to /tmp/low_stock_updates_log.txt with timestamped entries.
    """
    LOG_FILE = "/tmp/low_stock_updates_log.txt"
    GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Configure GraphQL client with timeout
        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            verify=True,
            retries=3,
            timeout=10,
        )
        client = Client(
            transport=transport, fetch_schema_from_transport=True, execute_timeout=20
        )

        # Define the mutation with proper formatting
        mutation = gql(
            """
            mutation UpdateLowStock {
                updateLowStockProducts {
                    updatedProducts {
                        id
                        name
                        stock
                    }
                    message
                }
            }
        """
        )

        # Execute mutation
        result = client.execute(mutation)
        data = result.get("updateLowStockProducts", {})

        # Prepare log message
        log_lines = [
            f"\n[{timestamp}] Stock Update Report",
            f"Status: {data.get('message', 'No message returned')}",
            "Updated Products:",
        ]

        # Add product details
        for product in data.get("updatedProducts", []):
            log_lines.append(
                f"- {product['name']}: Stock updated to {product['stock']} (ID: {product['id']})"
            )

        # Count of updated products
        log_lines.append(
            f"Total products updated: {len(data.get('updatedProducts', []))}"
        )

        # Write to log file
        with open(LOG_FILE, "a") as f:
            f.write("\n".join(log_lines) + "\n")

        return True

    except Exception as e:
        error_msg = (
            f"[{timestamp}] CRITICAL: Failed to update low stock products\n"
            f"Error: {str(e)}\n"
            f"GraphQL Endpoint: {GRAPHQL_ENDPOINT}\n"
        )
        with open(LOG_FILE, "a") as f:
            f.write(error_msg)
        return False
