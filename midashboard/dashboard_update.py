from datetime import datetime
from dashboard import Dashboard
from urllib3 import disable_warnings, exceptions


def log_with_timestamp(msg):
    print(f'[{datetime.now()}] {msg}')


def dashboard_update():
    log_with_timestamp("Start to update dashboard.")
    dashboard = Dashboard()
    succeeded = False
    max_retry = 5
    for i in range(0, max_retry):
        try:
            dashboard.update()
        except Exception as e:
            log_with_timestamp(f'Failed to update dashboard. [{e}]')
            continue
        succeeded = True
        break
    if succeeded:
        log_with_timestamp('Dashboard data updated.')
    else:
        log_with_timestamp(f'Dashboard data failed to update after {max_retry} retries.')


if __name__ == '__main__':
    disable_warnings(exceptions.InsecureRequestWarning)
    dashboard_update()

