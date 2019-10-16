# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html
import deepdiff
import plotly.graph_objects as go

colors = ['red', 'Orange', 'Grey']


class Review(object):
    def __init__(self, data):
        self.children = None
        self.data = {}
        self.refresh(data)

    @staticmethod
    def _get_title(title_text):
        return dict(text=title_text, position='top center', font=dict(size=20))

    def refresh(self, new_data):
        diff = deepdiff.DeepDiff(self.data, new_data)
        if len(diff) == 0:
            return
        self.data = new_data

        default_layout = dict(height=350, margin=dict(l=0, t=0, b=0))

        overall_figure = go.Figure(
            data=go.Pie(
                title=self._get_title('Overall'),
                labels=[s['description'] for s in self.data["status"]],
                values=[s['count'] for s in self.data["status"]],
                hoverinfo='label',
                textinfo='value',
                showlegend=True,
                textfont_size=15,
                pull=0.02
            ),
            layout={**default_layout, **dict(legend=dict(x=0.85))}
        )

        developers_figure = go.Figure(
            data=go.Pie(
                title=self._get_title('By developers'),
                labels=list(self.data["owners"].keys()),
                values=list(self.data["owners"].values()),
                hoverinfo='label+value',
                textinfo='value',
                showlegend=True,
                textfont_size=15,
                pull=0.03
            ),
            layout=default_layout
        )

        xnames = self.data["duration"]['names']
        duration_fig = go.Figure(
            data=[
                go.Bar(name=d['status'], x=xnames, y=d['values'], marker_color=c)
                for c, d in zip(colors, self.data["duration"]['data'])
            ],
            layout=default_layout
        )

        # Change the bar mode
        duration_fig.update_layout(barmode='stack')

        self.children = html.Div(children=[
            html.Div(children=[
                dcc.Graph(figure=overall_figure),
                dcc.Graph(figure=developers_figure)
            ], style={'columnCount': 2, 'rowCount': 1}),
            html.Div(children=[
                dcc.Graph(figure=duration_fig)])
        ], style={'columnCount': 1, 'rowCount': 1}, className='p-3 mb-2 bg-white text-dark')

