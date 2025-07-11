import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/crm_report_log.txt"


def log_report(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - Report: {message}\n")


@shared_task
def generate_crm_report():
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql", verify=True, retries=3
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql(
        """
        {
            totalCustomers
            totalOrders
            totalRevenue
        }
    """
    )

    try:
        result = client.execute(query)
        customers = result["totalCustomers"]
        orders = result["totalOrders"]
        revenue = result["totalRevenue"]
        log_report(f"{customers} customers, {orders} orders, {revenue} revenue")
        print("CRM weekly report logged.")
    except Exception as e:
        log_report(f"Error: {e}")
        print(f"Error: {e}")
