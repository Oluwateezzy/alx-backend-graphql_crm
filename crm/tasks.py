import logging
from datetime import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_crm_report(self):
    """Generates weekly CRM report via GraphQL query"""
    log_file = "/tmp/crm_report_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Configure GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)

        # Define the report query
        query = gql(
            """
            query GenerateCRMReport {
                customerCount
                orderCount
                totalRevenue
            }
        """
        )

        # Execute query
        result = client.execute(query)

        # Prepare report
        report_data = {
            "customers": result.get("customerCount", 0),
            "orders": result.get("orderCount", 0),
            "revenue": result.get("totalRevenue", 0),
        }

        log_message = (
            f"{timestamp} - Report: "
            f"{report_data['customers']} customers, "
            f"{report_data['orders']} orders, "
            f"${report_data['revenue']:,.2f} revenue\n"
        )

        # Write to log file
        with open(log_file, "a") as f:
            f.write(log_message)

        return log_message.strip()

    except Exception as e:
        error_msg = f"{timestamp} - Report generation failed: {str(e)}\n"
        with open(log_file, "a") as f:
            f.write(error_msg)
        raise self.retry(exc=e, countdown=60)
