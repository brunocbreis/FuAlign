from dataclasses import dataclass
import tkinter as tk


class Color:
    HOVER = "#c1c1c1"
    NORMAL = "#868686"
    ACTIVE = "#f1f1f1"
    CANVAS_BG = "#252525"
    TEXT = "#A3A3A3"


class Font:
    DEFAULT = "TkTextFont"
    TOOLTIP_BOLD = "TkTooltipFont 12 bold"
    TOOLTIP = "TkTooltipFont 12"


@dataclass
class UIRow:
    parent: tk.Widget
    frame: tk.Frame
    name: str

    def __post_init__(self):
        self.title_var = tk.StringVar()
        self.title = tk.Label(
            self.frame,
            textvariable=self.title_var,
            width=20,
            height=1 if self.name in ["header", "footer"] else 2,
            anchor=tk.SW,
            padx=5,
            pady=0 if self.name in ["header", "footer"] else 5,
        )
        self.title.grid(column=1, columnspan=4, row=1, sticky=tk.W)

    def describe(self, name: str, key: str = None):
        words_in_name = self.name.split()
        two_words = len(words_in_name) > 1

        if name:
            name = f" {name}"

        self.title_var.set(
            f"{words_in_name[0].capitalize()}{name}"
            f" {words_in_name[-1] if two_words else ''}{f' [{key}]' if key else ''}"
        )


@dataclass
class UIElement:
    parent: UIRow
    name: str
    row: int
    col: int
    canvas: tk.Canvas = None
    icon_dims: list[tuple] = None
    key: str = None

    def describe(self, event):
        self.parent.describe(self.name, self.key)

    def undescribe(self, event):
        self.parent.describe("")

    # Creates rectangle from normalized dimensions instead of absolute coordinates.
    def draw_rect(
        self,
        width: float,
        height: float,
        x: float,
        y: float,
        **configs,
    ) -> int:

        multiplier = self.canvas.winfo_width()

        x0 = x * multiplier
        x1 = (x + width) * multiplier
        y0 = y * multiplier
        y1 = (y + height) * multiplier

        return self.canvas.create_rectangle(x0, y0, x1, y1, **configs)

    # Creates all rectangles necessary to draw each icon
    def draw_icon(self, **config) -> None:
        for dim in self.icon_dims:
            self.draw_rect(*dim, **config)
        set_hover_style(self.canvas)


# Button style events  ========================================
def on_hover(event: tk.Event):
    canvas: tk.Canvas = event.widget
    canvas.itemconfig("icon", fill=Color.HOVER)


def on_leave(event: tk.Event):
    canvas: tk.Canvas = event.widget
    canvas.itemconfig("icon", fill=Color.NORMAL)


def on_click(event: tk.Event):
    canvas: tk.Canvas = event.widget
    canvas.itemconfig("icon", fill=Color.ACTIVE)


def set_hover_style(canvas: tk.Canvas):
    canvas.bind("<Enter>", on_hover)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)
    canvas.bind("<ButtonRelease-1>", on_hover)


# Dict of dimensions for drawing the icons. (width, height, x, y)
ICON_DIMS = {
    "left": [
        (0.1, 1, 0.05, 0),  # line
        (0.7, 0.3, 0.25, 0.15),  # rect1
        (0.5, 0.3, 0.25, 0.55),  # rect 2
    ],
    "horizontal": [
        (0.1, 1, 0.45, 0),  # line
        (0.5, 0.3, 0.25, 0.15),  # rect1
        (0.7, 0.3, 0.15, 0.55),  # rect2
    ],
    "right": [
        (0.1, 1, 0.85, 0),  # line
        (0.7, 0.3, 0.05, 0.15),  # rect1
        (0.5, 0.3, 0.25, 0.55),  # rect2
    ],
    "vertically": [
        (1, 0.1, 0, 0.1),  # line1
        (0.6, 0.3, 0.2, 0.35),  # rect1
        (1, 0.1, 0, 0.8),  # line2
    ],
    "top": [
        (1, 0.1, 0, 0.05),  # line
        (0.3, 0.7, 0.15, 0.25),  # rect1
        (0.3, 0.5, 0.55, 0.25),  # rect 2
    ],
    "vertical": [
        (1, 0.1, 0, 0.45),  # line
        (0.3, 0.5, 0.15, 0.25),  # rect1
        (0.3, 0.7, 0.55, 0.15),  # rect2
    ],
    "bottom": [
        (1, 0.1, 0, 0.85),  # line
        (0.3, 0.7, 0.15, 0.05),  # rect1
        (0.3, 0.5, 0.55, 0.25),  # rect2
    ],
    "horizontally": [
        (0.1, 1, 0.1, 0),  # line1
        (0.3, 0.6, 0.35, 0.2),  # rect1
        (0.1, 1, 0.8, 0),  # line2
    ],
}

