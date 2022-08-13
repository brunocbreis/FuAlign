from dataclasses import dataclass
import tkinter as tk
from fa_backend import Tool, Comp, Fusion


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
        return self.pixel_width / self.merge_pixel_width

    @property
    def rel_height(self):
        return self.pixel_height / self.merge_pixel_height

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
    def data_window(self) -> dict[int, int] | None:
        return self.fg_tool.Output.GetValue().DataWindow

    @property
    def edges(self) -> dict[str, float]:
        x0, y0, x1, y1 = self.data_window.values()

        edges = {}
        edges["top"] = y1 / self.merge_pixel_height
        edges["left"] = x0 / self.merge_pixel_width
        edges["bottom"] = y0 / self.merge_pixel_height
        edges["right"] = x1 / self.merge_pixel_width

        return edges


# Align left
def align_left(tool: Tool, merge: Tool, edge: float = 0) -> None:
    y = merge.GetInput("Center")[2]
    x = edge + get_rel_width(tool, merge) / 2

    merge.SetInput("Center", [x, y])


def align_right(tool: Tool, merge: Tool, edge: float = 0) -> None:
    y = merge.GetInput("Center")[2]
    x = edge - get_rel_width(tool, merge) / 2

    merge.SetInput("Center", [x, y])


# Data Window: {1: x0, 2: y0, 3: x1, 4: y1}
# tool.Output.GetValue().DataWindow

# comp.Merge1.Foreground.GetConnectedOutput().GetTool() -> gets tool connected to merge
# comp.Merge1.Foreground.GetConnectedOutput().GetValue().Height


def main_left():
    global comp

    selected_merges = comp.GetToolList(True, "Merge").values()

    if not selected_merges:
        print("no Merges have been selected")
        return None

    tools = [get_tool(merge) for merge in selected_merges]

    left_edges = [
        get_left_edge(tool, merge) for tool, merge in zip(tools, selected_merges)
    ]

    leftmost_edge = min(left_edges)

    for tool, merge in zip(tools, selected_merges):
        align_left(tool, merge, leftmost_edge)


def main_right():
    global comp

    selected_merges = comp.GetToolList(True, "Merge").values()

    if not selected_merges:
        print("no Merges have been selected")
        return None

    tools = [get_tool(merge) for merge in selected_merges]

    right_edges = [
        get_right_edge(tool, merge) for tool, merge in zip(tools, selected_merges)
    ]

    rightmost_edge = max(right_edges)

    for tool, merge in zip(tools, selected_merges):
        align_right(tool, merge, rightmost_edge)


class App:
    def run(self):
        root = tk.Tk()
        button = tk.Button(root, text="Align left", command=main_left)
        button.pack(padx=30, pady=30)

        button2 = tk.Button(root, text="Align right", command=main_right)
        button2.pack(padx=30, pady=30)

        root.attributes("-topmost", True)
        root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
