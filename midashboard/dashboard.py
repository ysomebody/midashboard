# -*- coding: utf-8 -*-
import datetime
import json
from pathlib import Path

from .argo import get_installer_info
from .nijenkins import get_build_result
from .reviewboard import analyze_open_reviews


class Dashboard:
    def __init__(self):
        config_filename = Path.home().joinpath('dashboard_config.json')
        with open(config_filename) as f:
            self.config = json.load(f)
        self.data_filename = Path.home().joinpath('dashboard_data.json')

    def read_data(self):
        with open(self.data_filename) as f:
            return json.load(f)

    def update(self):
        dashboard_data = self._pull_data_from_servers()
        with open(self.data_filename, 'w') as f:
            f.write(json.dumps(dashboard_data, indent=4))

    def _pull_data_from_servers(self):
        build_data = [
            {
                'product': build_config['product'],
                **get_installer_info(build_config['installer']),
                **get_build_result(build_config['build'])
            }
            for build_config in self.config['build']
            ]
        review_config = self.config['review']
        review_data = analyze_open_reviews(code_owners=review_config['code_owners'],
                                           dev_group=review_config['devgroup'],
                                           ignore_tags=review_config['ignore_tags'])
        return {
            'title'      : self.config['title'],
            'update_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'build'      : build_data,
            'review'     : review_data
        }


if __name__ == '__main__':
    dashboard = Dashboard()
    dashboard.update()
    print(dashboard.read_data())