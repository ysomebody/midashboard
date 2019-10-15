from dashboard_server import DashboardServer
from dashboard_update import DashboardUpdater


if __name__ == "__main__":
    DashboardUpdater(interval_min=3).start()
    DashboardServer(refresh_interval_min=5).run()



