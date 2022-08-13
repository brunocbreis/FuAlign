from dataclasses import dataclass
import tkinter as tk
from fa_backend import Tool, Comp, Fusion

NEG_MILL = -1_000_000


def initialize_fake_fusion():
    print("Initializing fake Fusion.")
    global fusion, comp
    fusion = Fusion()
    comp = Comp()


try:
    print(fusion)
except NameError:
    initialize_fake_fusion()

# Get tool from merge
def get_tool(merge: Tool):
    return merge.Foreground.GetConnectedOutput().GetTool()


@dataclass
class Align:
    merge: Tool

    def __post_init__(self):
        self.fg_tool = get_tool(self.merge)

    @property
    def pixel_width(self) -> int:
        if not self.data_window:
            return self.fg_tool.GetAttrs("TOOLI_ImageWidth")

        x0, y0, x1, y1 = self.data_window.values()
        return x1 - x0

    @property
    def pixel_height(self) -> int:
        if not self.data_window:
            return self.fg_tool.GetAttrs("TOOLI_ImageHeight")

        x0, y0, x1, y1 = self.data_window.values()
        return y1 - y0

    @property
    def rel_width(self):
        return self.pixel_width * self.merge_size / self.merge_pixel_width

    @property
    def rel_height(self):
        return self.pixel_height * self.merge_size / self.merge_pixel_height

    @property
    def current_position(self) -> tuple[float, float]:
        """Returns current tool position relative to Merge (0.5, 0.5) is the center"""
        if not self.data_window:
            return 0.5, 0.5

        x_px = self.pixel_width / 2
        y_px = self.pixel_height / 2

        x = x_px / self.merge_pixel_width
        y = y_px / self.merge_pixel_height

        return x, y

    @property
    def current_offset(self) -> tuple[float, float]:
        """Returns current node offset in relation to the Merge center point"""
        x_offset, y_offset = [0.5 - pos for pos in self.current_position]
        return x_offset, y_offset

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
    def merge_center_coords(self) -> tuple[int, int]:
        x = self.merge_pixel_width / 2
        y = self.merge_pixel_height / 2

        return int(x), int(y)

    @property
    def tool_center_coords(self) -> tuple[float, float]:
        if self.data_window:
            x0, y0, x1, y1 = self.data_window.values()
        else:
            print(
                f"It looks like {self.fg_tool.GetAttrs('TOOLS_Name')} is off screen. Alignment might not work properly."
            )
            x0, y0 = 0, 0

        x = self.pixel_width / 2 + x0
        y = self.pixel_height / 2 + y0

        # Normalized...
        x = x / self.merge_pixel_width
        y = y / self.merge_pixel_height

        return x, y

    @property
    def data_window(self) -> dict[int, int] | None:
        dw = self.fg_tool.Output.GetValue().DataWindow
        if dw == {1: NEG_MILL, 2: NEG_MILL, 3: NEG_MILL, 4: NEG_MILL}:
            return None
        if not dw:
            return None
        return dw

    @property
    def edges(self) -> dict[str, float]:
        edges = {}
        x, y = self.tool_center_coords
        edges["top"] = y + self.rel_height / 2
        edges["left"] = x - self.rel_width / 2
        edges["bottom"] = y - self.rel_height / 2
        edges["right"] = x + self.rel_width / 2

        return edges


# Align left
def align_left(object: Align, edge: float) -> None:
    x = edge + object.rel_width / 2  # + object.current_offset[0]
    y = object.merge.GetInput("Center")[2]

    object.merge.SetInput("Center", [x, y])


def align_right(object: Align, edge: float) -> None:
    x = edge - object.rel_width / 2  # + object.current_offset[0]
    y = object.merge.GetInput("Center")[2]

    object.merge.SetInput("Center", [x, y])


def align_top(object: Align, edge: float) -> None:
    x = object.merge.GetInput("Center")[1]
    y = edge - object.rel_height / 2  # - object.current_offset[1]

    object.merge.SetInput("Center", [x, y])


def align_bottom(object: Align, edge: float) -> None:
    x = object.merge.GetInput("Center")[1]
    y = edge + object.rel_height / 2  # - object.current_offset[1]

    object.merge.SetInput("Center", [x, y])


# Data Window: {1: x0, 2: y0, 3: x1, 4: y1}
# tool.Output.GetValue().DataWindow

# comp.Merge1.Foreground.GetConnectedOutput().GetTool() -> gets tool connected to merge
# comp.Merge1.Foreground.GetConnectedOutput().GetValue().Height


def align_all(key: str):
    if key not in ["top", "left", "bottom", "right"]:
        print("Please select a correct key.")
        return

    global comp

    selected_merges = comp.GetToolList(True, "Merge").values()

    if not selected_merges:
        print("No selected merges.")
        return

    align_objects = [Align(merge) for merge in selected_merges]

    if key in ["top", "right"]:
        edge = max([object.edges[key] for object in align_objects])

        for obj in align_objects:
            if key == "right":
                align_right(obj, edge)
            else:
                align_top(obj, edge)

    else:
        edge = min([object.edges[key] for object in align_objects])

        for obj in align_objects:
            if key == "left":
                align_left(obj, edge)
            else:
                align_bottom(obj, edge)


class App:
    def run(self):
        root = tk.Tk()
        button = tk.Button(
            root, text="Align left", command=lambda key="left": align_all(key)
        )
        button.pack(padx=30, pady=30)

        button2 = tk.Button(
            root, text="Align right", command=lambda key="right": align_all(key)
        )
        button2.pack(padx=30, pady=30)

        root.attributes("-topmost", True)
        root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
