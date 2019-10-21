# -*- coding: utf-8 -*-

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_core_components as dcc
import dash_html_components as html
import json
from datetime import datetime


class BuildView(object):
    def __init__(self, data):
        self.data = data

    def refresh(self, new_data):
        self.data = new_data

    def get_html(self):
        return [
            html.Div([dcc.Graph(figure=self.get_build_figure())]),
            html.Div([self.get_installer_table()])
        ]

    @staticmethod
    def _get_title(title_text):
        return dict(text=title_text, position='top center', font=dict(size=25))

    def get_build_figure(self):
        product_per_row = 3
        rows = (len(self.data) - 1) // product_per_row + 1
        fig = make_subplots(
            rows=rows,
            cols=product_per_row,
            subplot_titles=[d['product'] for d in self.data],
            vertical_spacing=0.1,
            horizontal_spacing=0.1,
            print_grid=True,
            specs=[[{'type': 'domain'}] * product_per_row for i in range(rows)])
        fig.update_layout(margin=dict(t=30, l=10, b=10, r=10))

        row_index = 1
        col_index = 1
        for d in self.data:
            last_installer_timestamp = datetime.strptime(d['installer_timestamp'], "%Y-%m-%d %H:%M:%S")
            days = (datetime.now() - last_installer_timestamp).days

            fig.add_trace(
                go.Pie(
                    values=[1],
                    marker={'colors': ['#a3de83' if d['build_pass'] else '#FF4500']},
                    text=[f'{days} day' + ('s' if days != 1 else '')],
                    textinfo='text',
                    hoverinfo='text',
                    hovertext=['Latest Installer: ' + d['installer_details']['version']],
                    showlegend=False,
                    textfont_size=25),
                row_index,
                col_index)
            col_index += 1
            if col_index > product_per_row:
                col_index = 1
                row_index += 1
        return fig

    def get_installer_table(self):
        tab = html.Table(
            # Header
            [html.Tr([
                html.Th('Product'),
                html.Th('Last Installer Time'),
                html.Th('Export')]
            )]
            +
            # Body
            [html.Tr([
                html.Td(d['product']),
                html.Td(d['installer_timestamp']),
                html.Td(d['installer_details']['export'])
            ]) for d in self.data]
        )
        tab.className = 'table table-dark'
        return tab


if __name__ == '__main__':
    with open(r'..\data\dashboard_data.json') as f:
        data = json.load(f)
    r = BuildView(data['build'])
    r.get_build_figure().write_html('test.html', auto_open=True)
