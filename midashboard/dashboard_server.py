# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from .dashboard import Dashboard
from .review_view import ReviewView
from .build_view import BuildView


class DashboardServer:
    def __init__(self, refresh_interval_min):
        self.refresh_interval_min = refresh_interval_min
        dashboard_data = Dashboard().read_data()
        dashboard_title = dashboard_data['title']
        self.build = BuildView(dashboard_data['build'])
        self.review = ReviewView(dashboard_data['review'])

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


