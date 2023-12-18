import pandas as pd
from pathlib import Path
from textual.app import App
from textual.widget import Widget
from textual.widgets import Header, Footer, DataTable

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

class WhenTrackerApp(App):
    TITLE = "When Tracker"
    BINDINGS = [
        ("e", "exit_application", "Exit"),
        ("d", "toggle_dark_mode", "Toggle Dark Mode"),
    ]

    CSS_PATH = "daily_when_tracker.css"

    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        yield DataView(id="data-view")

    def action_toggle_dark_mode(self) -> None:
        self.dark = not self.dark

    def action_exit_application(self) -> None:
        self.exit()

app = WhenTrackerApp()
if __name__ == "__main__":
    app.run()