from analytics import Analytics
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import dateutil.relativedelta

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

def best_player_history(analytics: Analytics):
    history = analytics.get_best_players_history()
    def entry_duration(entry):
        rd = dateutil.relativedelta.relativedelta(entry[2], entry[1])
        return "%d years, %d months, %d days, %d hours, %d minutes and %d seconds" % (rd.years, rd.months, rd.days, rd.hours, rd.minutes, rd.seconds)
    df = pd.DataFrame({
        "User": list(map(lambda entry : entry[0], history)),
        "Start": pd.to_datetime(list(map(lambda entry : entry[1], history)), utc=True),
        "End": pd.to_datetime(list(map(lambda entry : entry[2], history)), utc=True),
        "Period": list(range(1, len(history) + 1)),
        "Duration": list(map(entry_duration, history)),
    })
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Period",
        color="User",
        title="Best Player History",
        hover_data={"User": True, "Start": True, "End": True, "Duration": True, "Period": False},
    )
    return html.Div([
        dcc.Graph(figure=fig),
    ])

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
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Events Count", className="numeric-statistic-title"),
                    html.Div(id="user_events", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Avg. Interval", className="numeric-statistic-title"),
                    html.Div(id="user_average_interval", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Longest Streak", className="numeric-statistic-title"),
                    html.Div(id="user_longest_streak", className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "gap": "20px",
            "paddingLeft": "60px",
            "paddingRight": "60px",
        })
    
    def event_statistics():
        return html.Div([
            html.Div(
                dcc.Graph(id="user_events_day"),
                style={"flex": "1"},
            ),
            html.Div(
                dcc.Graph(id="user_events_time"),
                style={"flex": "1"},
            ),
            html.Div(
                dcc.Graph(id="user_events_delta"),
                style={"flex": "1"},
            ),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "gap": "20px",
            "paddingLeft": "20px",
            "paddingRight": "20px",
        })

    return html.Div([
        html.H2("User Statistics"),
        user_dropdown(analytics),
        length_history(),
        numeric_statistics(),
        event_statistics(),
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
        best_player_history(analytics),
        user_statstics(analytics),
    ])
    @app.callback(
        Output("user_length_history", "figure"),
        Input("user_dropdown", "value"))
    def update_user_length(user: str):
        history = analytics.get_user_length_history(user)
        df = pd.DataFrame({
            "Date": list(map(lambda entry: entry[0], history)),
            "Length": list(map(lambda entry: entry[1], history)),
        })
        fig = px.line(df, x="Date", y="Length", title=f"{user}'s Length History")
        return fig

    @app.callback(
        Output("user_best_rank", "children"),
        Output("user_events", "children"),
        Output("user_average_interval", "children"),
        Output("user_longest_streak", "children"),
        Input("user_dropdown", "value"))
    def update_user_numerics(user: str):
        best_rank = analytics.get_user_best_rank(user)
        events_count = analytics.get_user_events_count(user)
        average_interval = analytics.get_user_average_interval(user)
        interval_days = round(average_interval.total_seconds() / (60 * 60 * 24), 2)
        return f"#{best_rank}", events_count, f"{interval_days} days", "3 days"
    
    @app.callback(
        Output("user_events_day", "figure"),
        Output("user_events_time", "figure"),
        Output("user_events_delta", "figure"),
        Input("user_dropdown", "value"))
    def update_user_events(user: str):
        deltas = analytics.get_user_deltas(user)
        df = pd.DataFrame({
            "Date": list(map(lambda entry: entry[0], deltas)),
            "Delta": list(map(lambda entry: entry[1], deltas)),
        })
        df_day = pd.DataFrame({
            "Day": df["Date"].dt.day_name()
        })
        df_time = pd.DataFrame({
            "Time": df["Date"].dt.hour
        })
        df_delta = pd.DataFrame({
            "Delta": df["Delta"]
        })
        fig_day = px.histogram(
            df_day,
            x="Day",
            category_orders={"Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            title=f"Events by Day",
            color_discrete_sequence=["DeepSkyBlue"],
        )
        fig_time = px.histogram(df_time, x="Time", title=f"Events by Time", color_discrete_sequence=["DeepSkyBlue"])
        fig_delta = px.histogram(df_delta, x="Delta", title=f"Events by Delta", color_discrete_sequence=["DeepSkyBlue"])
        return fig_day, fig_time, fig_delta
    
    app.run(host="0.0.0.0", port=8050, debug=False)
