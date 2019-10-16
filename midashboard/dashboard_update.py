# -*- coding: utf-8 -*-
from threading import Timer
from threading import Thread
from datetime import datetime

from urllib3 import disable_warnings, exceptions

from .dashboard import Dashboard


def log_with_timestamp(msg):
    print(f'[{datetime.now()}] {msg}')


class DashboardTimer():
    def __init__(self, interval_min):
        self.timer = Timer(interval_min * 60, self._dashboard_update)

    def run(self):
        self.timer.run()

    def cancel(self):
        self.timer.cancel()

    @staticmethod
    def _dashboard_update():
        disable_warnings(exceptions.InsecureRequestWarning)
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


class DashboardUpdater(Thread):
    def __init__(self, interval_min):
        Thread.__init__(self)
        self.canceled = False
        self.timer = DashboardTimer(interval_min)

    def run(self):
        while not self.canceled:
            self.timer.run()

    def cancel(self):
        self.canceled = True
        self.timer.cancel()
        self.join()


if __name__ == '__main__':
    DashboardUpdater(interval_min=1).start()


