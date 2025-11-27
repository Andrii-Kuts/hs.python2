from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

import numpy as np
from analytics import Analytics
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from utils import *
from plotly.colors import sample_colorscale, sequential

class PlotsData:
    def __init__(self, analytics: Analytics = None, selected_user: str = None):
        self.analytics = analytics
        self.selected_user = selected_user

T = TypeVar("T")

class Plot(Generic[T], ABC):
    @classmethod
    @abstractmethod
    def create(cls, plotsData: PlotsData) -> T:
        pass
    @classmethod
    @abstractmethod
    def output_type(cls) -> str:
        pass
    @classmethod
    @abstractmethod
    def get_id(cls) -> str:
        pass

class FigurePlot(Plot[go.Figure], ABC):
    @classmethod
    def output_type(cls):
        return "figure"

class ChildrenPlot(Plot[str], ABC):
    @classmethod
    def output_type(cls):
        return "children"
    
class CurrentLengthPlot(FigurePlot):
    @classmethod
    def create(cls, plotsData):
        analytics = plotsData.analytics
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
        return fig
    @classmethod
    def get_id(cls):
        return "current_length"
    
class BestPlayerHistoryPlot(FigurePlot):
    @classmethod
    def create(cls, plotsData):
        analytics = plotsData.analytics
        history = analytics.get_best_players_history()
        print(history[-1])
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
        return fig
    @classmethod
    def get_id(cls):
        return "best_player_history"
    
class TopPlayerPiePlot(FigurePlot):
    @classmethod
    def create(cls, plotsData):
        analytics = plotsData.analytics
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
    @classmethod
    def get_id(cls):
        return "top_player_pie"
    
class GamesPiePlot(FigurePlot):
    @classmethod
    def create(cls, plotsData):
        analytics = plotsData.analytics
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
            title="Games Count"
        )
        fig.update_layout(
            showlegend=False,
        )
        fig.update_traces(
            textposition="inside",
        )
        return fig
    @classmethod
    def get_id(cls):
        return "games_pie"
    
class UserPlots:
    class LengthHistoryPlot(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
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
        @classmethod
        def get_id(cls):
            return "user_length_history"
        
    class BestRankPlot(ChildrenPlot):
        @classmethod
        def create(self, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            best_rank = analytics.get_user_best_rank(user)
            return f"#{best_rank}"
        @classmethod
        def get_id(self):
            return "user_best_rank"
    
    class GamesCountPlot(ChildrenPlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            events_count = analytics.get_user_events_count(user)
            return str(events_count)
        @classmethod
        def get_id(cls):
            return "user_games_count"
    
    class AverageIntervalPlot(ChildrenPlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            average_interval = analytics.get_user_average_interval(user)
            interval_days = round(average_interval.total_seconds() / (60 * 60 * 24), 2)
            return f"{interval_days} days"
        @classmethod
        def get_id(cls):
            return "user_average_interval"
    
    class BestStreakPlot(ChildrenPlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            best_streak = analytics.get_user_best_streak(user)[2]
            return format_plural(best_streak, "day")
        @classmethod
        def get_id(cls):
            return "user_best_streak"
    
    class CurrentStreakPlot(ChildrenPlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            current_streak = analytics.get_user_current_streak(user)
            return format_plural(current_streak, "day")
        @classmethod
        def get_id(cls):
            return "user_current_streak"
        
    class GamesByDay(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            deltas = analytics.get_user_deltas(user)
            df = pd.DataFrame({
                "Date": pd.to_datetime(list(map(lambda entry: entry[0], deltas))),
                "Delta": list(map(lambda entry: entry[1], deltas)),
            })
            df_day = pd.DataFrame({
                "Day": df["Date"].dt.day_name()
            })
            fig_day = px.histogram(
                df_day,
                x="Day",
                category_orders={"Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
                title=f"Events by Day",
                color_discrete_sequence=["DeepSkyBlue"],
            )
            return fig_day
        @classmethod
        def get_id(cls):
            return "user_games_by_day"
    class GamesByHour(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            deltas = analytics.get_user_deltas(user)
            df = pd.DataFrame({
                "Date": pd.to_datetime(list(map(lambda entry: entry[0], deltas))),
                "Delta": list(map(lambda entry: entry[1], deltas)),
            })
            df_hour = pd.DataFrame({
                "Hour": df["Date"].dt.hour,
            })
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
            return fig_time
        @classmethod
        def get_id(cls):
            return "user_games_by_hour"
    class GamesByDelta(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            user = plotsData.selected_user
            deltas = analytics.get_user_deltas(user)
            df = pd.DataFrame({
                "Date": pd.to_datetime(list(map(lambda entry: entry[0], deltas))),
                "Delta": list(map(lambda entry: entry[1], deltas)),
            })
            df_delta = pd.DataFrame({
                "Delta": df["Delta"]
            })
            fig_delta = px.histogram(
                df_delta,
                x="Delta",
                title=f"Events by Delta",
                color_discrete_sequence=["DeepSkyBlue"],
                nbins=16
            )
            return fig_delta
        @classmethod
        def get_id(cls):
            return "user_games_by_delta"
    
    @classmethod
    def get_all_plots(cls) -> list[Type[Plot]]:
        return [
            cls.LengthHistoryPlot,
            cls.BestRankPlot,
            cls.GamesCountPlot,
            cls.AverageIntervalPlot,
            cls.BestStreakPlot,
            cls.CurrentStreakPlot,
            cls.GamesByDay,
            cls.GamesByHour,
            cls.GamesByDelta
        ]
    
class RankingPlots:
    class AverageIntervalPlot(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
            users = analytics.get_users()
            average_intervals = list(map(lambda user: (user, analytics.get_user_average_interval(user)), users))
            average_intervals = sorted(filter(lambda entry: entry[1].total_seconds() > 0, average_intervals), key=lambda entry: entry[1], reverse=True)
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
            return fig
        @classmethod
        def get_id(cls):
            return "ranking_average_interval"
    
    class LongestStreakPlot(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
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
            return fig
        @classmethod
        def get_id(cls):
            return "ranking_longest_streak"
        
    class CurrentStreakPlot(FigurePlot):
        @classmethod
        def create(cls, plotsData):
            analytics = plotsData.analytics
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
            return fig
        @classmethod
        def get_id(cls):
            return "ranking_current_streak"
        
    @classmethod
    def get_all_plots(cls) -> list[Type[Plot]]:
        return [
            cls.AverageIntervalPlot,
            cls.LongestStreakPlot,
            cls.CurrentStreakPlot,
        ]
    
def get_non_user_plots() -> list[Type[Plot]]:
    result: list[Type[Plot]] = [CurrentLengthPlot, BestPlayerHistoryPlot, TopPlayerPiePlot, GamesPiePlot]
    result.extend(RankingPlots.get_all_plots())
    return result
