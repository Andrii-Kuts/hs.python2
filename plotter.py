import asyncio
import socket
import threading
from wsgiref.simple_server import WSGIServer, make_server
from analytics import Analytics
import dash
from dash import dcc, html, Input, Output, Dash, State
import plotly.io as pio
import plotly.graph_objects as go
import os
from utils import *
from threading import Thread
from asyncio import Future, get_running_loop
from utils import hash_group_id
from database.database import Database
from plots import *

def user_dropdown():
    return html.Div([
        html.H4("Select User"),
        dcc.Dropdown(
            id="user_dropdown",
            options=[],
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

def user_statistics():
    def length_history():
        return dcc.Graph(id=UserPlots.LengthHistoryPlot.get_id())
    
    def numeric_statistics():
        return html.Div([
            html.Div([
                    html.Div("Best Rank", className="numeric-statistic-title"),
                    html.Div(id=UserPlots.BestRankPlot.get_id(), className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Games Count", className="numeric-statistic-title"),
                    html.Div(id=UserPlots.GamesCountPlot.get_id(), className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Avg. Interval", className="numeric-statistic-title"),
                    html.Div(id=UserPlots.AverageIntervalPlot.get_id(), className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Longest Streak", className="numeric-statistic-title"),
                    html.Div(id=UserPlots.BestStreakPlot.get_id(), className="numeric-statistic-value"),
                ],
                className="numeric-statistic",
                style={"flex": "1", "color": "DeepSkyBlue"},
            ),
            html.Div([
                    html.Div("Current Streak", className="numeric-statistic-title"),
                    html.Div(id=UserPlots.CurrentStreakPlot.get_id(), className="numeric-statistic-value"),
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
                dcc.Graph(
                    id=UserPlots.GamesByDay.get_id(),
                    style={"height": "100%", "width": "100%"},  
                ),
                style={"flex": "1"},
            ),
            html.Div(
                dcc.Graph(
                    id=UserPlots.GamesByHour.get_id(),
                    style={"height": "100%", "width": "100%"},  
                ),
                style={"flex": "1"},
            ),
            html.Div(
                dcc.Graph(
                    id=UserPlots.GamesByDelta.get_id(),
                    style={"height": "100%", "width": "100%"},  
                ),
                style={"flex": "1"},
            ),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "paddingLeft": "20px",
            "paddingRight": "20px",
        })

    return html.Div([
        html.H2("User Statistics"),
        user_dropdown(),
        length_history(),
        numeric_statistics(),
        event_statistics(),
    ])

def user_rankings_panel():
    def left_panel():
        return html.Div([
            html.Div(
                dcc.Graph(
                    id=TopPlayerPiePlot.get_id(),
                    style={"height": "100%", "width": "100%"},
                ),
                style={"flex": "1", "height": "50%", "aspect-ratio": "1"},
            ),
            html.Div(
                dcc.Graph(
                    id=GamesPiePlot.get_id(),
                    style={"height": "100%", "width": "100%"},
                ),
                style={"flex": "1", "height": "50%", "aspect-ratio": "1"},
            ),
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
                dcc.Graph(
                    id=RankingPlots.AverageIntervalPlot.get_id(),
                    style={"height": "100%", "width": "100%"},
                ),
                style={"flex": "1"},
            ),
            html.Div(
                dcc.Graph(
                    id=RankingPlots.LongestStreakPlot.get_id(),
                    style={"height": "100%", "width": "100%"},
                ),
                style={"flex": "1"},
            ),
            html.Div(
                dcc.Graph(
                    id=RankingPlots.CurrentStreakPlot.get_id(),
                    style={"height": "100%", "width": "100%"},
                ),
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

def run(path: str, group_id: int):
    app = dash.Dash(__name__, routes_pathname_prefix=path, requests_pathname_prefix=path)
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
        dcc.Interval(id="refresh", interval=500, n_intervals=0, max_intervals=-1),
        dcc.Store(id='last_update', data=-1),
        dcc.Store(id='last_user_update', data=-1),
        dcc.Graph(id=CurrentLengthPlot.get_id()),
        dcc.Graph(id=BestPlayerHistoryPlot.get_id()),
        user_statistics(),
        user_rankings_panel(),
    ])

    update_counter = 0
    analytics: Analytics = None
    lock = threading.Lock()

    def get_analytics():
        event_loop = Database.get_event_loop()
        db = asyncio.run_coroutine_threadsafe(Database.get_instance(), event_loop).result()
        analytics = asyncio.run_coroutine_threadsafe(db.read_analytics(group_id), event_loop).result()
        return analytics

    outputs = [Output("last_update", "data"), Output("last_user_update", "data"), Output("user_dropdown", "value"), Output("user_dropdown", "options")] + \
        [Output(plot.get_id(), plot.output_type()) for plot in get_non_user_plots()]
    @app.callback(
        outputs,
        Input("refresh", "n_intervals"),
        State("last_update", "data"),
        State("user_dropdown", "value"),
        State("user_dropdown", "options"),
    )
    def refresh(n_intervals, last_update, selected_user: str, user_options: list[str]):
        with lock:
            if update_counter > last_update:
                print("UPDATE")
                nonlocal analytics
                analytics = get_analytics()
                if analytics is None:
                    logger.error("Something went wrong while refreshing analytics")
                new_users = sorted(analytics.get_users())
                new_selected_user = selected_user
                if selected_user is None or selected_user not in new_users:
                    new_selected_user = new_users[0] if len(new_users) > 0 else None
                plotsData = PlotsData(analytics, new_selected_user)
                return update_counter, update_counter, new_selected_user, new_users, *[plot.create(plotsData) for plot in get_non_user_plots()]
        raise dash.exceptions.PreventUpdate
    
    dropdown_outputs = [Output(plot.get_id(), plot.output_type()) for plot in UserPlots.get_all_plots()]
    @app.callback(
        dropdown_outputs,
        Input("last_user_update", "data"),
        Input("user_dropdown", "value"),
    )
    def refresh_user(last_user_update, selected_user: str):
        print("UPDATE USERS")
        plotsData = PlotsData(analytics, selected_user)
        return tuple([plot.create(plotsData) for plot in UserPlots.get_all_plots()])
    
    @app.server.route(f"{path}update", methods=["POST"])
    def update_plots():
        nonlocal lock
        nonlocal update_counter
        with lock:
            update_counter += 1
            return "OK", 200
        return "Failed", 400
    
    is_debug = os.getenv("DEBUG") == "TRUE"
    host = os.getenv("DASH_HOST")
    port = int(os.getenv("DASH_PORT"))
    app.server.debug = is_debug
    server: WSGIServer = make_server(host=host, port=port, app=app.server)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    app.server.app_context().push()
    thread = Thread(target=lambda: server.serve_forever(), daemon=True)

    thread.start()
    return app, server, thread

class PlotterData:
    def __init__(self, app: Dash, server: WSGIServer, thread: Thread, path: str):
        self.app = app
        self.server = server
        self.thread = thread
        self.path = path

class PlotterPool:
    _instance: PlotterPool = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PlotterPool()
        return cls._instance

    def __init__(self):
        self.plotters: dict[int, PlotterData] = {}

    def get_plotter_data(self, group_id: int):
        return self.plotters.get(group_id)

    def stop_plotter(self, group_id: int) -> Future[None]:
        loop = get_running_loop()
        future: Future[None] = loop.create_future()
        plotterData = self.get_plotter_data(group_id)
        if plotterData is None:
            future.set_result(None)
            return future
        def stop_app():
            plotterData.server.shutdown()
            plotterData.server.socket.close()
            plotterData.thread.join()
            loop.call_soon_threadsafe(future.set_result, None)
        thread = Thread(target=stop_app, daemon=True)
        thread.start()
        return future

    def start_plotter(self, group_id: int):
        path = f"/{hash_group_id(group_id)}/"
        app, server, thread = run(path, group_id)
        return PlotterData(app, server, thread, path)

    async def get_or_start_plotter(self, group_id: int):
        plotterData = self.get_plotter_data(group_id)
        if plotterData is not None:
            return plotterData
        await self.stop_plotter(group_id)
        plotterData = self.start_plotter(group_id)
        self.plotters[group_id] = plotterData
        return plotterData
    
    def get_plotter(self, group_id: int):
        return self.get_plotter_data(group_id)
    
    async def stop_plotters(self):
        for group_id in self.plotters:
            await self.stop_plotter(group_id)

