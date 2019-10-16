from .dashboard_server import DashboardServer
from .dashboard_update import DashboardUpdater


if __name__ == "__main__":
    updater = DashboardUpdater(interval_min=9)
    updater.start()
    DashboardServer(refresh_interval_min=5).run()
    print('Dashboard server stopped. Waiting for update thread to stop...')
    updater.cancel()
    print('done')



