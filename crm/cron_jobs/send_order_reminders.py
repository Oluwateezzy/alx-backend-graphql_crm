#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure GraphQL client
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=True,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# GraphQL query to find recent pending orders
query = gql(
    """
    query GetRecentOrders {
        orders(where: {
            order_date_gte: "${week_ago}",
            status: "pending"
        }) {
            id
            customer {
                email
            }
        }
    }
"""
)


def main():
    # Calculate date 7 days ago
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()

    try:
        # Execute query with parameter
        result = client.execute(query, variable_values={"week_ago": week_ago})

        # Prepare log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Processing order reminders\n"

        # Process orders and build log
        for order in result["orders"]:
            log_entry += f"Order ID: {order['id']}, Customer Email: {order['customer']['email']}\n"

        # Write to log file
        with open("/tmp/order_reminders_log.txt", "a") as log_file:
            log_file.write(log_entry)

        print("Order reminders processed!")

    except Exception as e:
        error_msg = f"[{timestamp}] Error: {str(e)}\n"
        with open("/tmp/order_reminders_log.txt", "a") as log_file:
            log_file.write(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
