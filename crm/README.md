# CRM Weekly Report Setup

## Prerequisites
- Redis server installed and running
- Python dependencies installed

## Installation Steps

1. Install Redis:
```bash
sudo apt-get install redis-server  # For Ubuntu
brew install redis                # For macOS
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start Celery worker:
```bash
celery -A crm worker -l info
```

5. Start Celery Beat (in a separate terminal):
```bash
celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Verification

1. Check worker logs for task execution
2. Verify report generation in log file:
```bash
tail -f /tmp/crm_report_log.txt
```

Sample output:
```
2023-11-20 06:00:00 - Report: 142 customers, 97 orders, $12,847.50 revenue
```

## Troubleshooting
- Ensure Redis is running: `redis-cli ping` (should return "PONG")
- Check Celery worker connectivity to Redis
- Verify GraphQL endpoint is accessible