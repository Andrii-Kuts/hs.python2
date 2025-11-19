from analytics import Analytics
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd

def current_length(analytics: Analytics):
    users = sorted([(user, analytics.get_user_length(user)) for user in analytics.get_users()], key = lambda entry : entry[1])
    x = list(map(lambda user : user[0], users))
    y = list(map(lambda user : user[1], users))
    df = pd.DataFrame({
        "User": x,
        "Length": y,
    })
    fig=px.bar(
            df,
            x="User",
            y="Length",
            color_discrete_sequence=["DeepSkyBlue"],
            title="Length by User",
        )
    return html.Div([
        html.H4("All Users"),
        dcc.Graph(figure=fig),
    ])

def user_dropdown(analytics: Analytics):
    users = sorted(list(analytics.get_users()))
    return html.Div([
        html.H4("Select User"),
        dcc.Dropdown(
            id="user_dropdown",
            options=users,
            value=users[0],
            clearable=False,
            style={
                "fontFamily": "Avenir Next",
                "fontSize": "1rem",
                "flex": "1" 
            },
        ),
    ], style={
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "center",
        "gap": "20px",
        "padding": "20px"
    })


def user_statstics(analytics: Analytics):
    def length_history():
        return dcc.Graph(id="user_length_history")
    
    def numeric_statistics():
        return html.Div([
            html.Div([
                    html.Div("Best Rank", className="numeric-statistic-title"),
                    html.Div(id="user_best_rank", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "red"},
            ),
            html.Div([
                    html.Div("Events Count", className="numeric-statistic-title"),
                    html.Div(id="user_events", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1"},
            ),
            html.Div([
                    html.Div("Avg. Interval", className="numeric-statistic-title"),
                    html.Div(id="user_average_interval", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1"},
            ),
            html.Div([
                    html.Div("Longest Streak", className="numeric-statistic-title"),
                    html.Div(id="user_longest_streak", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1"},
            ),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "gap": "20px",
            "paddingLeft": "60px",
            "paddingRight": "60px",
        })

    return html.Div([
        html.H2("User Statistics"),
        user_dropdown(analytics),
        length_history(),
        numeric_statistics(),
    ])

def init(analytics: Analytics):
    app = dash.Dash(__name__)
    pio.templates["fonts"] = go.layout.Template(
        layout=go.Layout(title_font=dict(family="Avenir Next", size=24))
    )
    pio.templates.default = 'plotly_dark+fonts'
    app.layout = html.Div([
       html.H1(
        "Pesun Analytics",
        style={
            "marginTop": "20px",
            "marginBottom": "40px",
        }),
        current_length(analytics),
        user_statstics(analytics),
    ])
    @app.callback(
        Output("user_length_history", "figure"),
        Output("user_best_rank", "children"),
        Output("user_events", "children"),
        Output("user_average_interval", "children"),
        Output("user_longest_streak", "children"),
        Input("user_dropdown", "value"))
    def update_user(user: str):
        history = analytics.get_user_length_history(user)
        df = pd.DataFrame({
            "Date": list(map(lambda entry: entry[0], history)),
            "Length": list(map(lambda entry: entry[1], history)),
        })
        fig = px.line(df, x="Date", y="Length", title=f"{user}'s Length History")
        return fig, "#3", "100", "5 days", "3 days"
    app.run(debug=True)
