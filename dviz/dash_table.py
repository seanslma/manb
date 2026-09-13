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
#     display_name: dev
#     language: python
#     name: python3
# ---

# + language="html"
# <style>
# .cell-output-ipywidget-background {
#     background-color: transparent !important;
# }
# :root {
#     --jp-widgets-color: var(--vscode-editor-foreground);
#     --jp-widgets-font-size: var(--vscode-editor-font-size);
# }
# </style>
#

# +
import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table

# Create a pandas DataFrame
df = pd.DataFrame(
    {
        "Name": ["Alice", "Brian", "Chris", "David", "Emily"],
        "Age": [25, 30, 36, 25, 36],
        "Gender": ["Female", "Male", "Male", "Male", "Female"],
        "Occupation": ["Engineer", "Doctor", "Lawyer", "Artist", "Artist"],
    }
)

# Custom styles
styles = {
    "table": {
        "width": "50%",
        "margin": "auto",
    }
}

# Define the Dash layout
app = dash.Dash(__name__)

# Define the callback function for the drop-down filter
@app.callback(
    Output("table-body", "children"),
    [
        Input(f"filter-dropdown-{index}", "value")
        for index in range(len(df.columns))
    ],
    [State("datatable", "children")],
)
def update_table_body(filter_values, table_body):
    # Check if the filter-dropdown-3 component exists
    if table_body is None:
        return None

    # Filter the data
    filtered_df = df.copy()
    for col_index, filter_value in enumerate(filter_values):
        if filter_value:
            filtered_df = filtered_df[
                filtered_df[df.columns[col_index]] == filter_value
            ]

    # Update the table body
    return dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df.columns],
        data=filtered_df.to_dict("records"),
        style_table=styles["table"],
        style_cell={"textAlign": "left", "minWidth": "100px", "width": "150px", "maxWidth": "200px"},
        style_cell_conditional=[
            {"if": {"column_id": "Name"}, "width": "20%"},
            {"if": {"column_id": "Age"}, "width": "10%"},
            {"if": {"column_id": "Gender"}, "width": "20%"},
            {"if": {"column_id": "Occupation"}, "width": "20%"},
        ],
        filter_action="native",
        sort_action="native",
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(248, 248, 248)",
            }
        ],
    )

# Define the layout
app.layout = html.Div(
    [
        html.H1("Table with Filtering and Sorting"),
        html.Table(
            id="datatable",
            children=[
                html.Thead(
                    html.Tr(
                        [
                            html.Th(
                                dcc.Dropdown(
                                    id={"type": "filter-dropdown", "index": col},
                                    options=[
                                        {"label": col, "value": col}
                                        for col in df[col].unique()
                                    ],
                                    value="",
                                    clearable=True,
                                )
                            )
                            for col in df.columns
                        ]
                    )
                ),
                html.Tbody(id="table-body"),
            ],
        ),
    ]
)

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)

# -

# # filter works but sort not

# +
import dash
from dash import html
from dash import dcc
import pandas as pd

# Sample data
data = {
    'Name': ['John', 'Smith', 'Jane', 'Doe'],
    'Age': [30, 25, 32, 28],
    'City': ['New York', 'Los Angeles', 'Chicago', 'Houston']
}
df = pd.DataFrame(data)

# Initialize the Dash app
app = dash.Dash(__name__)

# Create a Dash layout
app.layout = html.Div([
    html.H1("Table with Filtering and Sorting"),
    html.Table(
        id='datatable',
        children=[
            html.Thead(
                html.Tr([
                    html.Th(dcc.Dropdown(
                        id={'type': 'filter-dropdown', 'index': col},
                        options=[{'label': col, 'value': col} for col in df[col].unique()],
                        value='',
                        clearable=True
                    )) for col in df.columns
                ])
            ),
            html.Tbody(id='table-body')
        ]
    )
])


@app.callback(
    dash.dependencies.Output('table-body', 'children'),
    [dash.dependencies.Input({'type': 'filter-dropdown', 'index': dash.dependencies.ALL}, 'value')]
)
def update_table(filter_values):
    dff = df
    for col, value in zip(df.columns, filter_values):
        if value:
            dff = dff[dff[col] == value]

    return [
        html.Tr([
            html.Td(dff.iloc[i][col]) for col in dff.columns
        ]) for i in range(len(dff))
    ]


if __name__ == '__main__':
    app.run_server(debug=True)

# -

# # sort works but filter not

# +
import dash
from dash import html
from dash import dcc
from dash import dash_table
import pandas as pd

# Sample data
data = {
    'Name': ['John', 'Smith', 'Jane', 'Doe'],
    'Age': [30, 25, 32, 28],
    'City': ['New York', 'Los Angeles', 'Chicago', 'Houston']
}
df = pd.DataFrame(data)

# Initialize the Dash app
app = dash.Dash(__name__)

# Custom styles
styles = {
    'table': {
        'width': '50%',
        'margin': 'auto',
    },
    'dropdown': {
        'width': '100%',
    }
}

# Create a Dash layout
app.layout = html.Div([
    html.H1("Table with Filtering and Sorting"),
    dash_table.DataTable(
        id='datatable',
        columns=[{'name': col, 'id': col} for col in df.columns],
        data=df.to_dict('records'),
        style_table=styles['table'],
        style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '150px', 'maxWidth': '200px'},
        style_cell_conditional=[
            {'if': {'column_id': 'Name'}, 'width': '20%'},
            {'if': {'column_id': 'Age'}, 'width': '10%'},
            {'if': {'column_id': 'City'}, 'width': '20%'},
        ],
        filter_action='native',
        sort_action='native',
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
    )
])


if __name__ == '__main__':
    app.run_server(debug=True)

