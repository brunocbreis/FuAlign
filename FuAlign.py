import tkinter as tk


# Dims with DataWindow
def get_pixel_width(tool) -> int:
    data_window = tool.Output.GetValue().DataWindow
    if not data_window:
        return tool.GetAttrs("TOOLI_ImageWidth")

    x0, y0, x1, y1 = data_window.values()
    return x1 - x0


def get_pixel_height(tool) -> int:
    data_window = tool.Output.GetValue().DataWindow
    if not data_window:
        return tool.GetAttrs("TOOLI_ImageHeight")

    x0, y0, x1, y1 = data_window.values()
    return y1 - y0


# Rel dims
def get_rel_width(tool, merge) -> float:
    size = merge.GetInput("Size")
    rel_width = get_pixel_width(tool) * size / merge.GetAttrs("TOOLI_ImageWidth")
    print(rel_width)
    return rel_width


def get_rel_height(tool, merge) -> float:
    size = merge.GetInput("Size")
    return get_pixel_height(tool) * size / merge.GetAttrs("TOOLI_ImageHeight")


# Edges
def get_top_edge(tool, merge) -> float:
    height = get_rel_height(tool, merge)

    return merge.GetInput("Center")[2] + height / 2


def get_left_edge(tool, merge) -> float:
    width = get_rel_width(tool, merge)

    return merge.GetInput("Center")[1] - width / 2


def get_bottom_edge(tool, merge) -> float:
    height = get_rel_height(tool, merge)

    return merge.GetInput("Center")[2] - height / 2


def get_right_edge(tool, merge) -> float:
    width = get_rel_width(tool, merge)

    return merge.GetInput("Center")[1] + width / 2


# Align left
def align_left(tool, merge, edge: float = 0) -> None:
    y = merge.GetInput("Center")[2]
    x = edge + get_rel_width(tool, merge) / 2

    merge.SetInput("Center", [x, y])


def align_right(tool, merge, edge: float = 0) -> None:
    y = merge.GetInput("Center")[2]
    x = edge - get_rel_width(tool, merge) / 2

    merge.SetInput("Center", [x, y])


# Get tool from merge
def get_tool(merge):
    return merge.Foreground.GetConnectedOutput().GetTool()


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


if __name__ == "__main__":
    root = tk.Tk()
    button = tk.Button(root, text="Align left", command=main_left)
    button.pack(padx=30, pady=30)

    button2 = tk.Button(root, text="Align right", command=main_right)
    button2.pack(padx=30, pady=30)

    root.attributes("-topmost", True)
    root.mainloop()
