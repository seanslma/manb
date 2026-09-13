# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import pandas as pd
import plotly.graph_objects as go

def generate_figure(df, model):
    fig = go.Figure()

    fig.add_scatter(
        x=df['ts'],
        y=df['sales'],
        name='Actual',
        #line_shape='hv',
        legendgroup='Y',
    )

    fig.add_scatter(
        x=df['ts'],
        y=df['forecast'],
        name='Forecast',
        #line_shape='hv',
        legendgroup='Z',
    )

    fig.update_layout(
        autosize=True,
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(title='Sales vs Forecast', gridcolor='rgba(0,0,0,0)'),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(
            t=20,
            b=20,
            r=50,
            l=100
        ),
        xaxis=dict(
            showline=True,
            linewidth=1,
            color='black',
            type='date',
            gridcolor='#a2a2a2'
        )
    )

    return fig

def update_fig(df, fig, model):
    fig = go.Figure(fig)
    forecast_trace_name = [trace['name'] for trace in fig.data if 'Forecast' in trace.name][0]
    fig.update_traces(
        overwrite=True,
        x=list(df['ts']),
        y=list(df['sales']),
        selector=dict(name='Actual')
    )
    fig.update_traces(
        overwrite=True,
        x=list(df['ts']),
        y=list(df['forecast']),
        name=f'{model} Forecast',
        selector=dict(name=forecast_trace_name)
    )
    return fig



# -

df = pd.DataFrame({'ts': [1,2,3], 'sales': [3,5,4], 'forecast': [2,4,6]})
fig = generate_figure(df, 'A')
fig.show()


fig = update_fig(df, fig, 'D')
fig.show()

