from __future__ import annotations
from dataclasses import dataclass
import tkinter as tk
from typing import Callable

# For testing inside VSCode.
try:
    from fa_backend import Tool, Comp, Fusion

    try:
        fusion
    except NameError:
        print("Initializing fake Fusion.")
        fusion = Fusion()
        comp = Comp()

except ModuleNotFoundError:
    pass

# =========================================================================== #
# ========================     BACKEND    =================================== #
# =========================================================================== #

# Constant for DataWindow Error.
NEG_MILL = -1_000_000
EMPTY_DATA_WINDOW = {key + 1: NEG_MILL for key in range(4)}


# Get tool from merge.
def get_tool(merge: Tool):
    return merge.Foreground.GetConnectedOutput().GetTool()


@dataclass
class Align:
    merge: Tool

    def __post_init__(self):
        self.fg_tool = get_tool(self.merge)

    @property
    def tool_pixel_width(self):
        return self.fg_tool.GetAttrs("TOOLI_ImageWidth")

    @property
    def tool_pixel_height(self):
        return self.fg_tool.GetAttrs("TOOLI_ImageHeight")

    @property
    def tool_img_pixel_width(self) -> int:
        if not self.tool_data_window:
            return self.tool_pixel_width

        x0, y0, x1, y1 = self.tool_data_window.values()
        return x1 - x0

    @property
    def tool_img_pixel_height(self) -> int:
        if not self.tool_data_window:
            return self.tool_pixel_height

        x0, y0, x1, y1 = self.tool_data_window.values()
        return y1 - y0

    @property
    def tool_rel_width(self):
        return self.tool_img_pixel_width * self.merge_size / self.merge_pixel_width

    @property
    def tool_rel_height(self):
        return self.tool_img_pixel_height * self.merge_size / self.merge_pixel_height

    @property
    def merge_pixel_width(self) -> int:
        return self.merge.GetAttrs("TOOLI_ImageWidth")

    @property
    def merge_pixel_height(self) -> int:
        return self.merge.GetAttrs("TOOLI_ImageHeight")

    @property
    def merge_size(self) -> float:
        return self.merge.GetInput("Size")

    @property
    def tool_center_coords(self) -> tuple[float, float]:
        """Returns a normalized value of the tool's 'Center' position relative to itself.
        If its image information is only a fraction of its width, this method will return
        where in the screen this information is centered. Else, we get the default 0.5, 0.5 values.
        """
        if self.tool_data_window:
            x0, y0, x1, y1 = self.tool_data_window.values()
        else:
            print(
                f"It looks like {self.fg_tool.GetAttrs('TOOLS_Name')} is off screen. Alignment might not work properly."
            )
            return 0.5, 0.5

        x = self.tool_img_pixel_width / 2 + x0
        y = self.tool_img_pixel_height / 2 + y0

        # Normalized...
        x = x / self.tool_pixel_width
        y = y / self.tool_pixel_height

        return x, y

    @property
    def tool_offset_in_self(self) -> tuple[float, float]:
        """Returns the amount of offset from center of a tool's image rectangle."""
        x_offset, y_offset = [pos - 0.5 for pos in self.tool_center_coords]

        return x_offset, y_offset

    @property
    def tool_offset_in_merge(self) -> tuple[float, float]:
        """Returns the amount of offset from center of a tool when it is first placed on the Merge."""

        x_offset, y_offset = [
            offset * rel_res
            for offset, rel_res in zip(
                self.tool_offset_in_self, self.tool_rel_resolution
            )
        ]

        return x_offset, y_offset

    @property
    def tool_rel_resolution(self) -> tuple[float, float]:

        rel_x = self.tool_pixel_width / self.merge_pixel_width
        rel_y = self.tool_pixel_height / self.merge_pixel_height

        return rel_x, rel_y

    @property
    def tool_data_window(self) -> dict[int, int] | None:
        dw = self.fg_tool.Output.GetValue().DataWindow
        if dw == EMPTY_DATA_WINDOW:
            return None
        if not dw:
            return None
        return dw

    @property
    def merge_current_x(self):
        return self.merge.GetInput("Center")[1]

    @property
    def merge_current_y(self):
        return self.merge.GetInput("Center")[2]

    @property
    def edges_and_centers(self) -> dict[str, float]:
        """Returns normalized edge positions (top, left, bottom, right) for tool in merge"""
        edges_and_centers = {}
        x_offset, y_offset = self.tool_offset_in_merge
        x = x_offset + self.merge_current_x
        y = y_offset + self.merge_current_y

        edges_and_centers["top"] = y + self.tool_rel_height / 2
        edges_and_centers["left"] = x - self.tool_rel_width / 2
        edges_and_centers["bottom"] = y - self.tool_rel_height / 2
        edges_and_centers["right"] = x + self.tool_rel_width / 2

        edges_and_centers["horizontal"] = x
        edges_and_centers["vertical"] = y

        return edges_and_centers


def get_merges(comp: Comp) -> list[Align] | None:
    merges = comp.GetToolList(True, "Merge").values()
    if not merges:
        return None
    merges_and_tools = [Align(merge) for merge in merges]
    return merges_and_tools


# Align edges funcs
def align_left_edges(object: Align, edge: float) -> None:
    x = edge + object.tool_rel_width / 2 - object.tool_offset_in_merge[0]
    y = object.merge_current_y

    object.merge.SetInput("Center", [x, y])


def align_right_edges(object: Align, edge: float) -> None:
    x = edge - object.tool_rel_width / 2 - object.tool_offset_in_merge[0]
    y = object.merge_current_y

    object.merge.SetInput("Center", [x, y])


