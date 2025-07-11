#!/bin/bash

# Get the directory where the script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DJANGO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Log file
LOG_FILE="/tmp/customer_cleanup_log.txt"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Starting customer cleanup..." >> "$LOG_FILE"

# Ensure manage.py exists
if [ ! -f "$DJANGO_DIR/manage.py" ]; then
  echo "[$TIMESTAMP] ERROR: manage.py not found in $DJANGO_DIR" >> "$LOG_FILE"
  exit 1
fi

# Run the Django shell to delete inactive customers
cd "$DJANGO_DIR" || {
  echo "[$TIMESTAMP] ERROR: Failed to change directory to $DJANGO_DIR" >> "$LOG_FILE"
  exit 1
}

./manage.py shell << EOF >> "$LOG_FILE" 2>&1
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer

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
echo "[$TIMESTAMP] Cleanup completed" >> "$LOG_FILE"
