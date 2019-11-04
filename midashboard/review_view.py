# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import json
from enum import Enum
import textwrap
from collections import defaultdict


class ReviewView(object):
    ColorPalette = Enum('ColorPalette', 'category people')

    def __init__(self, data):
        self.data = data
        self.default_layout = dict(height=250, margin=dict(l=10, t=30, b=10, r=10))
        # colors matching: unresolved, internal, owner, submitted
        self.category_colors = {
            'Unresolved': 'OrangeRed',
            'Internal': 'DarkOrange',
            'Code Owner': 'SkyBlue',
            'Submitted': 'Gray'
        }
        self.people_colors = ['#FFCD24', '#2AABE4', '#9DC8E4', '#666B6E', '#FFC2BB', '#FF8883', '#BC4123', '#0B172A', '#463940', '#03393D']

    @staticmethod
    def _get_title(title_text):
        return dict(text=title_text, position='top center', font=dict(size=20))

    def _map_colors(self, labels):
        return [self.category_colors[l] for l in labels]

    @staticmethod
    def _brief_detail_string(detail):
        url = detail['url'].rsplit('/', 2)[1]
        summary = detail['summary']
        brief = f'[{url}] {summary}'
        return textwrap.shorten(brief, width=100)

    def _get_hover_text(self, details):
        hover_text = []
        for details_of_the_label in details:
            text_of_the_label = '<br>'.join([self._brief_detail_string(d) for d in details_of_the_label])
            hover_text.append(text_of_the_label)
        return hover_text

    def get_pie(self, key, color=ColorPalette.people):
        data = self.data[key]
        total_count = sum([v['count'] for v in data.values()])
        title = f'{key} ({total_count})'
        labels = list(data.keys())
        if color == self.ColorPalette.people:
            colors = self.people_colors
        elif color == self.ColorPalette.category:
            colors = self._map_colors(labels)
        hover_text = self._get_hover_text([v['details'] for v in data.values()])
        return go.Figure(
            data=go.Pie(
                title=self._get_title(title),
                labels=labels,
                values=[v['count'] for v in data.values()],
                marker_colors=colors,
                textinfo='value',
                hoverinfo='text',
                hovertext=hover_text,
                showlegend=True,
                textfont_size=15,
                pull=0.02,
                sort=False
            ),
            # pull the legend back by 85% to make the figure compact
            layout={**self.default_layout, **dict(legend=dict(x=0.85))}
        )

    def get_stacked_bar(self, key):
        data = self.data[key]
        num_bars = max(list(map(int, data.keys()))) + 1
        x_names = list(range(0, num_bars))
        bars = defaultdict(lambda: [0] * num_bars)
        hover_text = defaultdict(lambda: [''] * num_bars)
        for day, categories in data.items():
            for category, v in categories.items():
                bars[category][int(day)] = int(v['count'])
                hover_text[category][int(day)] = '<br>'.join([self._brief_detail_string(d) for d in v['details']])
        duration_fig = go.Figure(
            data=[
                go.Bar(
                    name=k,
                    x=x_names,
                    y=v,
                    hoverinfo='text',
                    hovertext=hover_text[k],
                    marker_color=self.category_colors[k]
                )
                for k, v in bars.items()
            ],
            layout=self.default_layout
        )

        # Change the bar mode
        duration_fig.update_layout(
            title= key,
            xaxis_title='days',
            barmode='stack'
        )
        return duration_fig

    def refresh(self, new_data):
        self.data = new_data

    def get_html(self):
        return [html.Div(
            children=[
                html.Div(
                    children=[
                        dcc.Graph(figure=self.get_pie('Overall', ReviewView.ColorPalette.category))
                    ]
                ),
                html.Div(
                    children=[
                        dcc.Graph(figure=self.get_pie('Unresolved Reviews')),
                        dcc.Graph(figure=self.get_pie('Inactive Reviews')),
                    ],
                    style={'columnCount': 2, 'rowCount': 1}
                ),
                html.Div(
                    children=[
                        dcc.Graph(figure=self.get_stacked_bar('Days Since Posted'))
                    ]
                )
            ],
            className='p-3 mb-2 bg-white text-dark'
        )]


if __name__ == '__main__':
    with open(r'..\data\dashboard_data.json') as f:
        data = json.load(f)
    r = ReviewView(data['review'])
    r.get_pie('Unresolved Reviews').write_html('test.html', auto_open=True)
    r.get_stacked_bar('Days Since Posted').write_html('test.html', auto_open=True)
