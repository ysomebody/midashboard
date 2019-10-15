# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import deepdiff

colors = ['red', 'Orange', 'Grey']


class Review(object):
    def __init__(self, data):
        self.children = None
        self.data = {}
        self.refresh(data)

    def refresh(self, new_data):
        diff = deepdiff.DeepDiff(self.data, new_data)
        if len(diff) > 0:
            self.data = new_data
            fig1 = go.Figure(
                data=[go.Pie(
                    labels=[s['description'] for s in self.data["status"]],
                    values=[s['count'] for s in self.data["status"]]
                )])

            fig2 = go.Figure(
                data=[go.Pie(
                    labels=list(self.data["owners"].keys()),
                    values=list(self.data["owners"].values())
                )])

            fig1.update_traces(
                hoverinfo='label+value', textinfo='value', textfont_size=20,
                hole=0.5,
                marker=dict(line=dict(color='#FFFFFF', width=2)))

            fig2.update_traces(
                hoverinfo='label+value', textinfo='value', textfont_size=20,
                hole=0.5,
                marker=dict(line=dict(color='#FFFFFF', width=2)))

            xnames = self.data["duration"]['names']

            duration_fig = go.Figure(data=[
                go.Bar(name=d['status'], x=xnames, y=d['values'], marker_color=c)
                for c, d in zip(colors, self.data["duration"]['data'])
            ])

            # Change the bar mode
            duration_fig.update_layout(barmode='stack')

            self.children = html.Div(children=[
                html.Div(children=[
                    dcc.Graph(figure=fig1), dcc.Graph(figure=fig2)
                ], style={'columnCount': 2, 'rowCount': 1}),
                html.Div(children=[
                    dcc.Graph(figure=duration_fig)])
            ], style={'columnCount': 1, 'rowCount': 1}, className='p-3 mb-2 bg-white text-dark')
