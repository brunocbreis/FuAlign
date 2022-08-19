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


# Align funcs
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


def align_horizontal_centers(object: Align, center: float) -> None:
    x = object.merge_current_x
    y = center - object.tool_offset_in_merge[1]

    object.merge.SetInput("Center", [x, y])


def align_vertical_centers(object: Align, center: float) -> None:
    x = center - object.tool_offset_in_merge[0]
    y = object.merge_current_y

    object.merge.SetInput("Center", [x, y])


ALIGN_FUNCS: dict[str, tuple[Callable, Callable]] = {
    "top": (max, align_top_edges),
    "bottom": (min, align_bottom_edges),
    "left": (min, align_left_edges),
    "right": (max, align_right_edges),
    "horizontal": (lambda x: (max(x) - min(x)) / 2 + min(x), align_horizontal_centers),
    "vertical": (lambda x: (max(x) - min(x)) / 2 + min(x), align_vertical_centers),
}

# General align
def align_all(key: str):
    global comp, ALIGN_FUNCS

    if key not in ALIGN_FUNCS:
        return

    align_objects = get_merges(comp)
    if not align_objects:
        return

    edges_or_centers = [object.edges_and_centers[key] for object in align_objects]

    edge_func = ALIGN_FUNCS[key][0]
    edge_or_center = edge_func(edges_or_centers)

    align_func = ALIGN_FUNCS[key][1]

    comp.Lock()

    for obj in align_objects:
        align_func(obj, edge_or_center)

    comp.Unlock()


# Distribute funcs
def distribute_horizontally() -> None:
    global comp

    align_objects = get_merges(comp)
    if not align_objects:
        return

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


def distribute_vertically() -> None:
    global comp

    align_objects = get_merges(comp)
    if not align_objects:
        return

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


# UI funcs
def create_buttons(root: tk.Tk, directions: list[str]) -> dict[str, tk.Button]:
    buttons = {}

    for direction in directions:
        button = tk.Button(
            root,
            text=f"Align {direction}",
            command=lambda key=direction: align_all(key),
        )
        buttons[direction] = button
    return buttons


class App:
    def run(self):
        root = tk.Tk()
        root.title("FuAlign")
        root.attributes("-topmost", True)

        horizontal = tk.Frame(root, pady=15)

        buttons = create_buttons(root, ["top", "bottom"])
        buttons["left"], buttons["right"] = create_buttons(
            horizontal, ["left", "right"]
        ).values()

        buttons["top"].pack(padx=30, pady=30)

        horizontal.pack()

        buttons["left"].grid(padx=30, column=1, row=1)
        buttons["right"].grid(padx=30, column=2, row=1)
        buttons["bottom"].pack(padx=30, pady=30)

        center_buttons = create_buttons(root, ["horizontal", "vertical"])
        for button in center_buttons.values():
            button.pack(pady=30)

        distrubute_h_button = tk.Button(
            text="Distribute horizontally", command=distribute_horizontally
        )
        distrubute_h_button.pack(pady=30)

        distrubute_v_button = tk.Button(
            text="Distribute vertically", command=distribute_vertically
        )
        distrubute_v_button.pack(pady=30)

        root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
