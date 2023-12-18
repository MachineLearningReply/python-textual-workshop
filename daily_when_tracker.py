from typing import Union
import datetime
import pandas as pd
from pathlib import Path
from textual.app import App
from textual.widget import Widget
from textual.widgets import Header, Footer, DataTable, Static, Input, Button, ContentSwitcher
from textual.validation import Integer, Length
from textual.containers import Horizontal
from textual import on
from textual_plotext import PlotextPlot


class DataView(Widget):
    COLS = ("date", "day", "time", "task", "alertness", "energy")
    FILE_PATH = Path("daily_when_tracker.csv")

    def compose(self):
        yield DataTable(zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.focus()

        for col in self.COLS:
            table.add_column(label=col.upper(), key=col)

        if self.FILE_PATH.is_file():
            df = pd.read_csv(self.FILE_PATH)
            table.add_rows(df.to_dict(orient="split")["data"])
        else:
            with open(self.FILE_PATH, "w") as file:
                file.writelines([", ".join(self.COLS)])

        self.sort()

    def get_df(self) -> pd.DataFrame:
        table = self.query_one(DataTable)
        content = []

        for i in range(len(table.rows.values())):
            content.append(table.get_row_at(i))

        df = pd.DataFrame(content, columns=self.COLS)
        return df.astype({"energy": int, "alertness": int})

    def sort(self):
        self.query_one(DataTable).sort("date", "time", reverse=True)


class ErrorDisplay(Static):
    def _on_mount(self) -> None:
        self.no_error_message()

    def no_error_message(self):
        self.styles.display = "none"

    def display_error_message(self, msg: str):
        self.update(msg)
        self.styles.display = "block"


class InputView(Widget):
    def compose(self):
        with Horizontal(id="input-array"):
            yield Input(
                placeholder="What am I doing?", id="task", type="text", validators=Length(minimum=1, maximum=255)
            )
            yield Input(
                placeholder="How mentally alert do I feel?",
                id="alertness",
                type="integer",
                validators=Integer(minimum=1, maximum=10),
            )
            yield Input(
                placeholder="How energetic do I feel?",
                id="energy",
                type="integer",
                validators=Integer(minimum=1, maximum=10),
            )

        yield ErrorDisplay()

        with Horizontal(id="input-buttons"):
            yield Button("Submit", id="submit", variant="success")
            yield Button("Back", classes="back-button", id="input-back", variant="error")

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        if event.validation_result is None:
            pass
        elif not event.validation_result.is_valid and len(event.validation_result.failure_descriptions) > 0:
            self.query_one(ErrorDisplay).display_error_message(f"{event.validation_result.failure_descriptions[0]}")
        else:
            self.query_one(ErrorDisplay).no_error_message()


class Plotview(Widget):
    def compose(self):
        with Horizontal(id="plot-tabs"):
            yield Button("Time over Total", id="time-over-total")
            yield Button("Time over Alertness", id="time-over-alertness")
            yield Button("Time over Energy", id="time-over-energy")
            yield Button("Back", classes="back-button", id="plot-back", variant="error")

        with ContentSwitcher(initial="time-over-total"):
            yield PlotextPlot(classes="bar-plot", id="time-over-total")
            yield PlotextPlot(classes="bar-plot", id="time-over-alertness")
            yield PlotextPlot(classes="bar-plot", id="time-over-energy")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "plot-back":
            self.query_one(ContentSwitcher).current = event.button.id

    def plot_total(self, x, y):
        plt = self.query(PlotextPlot).filter("#time-over-total").only_one().plt
        plt.bar(x, y, color="orange")
        plt.xlabel("Time of day")
        plt.ylabel("Total Score")
        plt.ylim(0, 20)
        plt.yticks(list(range(21)))
        plt.title("Total score over time of day")

    def plot_alertness(self, x, y):
        plt = self.query(PlotextPlot).filter("#time-over-alertness").only_one().plt
        plt.bar(x, y, color="red")
        plt.xlabel("Time of day")
        plt.ylabel("Alertness")
        plt.ylim(0, 10)
        plt.yticks(list(range(11)))
        plt.title("Alertness over time of day")

    def plot_energy(self, x, y):
        plt = self.query(PlotextPlot).filter("#time-over-energy").only_one().plt
        plt.bar(x, y, color="blue")
        plt.xlabel("Time of day")
        plt.ylabel("Energy")
        plt.ylim(0, 10)
        plt.yticks(list(range(11)))
        plt.title("Energy over time of day")


class WhenTrackerApp(App):
    TITLE = "When Tracker"
    BINDINGS = [
        ("a", "add_row", "Add Row"),
        ("r", "remove_row", "Delete Row"),
        ("p", "show_plots", "Plot"),
        ("s", "save", "Save"),
        ("e", "exit_application", "Exit"),
        ("d", "toggle_dark_mode", "Toggle Dark Mode"),
    ]

    CSS_PATH = "daily_when_tracker.css"

    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        yield DataView(id="data-view")
        yield InputView(id="input-view")
        yield Plotview(id="plot-view")

    @staticmethod
    def round_time(dt: Union[datetime.datetime, None] = None, round_to: int = 60) -> datetime.datetime:
        """Round a datetime object to any time lapse in seconds
        dt : datetime.datetime object, default now.
        roundTo : Closest number of seconds to round to, default 1 minute.
        Author: Thierry Husson 2012 - Use it as you want but don't blame me.
        """
        if dt is None:
            dt = datetime.datetime.now()
        seconds = (dt.replace(tzinfo=None) - dt.min).seconds
        rounding = (seconds + round_to / 2) // round_to * round_to
        return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)

    def show_data(self) -> None:
        self.query_one(InputView).styles.display = "none"
        self.query_one(Plotview).styles.display = "none"

        data_view = self.query_one(DataView)
        data_view.styles.display = "block"

        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.focus()

    def action_toggle_dark_mode(self) -> None:
        self.dark = not self.dark

    def action_add_row(self) -> None:
        self.query_one(DataView).styles.display = "none"
        self.query_one(Plotview).styles.display = "none"
        self.query_one(InputView).styles.display = "block"

        input = self.query(Input).first()
        input.focus()

    @on(Button.Pressed, "#time-over-total")
    def plot_total(self) -> None:
        df = self.query_one(DataView).get_df()
        df["total"] = df.energy + df.alertness
        x = sorted(df.time.unique())
        y = list(df[["time", "total"]].groupby("time").median().total)

        self.query_one(Plotview).plot_total(x, y)

    @on(Button.Pressed, "#time-over-alertness")
    def plot_alertness(self) -> None:
        df = self.query_one(DataView).get_df()
        x = sorted(df.time.unique())
        y = list(df[["time", "alertness"]].groupby("time").median().alertness)

        self.query_one(Plotview).plot_alertness(x, y)

    @on(Button.Pressed, "#time-over-energy")
    def plot_energy(self) -> None:
        df = self.query_one(DataView).get_df()
        x = sorted(df.time.unique())
        y = list(df[["time", "energy"]].groupby("time").median().energy)

        self.query_one(Plotview).plot_energy(x, y)

    def action_show_plots(self) -> None:
        self.query_one(InputView).styles.display = "none"
        self.query_one(DataView).styles.display = "none"
        self.query_one(Plotview).styles.display = "block"

        self.plot_total()
        plot = self.query(PlotextPlot).filter("#time-over-total").only_one()
        plot.focus()

    def action_remove_row(self) -> None:
        if self.query_one(DataView).styles.display == "block":
            table = self.query_one(DataTable)
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            table.remove_row(row_key)

    def action_save(self) -> None:
        data_view = self.query_one(DataView)

        df = data_view.get_df()
        df.to_csv(data_view.FILE_PATH, index=False)

    def action_exit_application(self) -> None:
        self.exit()

    @on(Button.Pressed, ".back-button")
    def back_to_view(self) -> None:
        self.show_data()

    @on(Button.Pressed, "#submit")
    def submit_entries(self) -> None:
        inputs = self.query(Input)
        valdiations = (input.validate(input.value).is_valid for input in inputs if len(input.validators) > 0)

        if not all(valdiations):
            return None

        dt = self.round_time(round_to=60 * 30)
        content = [dt.strftime("%Y-%m-%d"), dt.strftime("%A"), dt.strftime("%H:%M")]
        for input in inputs:
            content.append(input.value)
            input.clear()

        table = self.query_one(DataTable)
        table.add_row(*content)
        self.query_one(DataView).sort()
        self.show_data()


app = WhenTrackerApp()
if __name__ == "__main__":
    app.run()