def align_top_edges(object: Align, edge: float) -> None:
    x = object.merge_current_x
    y = edge - object.tool_rel_height / 2 - object.tool_offset_in_merge[1]

    object.merge.SetInput("Center", [x, y])


def align_bottom_edges(object: Align, edge: float) -> None:
    x = object.merge_current_x
    y = edge + object.tool_rel_height / 2 - object.tool_offset_in_merge[1]

    object.merge.SetInput("Center", [x, y])


# Align centers funcs
def align_horizontal_centers(object: Align, center: float) -> None:
    x = center - object.tool_offset_in_merge[0]
    y = object.merge_current_y

    object.merge.SetInput("Center", [x, y])


def align_vertical_centers(object: Align, center: float) -> None:
    x = object.merge_current_x
    y = center - object.tool_offset_in_merge[1]

    object.merge.SetInput("Center", [x, y])


# Distribute funcs
def distribute_horizontally(align_objects: list[Align]) -> None:
    global comp

    def by_edge(object: Align):
        return object.edges_and_centers["left"]

    align_objects.sort(key=by_edge)

    left_edge = min([obj.edges_and_centers["left"] for obj in align_objects])
    right_edge = max([obj.edges_and_centers["right"] for obj in align_objects])
    canvas_width = right_edge - left_edge

    total_tool_width = sum([obj.tool_rel_width for obj in align_objects])
    gutter = (canvas_width - total_tool_width) / (len(align_objects) - 1)

    comp.Lock()
    for idx, object in enumerate(align_objects):
        if idx == 0 or idx == len(align_objects) - 1:
            edge = object.edges_and_centers["right"] + gutter
            continue
        else:
            align_left_edges(object, edge)
        edge = object.edges_and_centers["right"] + gutter
    comp.Unlock()


def distribute_vertically(align_objects: list[Align]) -> None:
    global comp

    def by_edge(object: Align):
        return object.edges_and_centers["bottom"]

    align_objects.sort(key=by_edge)

    bottom_edge = min([obj.edges_and_centers["bottom"] for obj in align_objects])
    top_edge = max([obj.edges_and_centers["top"] for obj in align_objects])
    canvas_height = top_edge - bottom_edge

    total_tool_height = sum([obj.tool_rel_height for obj in align_objects])
    gutter = (canvas_height - total_tool_height) / (len(align_objects) - 1)

    comp.Lock()
    for idx, object in enumerate(align_objects):
        if idx == 0 or idx == len(align_objects) - 1:
            edge = object.edges_and_centers["top"] + gutter
            continue
        else:
            align_bottom_edges(object, edge)
        edge = object.edges_and_centers["top"] + gutter
    comp.Unlock()


FUALIGN_FUNCS: dict[str, tuple[Callable, Callable]] = {
    "top": (max, align_top_edges),
    "bottom": (min, align_bottom_edges),
    "left": (min, align_left_edges),
    "right": (max, align_right_edges),
    "horizontal": (lambda x: (max(x) - min(x)) / 2 + min(x), align_horizontal_centers),
    "vertical": (lambda x: (max(x) - min(x)) / 2 + min(x), align_vertical_centers),
    "horizontally": distribute_horizontally,
    "vertically": distribute_vertically,
}


# MAIN FUALIGN FUNCTION
def fualign(key: str):
    global comp, FUALIGN_FUNCS

    if key not in FUALIGN_FUNCS:
        return

    align_objects = get_merges(comp)
    if not align_objects:
        return

    if key in ["horizontally", "vertically"]:
        FUALIGN_FUNCS[key](align_objects)
        return

    edges_or_centers = [object.edges_and_centers[key] for object in align_objects]

    edge_func = FUALIGN_FUNCS[key][0]
    edge_or_center = edge_func(edges_or_centers)

    align_func = FUALIGN_FUNCS[key][1]

    comp.Lock()

    for obj in align_objects:
        align_func(obj, edge_or_center)

    comp.Unlock()


# =========================================================================== #
# ########################################################################### #

# =========================================================================== #
# ========================    FRONTEND    =================================== #
# =========================================================================== #
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


# Button style event handlers  ======================================
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

# Dict of keyboard shortcuts
KEYS = dict(
    top="T",
    left="L",
    right="R",
    bottom="B",
    vertical="V",
    horizontal="H",
    vertically="⇧V",
    horizontally="⇧H",
)


def parse_key(key: str) -> list[str]:
    events = []
    if "⇧" in key:
        modifier = "Shift"
        key = key[-1]
        upper_and_lower = False
    else:
        modifier = "Key"
        upper_and_lower = True

    if not upper_and_lower:
        return [f"<{modifier}-{key}>"]
    return [f"<{modifier}-{key}>", f"<{modifier}-{key.lower()}>"]


PARSED_KEYS = {key: parse_key(value) for key, value in KEYS.items()}
print(PARSED_KEYS)


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
        root.attributes("-topmost", True)
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
            el.canvas.bind(
                "<ButtonRelease-1>", lambda e, key=el.name: fualign(key), add="+"
            )

        # Binds root for keyboard shortcuts
        for name, shortcuts in PARSED_KEYS.items():
            for shortcut in shortcuts:
                root.bind(shortcut, lambda e, key=name: fualign(key))

        # Window size and position
        window_width = root.winfo_width()
        window_height = root.winfo_height()

        # get the screen dimension
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # find the center point
        x = int((screen_width / 2 - window_width / 2))
        y = int((screen_height / 2 - window_height / 2))

        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def run(self):
        self.build()

        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
