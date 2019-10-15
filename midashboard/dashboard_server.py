# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
from datetime import datetime
from review import Review
from dashboard import Dashboard
import deepdiff


class Build(object):
    def __init__(self, data):
        self.children = None
        self.data = {}
        self.product_per_row = 3
        self.refresh(data)

    def refresh(self, new_data):
        print("Refreshing build")
        data_updated = self._update_data_if_changed(new_data)
        if not data_updated:
            return
        self.children = [
            html.Div([self._generate_pie_charts()]),
            html.Div([self._generate_installer_table()])
        ]

    def _update_data_if_changed(self, new_data):
        diff = deepdiff.DeepDiff(self.data, new_data)
        if len(diff) == 0:
            return False
        self.data = new_data
        return True

    def _generate_pie_charts(self):
        self.product_per_row = 3
        rows = (len(self.data) - 1) // self.product_per_row + 1

        fig = make_subplots(
            rows=rows,
            cols=self.product_per_row,
            subplot_titles=[d['product'] for d in self.data],
            print_grid=True,
            specs=[[{'type': 'domain'}] * self.product_per_row for i in range(rows)])

        row_index = 1
        col_index = 1
        for d in self.data:
            last_installer_timestamp = datetime.strptime(d['installer_timestamp'], "%Y-%m-%d %H:%M:%S")
            days = (datetime.now() - last_installer_timestamp).days

            fig.add_trace(
                go.Pie(
                    values=[1],
                    marker={'colors': ['#a3de83' if d['build_pass'] else '#FF4500']},
                    text=[str(days) + ' days'],
                    textinfo='text',
                    hoverinfo='text',
                    hovertext=['Latest Installer: ' + d['installer_details']['version']],
                    showlegend=False,
                    textfont_size=25),
                row_index,
                col_index)
            col_index += 1
            if col_index > self.product_per_row:
                col_index = 1
                row_index += 1
        return dcc.Graph(figure=fig, style={'height': str(rows * 300) + 'px'})

    def _generate_installer_table(self):
        tab = html.Table(
            # Header
            [html.Tr([html.Th('Product'), html.Th('Last Build Time'), html.Th('State'), html.Th('Export')])] +

            # Body
            [html.Tr([
                html.Td(d['product']),
                html.Td(d['installer_timestamp']),
                html.Td('Good' if d['build_pass'] else 'Bad'),
                html.Td(d['installer_details']['export'])
            ]) for d in self.data]
        )
        tab.className = 'table table-dark'
        return tab


class DashboardServer:
    def __init__(self):
        self.refresh_interval_s = 120
        dashboard_data = Dashboard().read_data()
        dashboard_title = dashboard_data['title']
        self.build = Build(dashboard_data['build'])
        self.review = Review(dashboard_data['review'])
        tab_style = {
            'borderBottom': '1px solid #d6d6d6',
            'fontWeight': 'bold',
            'color': 'black'
        }
        tab_selected_style = {
            'borderTop': '1px solid #d6d6d6',
            'borderBottom': '1px solid #d6d6d6',
            'backgroundColor': '#119DFF',
            'color': 'black',
            'fontWeight': 'bold'
        }
        external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']
        self.dash = dash.Dash(dashboard_title, external_stylesheets=external_stylesheets)
        self.dash.layout = html.Div([
            html.H1(children=dashboard_title, style={'textAlign': 'center'}),
            dcc.Tabs(id="tabs", value='tab-1', children=[
                dcc.Tab(label='Build/Installer', value='tab-1', style=tab_style, selected_style=tab_selected_style),
                dcc.Tab(label='Review', value='tab-2', style=tab_style, selected_style=tab_selected_style),
            ]),
            html.Div(id='tabs-content'),
            dcc.Interval(
                id='interval-component',
                interval=self.refresh_interval_s * 1000,  # in milliseconds
                n_intervals=0
            )
        ], className='p-3 mb-2 bg-dark text-white')

        @self.dash.callback(Output('tabs-content', 'children'), [Input('tabs', 'value'), Input('interval-component', 'n_intervals')])
        def update_dashboard(tab, n):
            self._refresh_layout()
            if tab == 'tab-1':
                return self.build.children
            elif tab == 'tab-2':
                return self.review.children

    def _refresh_layout(self):
        print("refresh layout")
        dashboard_data = Dashboard().read_data()
        self.build.refresh(dashboard_data['build'])
        self.review.refresh(dashboard_data['review'])

    def run(self):
        self.dash.run_server(debug=False, host='0.0.0.0')


if __name__ == '__main__':
    DashboardServer().run()


