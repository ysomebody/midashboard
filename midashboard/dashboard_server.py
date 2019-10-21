# -*- coding: utf-8 -*-
from datetime import datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots

from .dashboard import Dashboard
from .review import Review


class Build(object):
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


class DashboardServer:
    def __init__(self, refresh_interval_min):
        self.refresh_interval_min = refresh_interval_min
        dashboard_data = Dashboard().read_data()
        dashboard_title = dashboard_data['title']
        self.build = Build(dashboard_data['build'])
        self.review = Review(dashboard_data['review'])

        style = {
            'backgroundColor': 'white',
            'color': 'black',
            'fontWeight': 'bold',
            'text-align': 'center',
            'font-size': '25px'
        }
        external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']
        self.dash = dash.Dash(dashboard_title, external_stylesheets=external_stylesheets)
        self.dash.layout = html.Div([
            html.H1(children=dashboard_title, style={'textAlign': 'center'}),
            dcc.Dropdown(
                id='dropdown',
                options=[
                    {'label': 'Build/Installer', 'value': '0'},
                    {'label': 'Open Reviews', 'value': '1'}
                ],
                value='0',
                optionHeight=40,
                clearable=False,
                style=style
            ),
            html.Div(id='dropdown-content'),
            dcc.Interval(
                id='interval-component',
                interval=self.refresh_interval_min * 60 * 1000,  # in milliseconds
                n_intervals=0
            )
        ], className='p-3 mb-2 bg-dark text-white')

        @self.dash.callback(Output('dropdown-content', 'children'),
                            [Input('dropdown', 'value'), Input('interval-component', 'n_intervals')])
        def update_dashboard(dropdown_value, n_intervals):
            dashboard_data = Dashboard().read_data()
            if dropdown_value == '0':
                self.build.refresh(dashboard_data['build'])
                return self.build.get_html()
            elif dropdown_value == '1':
                self.review.refresh(dashboard_data['review'])
                return self.review.get_html()

    def run(self):
        self.dash.run_server(debug=False, host='0.0.0.0')


if __name__ == '__main__':
    DashboardServer().run()


