# -*- coding: utf-8 -*-
import threading
import time
from datetime import datetime

from urllib3 import disable_warnings, exceptions

from .dashboard import Dashboard


def log_with_timestamp(msg):
    print(f'[{datetime.now()}] {msg}')


class DashboardUpdater(threading.Thread):
    def __init__(self, interval_min, max_updates=-1):
        threading.Thread.__init__(self)
        self.interval_min = interval_min
        self.max_updates = max_updates

    def run(self):
        count = 0
        while True:
            self._dashboard_update()
            if self.max_updates > 0:
                count += 1
                if count >= self.max_updates:
                    break
            time.sleep(self.interval_min * 60)

    @staticmethod
    def _dashboard_update():
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
    DashboardUpdater(interval_min=1, max_updates=2).start()

