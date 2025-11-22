from analytics import Analytics
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import os
from utils import *
from plotly.colors import sample_colorscale, sequential
import numpy as np

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
        return format_duration(entry[2] - entry[1])
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

def user_statistics(analytics: Analytics):
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
            html.Div([
                    html.Div("Current Streak", className="numeric-statistic-title"),
                    html.Div(id="user_current_streak", className="numeric-statistic-value"),
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

def top_player_pie_figure(analytics: Analytics):
    durations = analytics.get_user_domination_durations()
    df = pd.DataFrame({
        "User": list(map(lambda entry: entry[0], durations.items())),
        "Duration": list(map(lambda entry: entry[1].total_seconds(), durations.items())),
        "DurationHuman": list(map(lambda entry: format_duration(entry[1]), durations.items())),
    })
    fig = px.pie(
        df,
        values="Duration",
        names="User",
        custom_data=["DurationHuman"],
        title="Duration as Best Player"
    )
    fig.update_traces(
        hovertemplate="User: %{label}<br>Duration: %{customdata[0]}",
    )
    fig.update_layout(
        showlegend=False,
    )
    return fig

def events_pie_figure(analytics: Analytics):
    events = analytics.get_all_deltas()
    df = pd.DataFrame({
        "User": list(map(lambda entry: entry[0], events)),
    })
    df_counts = df.value_counts("User").reset_index()
    df_counts.columns = ["User", "Count"]
    fig = px.pie(
        df_counts,
        names="User",
        values="Count",
        title="Events Count"
    )
    fig.update_layout(
        showlegend=False,
    )
    return fig

def user_rankings_panel(analytics: Analytics):
    def average_interval():
        users = analytics.get_users()
        average_intervals = list(map(lambda user: (user, analytics.get_user_average_interval(user)), users))
        average_intervals = sorted(average_intervals, key=lambda entry: entry[1], reverse=True)
        df = pd.DataFrame({
            "User": list(map(lambda entry: entry[0], average_intervals)),
            "Days": list(map(lambda entry: entry[1].total_seconds() / (24*60*60), average_intervals)),
            "DaysLog": list(map(lambda entry: np.log10(entry[1].total_seconds() / (24*60*60)), average_intervals)),
        })
        fig = px.bar(
            df,
            y="User",
            x="Days",
            title="Average Interval",
            orientation="h",
            log_x=True,
            color="DaysLog",
            color_continuous_scale=sequential.Aggrnyl_r,
            hover_data={"User": True, "Days": True, "DaysLog": False},
        )
        fig.update_layout(coloraxis_showscale=False)
        return dcc.Graph(
            figure=fig,
            style={"height": "100%", "width": "100%"},
            config={"responsive": True}
        )
    
    def longest_streak():
        users = analytics.get_users()
        longest_streaks = list(map(lambda user: (user, analytics.get_user_best_streak(user)), users))
        longest_streaks = sorted(longest_streaks, key=lambda entry: entry[1][2])
        df = pd.DataFrame({
            "User": list(map(lambda entry: entry[0], longest_streaks)),
            "Duration": list(map(lambda entry: entry[1][2], longest_streaks)),
            "Start": list(map(lambda entry: format_date(entry[1][0]), longest_streaks)),
            "End": list(map(lambda entry: format_date(entry[1][1]), longest_streaks)),
        })
        fig = px.bar(
            df,
            y="User",
            x="Duration",
            title="Longest Streak",
            orientation="h",
            color="Duration",
            color_continuous_scale=sequential.Aggrnyl,
            hover_data=["User", "Duration", "Start", "End"],
        )
        fig.update_layout(coloraxis_showscale=False)
        return dcc.Graph(
            figure=fig,
            style={"height": "100%", "width": "100%"},
            config={"responsive": True}
        )
    
    def current_streak():
        users = analytics.get_users()
        current_streaks = list(map(lambda user: (user, analytics.get_user_current_streak(user)), users))
        current_streaks = sorted(filter(lambda entry: entry[1] > 0, current_streaks), key=lambda entry: entry[1])
        df = pd.DataFrame({
            "User": list(map(lambda entry: entry[0], current_streaks)),
            "Duration": list(map(lambda entry: entry[1], current_streaks)),
        })
        fig = px.bar(
            df,
            y="User",
            x="Duration",
            title="Current Streak",
            orientation="h",
            color="Duration",
            color_continuous_scale=sequential.Aggrnyl,
        )
        fig.update_layout(coloraxis_showscale=False)
        return dcc.Graph(
            figure=fig,
            style={"height": "100%", "width": "100%"},
            config={"responsive": True}
        )

    def left_panel():
        return html.Div([
            html.Div(
                dcc.Graph(
                    figure=top_player_pie_figure(analytics),
                    style={"height": "100%", "width": "100%"},
                    config={"responsive": True},
                    id="top_player_pie",
                ),
                style={"flex": "1", "height": "50%", "aspect-ratio": "1"},
            ),
            html.Div(
                dcc.Graph(
                    figure=events_pie_figure(analytics),
                    style={"height": "100%", "width": "100%"},
                    config={"responsive": True},
                    id="events_pie",
                ),
                style={"flex": "1", "height": "50%", "aspect-ratio": "1"},
            ),
            dcc.Interval(id="pies_refresh", interval=100, n_intervals=0, max_intervals=1),
        ], style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "gap": "0px",
            "padding": "0px",
            "align-self": "stretch",
        })
    def right_panel():
        return html.Div([
            html.Div(
                average_interval(),
                style={"flex": "1"},
            ),
            html.Div(
                longest_streak(),
                style={"flex": "1"},
            ),
            html.Div(
                current_streak(),
                style={"flex": "1"},
            ),
        ], style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "gap": "0px",
            "padding": "0px",
        })
    return html.Div([
        html.H2("Rankings"),
        html.Div([
            left_panel(),
            right_panel(),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "gap": "20px",
            "marginTop": "40px",
        }),
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
        user_statistics(analytics),
        user_rankings_panel(analytics),
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
        streaks = list(filter(lambda streak: streak[2] > 1, analytics.get_user_streaks(user)))
        count = 10
        streaks = sorted(streaks, key=lambda streak: streak[2], reverse=True)[:count]
        for i in range(len(streaks)):
            streak = streaks[i]
            color = sample_colorscale(sequential.Aggrnyl_r, i / (count-1), colortype="hex")[0]
            color = f"rgb({color[0]},{color[1]},{color[2]})"
            name = f"Streak #{i+1}"
            fig.add_trace(
                go.Scatter(
                    x=[streak[0], streak[1]],
                    y=[0, 0],
                    mode="lines",
                    line=dict(color=color, width=10),
                    hoverinfo="text",
                    text=f"{name}<br>Duration: {format_plural(streak[2], "day")}<br>Start: {format_date(streak[0])}<br>End: {format_date(streak[1])}",
                    name=name
                )
            )
        return fig

    @app.callback(
        Output("user_best_rank", "children"),
        Output("user_events", "children"),
        Output("user_average_interval", "children"),
        Output("user_longest_streak", "children"),
        Output("user_current_streak", "children"),
        Input("user_dropdown", "value"))
    def update_user_numerics(user: str):
        best_rank = analytics.get_user_best_rank(user)
        events_count = analytics.get_user_events_count(user)
        average_interval = analytics.get_user_average_interval(user)
        interval_days = round(average_interval.total_seconds() / (60 * 60 * 24), 2)
        best_streak = analytics.get_user_best_streak(user)[2]
        current_streak = analytics.get_user_current_streak(user)
        return f"#{best_rank}", events_count, f"{interval_days} days", format_plural(best_streak, "day"), format_plural(current_streak, "day")
    
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
        df_hour = pd.DataFrame({
            "Hour": df["Date"].dt.hour,
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
        fig_time = px.histogram(
            df_hour,
            x="Hour",
            title=f"Events by Hour",
            color_discrete_sequence=["DeepSkyBlue"],
            nbins=24,
        )
        fig_time.update_traces(
            hovertemplate="Interval: %{x:02d}:00 - %{customdata:02d}:00<br>Count: %{y}<extra></extra>",
            customdata=[(h + 1) % 24 for h in range(24)],
        )
        fig_delta = px.histogram(
            df_delta,
            x="Delta",
            title=f"Events by Delta",
            color_discrete_sequence=["DeepSkyBlue"],
            nbins=16
        )
        return fig_day, fig_time, fig_delta
    
    @app.callback(
        Output("top_player_pie", "figure"),
        Output("events_pie", "figure"),
        Input("pies_refresh", "n_intervals")
    )
    def refresh_pie(n):
        if n > 1:
            return dash.no_update
        fig_top_player = top_player_pie_figure(analytics)
        fig_events = events_pie_figure(analytics)
        return fig_top_player, fig_events
    
    is_debug = os.getenv("DEBUG") == "TRUE"
    app.run(host="0.0.0.0", port=8050, debug=is_debug)