KEYS = dict(
    top="T",
    left="L",
    right="R",
    bottom="B",
    vertical="V",
    horizontal="H",
    vertically="⌥V",
    horizontally="⌥H",
)


class App:
    APP_ROWS = {
        "header": None,
        "align edges": ["left", "top", "bottom", "right"],
        "align centers": ["vertical", "horizontal"],
        "distribute": ["vertically", "horizontally"],
        "footer": None,
    }

    def build(self):
        root = tk.Tk()
        self.root = root

        # Appearance.
        root.configure(background=Color.CANVAS_BG)
        root.title("FuAlign")
        root.resizable(False, False)
        root.option_add("*background", Color.CANVAS_BG)
        root.option_add("*foreground", Color.TEXT)

        # Setting up layout.
        root.rowconfigure(index=1, weight=0)  # HEADER ROW
        root.rowconfigure(index=2, weight=1)  # ALIGN EDGES ROW
        root.rowconfigure(index=3, weight=1)  # ALIGN CENTERS ROW
        root.rowconfigure(index=4, weight=1)  # DISTRIBUTE ROW
        root.rowconfigure(index=5, weight=0)  # FOOTER ROW

        # Creating UIRows.
        self.ui_rows: dict[str, UIRow] = {}
        for row in self.APP_ROWS:
            ui_row = UIRow(self.root, tk.Frame(padx=10), row)
            self.ui_rows[row] = ui_row
            if self.APP_ROWS[row]:
                ui_row.title_var.set(row.capitalize())

        for idx, row in enumerate(self.ui_rows.values()):
            row.frame.grid(row=idx + 1)

        # Configuring row grids.
        for row in self.ui_rows.values():
            row.frame.rowconfigure(index=1, weight=0)
            row.frame.rowconfigure(index=2, weight=1)

            row.frame.columnconfigure(index=1, weight=0)
            row.frame.columnconfigure(index=2, weight=0)
            row.frame.columnconfigure(index=3, weight=0)
            row.frame.columnconfigure(index=4, weight=1)

        # Creating UIElements.
        self.ui_elements: dict[str, UIElement] = {}
        for row_name, elements in self.APP_ROWS.items():
            if elements:
                for idx, element in enumerate(elements):
                    ui_element = UIElement(
                        parent=self.ui_rows[row_name], name=element, row=2, col=idx + 1
                    )
                    ui_element.icon_dims = ICON_DIMS[ui_element.name]

                    self.ui_elements[ui_element.name] = ui_element

        # Adding keys to UIElements.
        for key, el in self.ui_elements.items():
            if key in KEYS:
                el.key = KEYS[key]

        # Creating Canvases for the icons
        for el in self.ui_elements.values():
            el.canvas = tk.Canvas(
                el.parent.frame,
                width=20,
                height=20,
                background=Color.CANVAS_BG,
                highlightthickness=0,
                relief="ridge",
                bd=0,
            )
            el.canvas.grid(row=el.row, column=el.col, sticky=tk.W, padx=10, pady=5)

        # Updates canvas before drawing icons.
        for el in self.ui_elements.values():
            el.canvas.update()

        # Draws icons.
        for el in self.ui_elements.values():
            el.draw_icon(fill=Color.NORMAL, outline=Color.CANVAS_BG, tag="icon")

        # Binds canvases.
        for el in self.ui_elements.values():
            el.canvas.bind("<Enter>", el.describe, add="+")
            el.canvas.bind("<Leave>", el.undescribe, add="+")

    def run(self):
        self.build()

        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
