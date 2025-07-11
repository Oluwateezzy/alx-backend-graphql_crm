#!/bin/bash

# Get the Django project directory (assuming script is in crm/cron_jobs)
DJANGO_DIR=$(dirname $(dirname $(realpath "$0")))

# Execute Python command to delete inactive customers and log results
LOG_FILE="/tmp/customer_cleanup_log.txt"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$TIMESTAMP] Starting customer cleanup..." >> $LOG_FILE

# Run the Django shell command to delete inactive customers
$DJANGO_DIR/manage.py shell << EOF >> $LOG_FILE 2>&1
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Order

cutoff_date = timezone.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(
    last_order_date__lt=cutoff_date,
    orders__isnull=False
).distinct()

count = inactive_customers.count()
inactive_customers.delete()

print(f"Deleted {count} inactive customers")
EOF

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Cleanup completed" >> $LOG_FILE