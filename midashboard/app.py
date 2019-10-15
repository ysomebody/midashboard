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


external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

tabs_styles = {
    'height': '30px'
}
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


def generate_table(data):
    tab = html.Table(
        # Header
        [html.Tr([html.Th('Product'), html.Th('Last Build Time'), html.Th('State'), html.Th('Export')])] +

        # Body
        [html.Tr([
            html.Td(d['product']),
            html.Td(d['installer_timestamp']),
            html.Td('Good' if d['build_pass'] else 'Bad'),
            html.Td(d['installer_details']['export'])
        ]) for d in data]
    )
    tab.className = 'table table-dark'
    return tab


class Build(object):
    def __init__(self):
        self.children = None
        self.data = {}

    def refresh(self, new_data):
        diff = deepdiff.DeepDiff(self.data, new_data)
        if len(diff) == 0:
            return
        self.data = new_data
        column_num = 3
        row_num = (len(self.data) - 1) // column_num + 1

        fig = make_subplots(
            rows=row_num,
            cols=column_num,
            subplot_titles=[d['product'] for d in self.data],
            row_heights=[400] * row_num,
            print_grid=True,
            specs=[[{'type': 'domain'}] * column_num for i in range(row_num)])

        row_index = 1
        col_index = 1
        for d in self.data:
            build_data = datetime.strptime(d['installer_timestamp'], "%Y-%m-%d %H:%M:%S")
            days = (datetime.now() - build_data).days

            fig.add_trace(
                go.Pie(
                    values=[1],
                    marker={'colors': ['#a3de83' if d['build_pass'] else '#FF4500']},
                    text=[str(days) + ' days'],
                    textinfo='text',
                    hoverinfo='text',
                    hovertext=['Last Build Time: ' + d['installer_timestamp']],
                    showlegend=False,
                    textfont_size=30),
                row_index,
                col_index)
            col_index += 1
            if col_index > column_num:
                col_index = 1
                row_index += 1

        self.children = []
        self.children.append(html.Div([dcc.Graph(figure=fig, style={'height': str(row_num * 400) + 'px'})]))
        self.children.append(html.Div([generate_table(self.data)]))


build = Build()
review = Review()


def serve_layout():
    dashboard_data = Dashboard().read_data()
    build.refresh(dashboard_data['build'])
    review.refresh(dashboard_data['review'])
    return html.Div([
        html.H1(children='Dashboard', style={'textAlign': 'center'}),
        dcc.Tabs(id="tabs", value='tab-1', children=[
            dcc.Tab(label='Build', value='tab-1', style=tab_style, selected_style=tab_selected_style),
            dcc.Tab(label='Review', value='tab-2', style=tab_style, selected_style=tab_selected_style)
        ]),
        html.Div(id='tabs-content')
    ], className='p-3 mb-2 bg-dark text-white')


app.layout = serve_layout


@app.callback(Output('tabs-content', 'children'), [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return build.children
    elif tab == 'tab-2':
        return review.children


if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')
