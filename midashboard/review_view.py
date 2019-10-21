# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import json


class ReviewView(object):
    def __init__(self, data):
        self.data = data
        self.default_layout = dict(height=350, margin=dict(l=0, t=0, b=0, r=0))

    @staticmethod
    def _get_title(title_text):
        return dict(text=title_text, position='top center', font=dict(size=20))

    def get_overall_figure(self):
        return go.Figure(
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
            # pull the legend back by 85% to make the figure compact
            layout={**self.default_layout, **dict(legend=dict(x=0.85))}
        )

    def get_developers_figure(self):
        return go.Figure(
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
            layout=self.default_layout
        )

    def get_duration_figure(self):
        duration = self.data['duration']
        days = duration['names']
        data = duration['data']
        colors = ['red', 'Orange', 'Grey']
        duration_fig = go.Figure(
            data=[
                go.Bar(
                    name=d['status'],
                    x=days,
                    y=d['values'],
                    marker_color=c
                )
                for c, d in zip(colors, data)
            ],
            layout=self.default_layout
        )

        # Change the bar mode
        duration_fig.update_layout(barmode='stack')
        return duration_fig

    def refresh(self, new_data):
        self.data = new_data

    def get_html(self):
        return html.Div(
            children=[
                html.Div(
                    children=[
                        dcc.Graph(figure=self.get_overall_figure()),
                        dcc.Graph(figure=self.get_developers_figure())
                    ],
                    style={'columnCount': 2, 'rowCount': 1}
                ),
                html.Div(
                    children=[
                        dcc.Graph(figure=self.get_duration_figure())
                    ]
                )
            ],
            className='p-3 mb-2 bg-white text-dark'
        )


if __name__ == '__main__':
    with open(r'..\data\dashboard_data.json') as f:
        data = json.load(f)
    r = ReviewView(data['review'])
    r.get_overall_figure().write_html('test.html', auto_open=True)
