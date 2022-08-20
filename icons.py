import tkinter as tk
from idlelib.tooltip import Hovertip


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


root = tk.Tk()
root.config(background=Color.CANVAS_BG)
root.title("")

label_frame = tk.Frame(root, background=Color.CANVAS_BG)
label_frame.pack(pady=10)

action = tk.StringVar(value="FuAlign")
modifier = tk.StringVar()


def make_rect(
    canvas: tk.Canvas, width: float, height: float, x: float, y: float, **configs
) -> int:

    multiplier = canvas.winfo_width()

    x0 = x * multiplier
    x1 = (x + width) * multiplier
    y0 = y * multiplier
    y1 = (y + height) * multiplier

    return canvas.create_rectangle(x0, y0, x1, y1, **configs)


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


icon_dims = {
    "left edges": [
        (0.1, 1, 0.05, 0),  # line
        (0.7, 0.3, 0.25, 0.15),  # rect1
        (0.5, 0.3, 0.25, 0.55),  # rect 2
    ],
    "horizontal centers": [
        (0.1, 1, 0.45, 0),  # line
        (0.5, 0.3, 0.25, 0.15),  # rect1
        (0.7, 0.3, 0.15, 0.55),  # rect2
    ],
    "right edges": [
        (0.1, 1, 0.85, 0),  # line
        (0.7, 0.3, 0.05, 0.15),  # rect1
        (0.5, 0.3, 0.25, 0.55),  # rect2
    ],
    "vertically": [
        (1, 0.1, 0, 0.1),  # line1
        (0.6, 0.3, 0.2, 0.35),  # rect1
        (1, 0.1, 0, 0.8),  # line2
    ],
    "top edges": [
        (1, 0.1, 0, 0.05),  # line
        (0.3, 0.7, 0.15, 0.25),  # rect1
        (0.3, 0.5, 0.55, 0.25),  # rect 2
    ],
    "vertical centers": [
        (1, 0.1, 0, 0.45),  # line
        (0.3, 0.5, 0.15, 0.25),  # rect1
        (0.3, 0.7, 0.55, 0.15),  # rect2
    ],
    "bottom edges": [
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


def make_canvases(
    root: tk.Widget, dims: dict[str, list[tuple]], size: int
) -> dict[str, tk.Canvas]:
    canvases: dict[str, tk.Canvas] = {}

    for key in dims:
        canvas = tk.Canvas(
            root,
            width=size,
            height=size,
            background=Color.CANVAS_BG,
            highlightthickness=0,
            relief="ridge",
            bd=0,
        )

        canvases[key] = canvas

    return canvases


def grid_canvases(canvases: dict[str, tk.Canvas]):
    for idx, canvas in enumerate(canvases.values()):
        canvas.grid(row=1, column=idx + 1, padx=10)


def draw_icons(
    canvases: dict[str, tk.Canvas], dims: dict[str, list[tuple]], **config
) -> dict[str, int]:

    for canvas in canvases.values():
        canvas.update()

    for key in dims:
        for dim in dims[key]:
            make_rect(canvases[key], *dim, **config)
        set_hover_style(canvases[key])


TOP_FRAME = tk.Frame()
TOP_FRAME_ICONS = ["left edges", "horizontal centers", "right edges", "vertically"]

BTM_FRAME = tk.Frame()
BTM_FRAME_ICONS = [
    "top edges",
    "vertical centers",
    "bottom edges",
    "horizontally",
]

frame1 = make_canvases(
    TOP_FRAME,
    {key: value for key, value in icon_dims.items() if key in TOP_FRAME_ICONS},
    20,
)

frame2 = make_canvases(
    BTM_FRAME,
    {key: value for key, value in icon_dims.items() if key in BTM_FRAME_ICONS},
    20,
)

grid_canvases(frame1)
grid_canvases(frame2)

canvases = {**frame1, **frame2}


for frame in [TOP_FRAME, BTM_FRAME]:
    frame.pack()
    frame.configure(pady=20, padx=20, background=Color.CANVAS_BG)
    for idx in range(1, 5):
        frame.columnconfigure(index=idx)


draw_icons(canvases, icon_dims, fill=Color.NORMAL, outline=Color.CANVAS_BG, tag="icon")

for key, canvas in canvases.items():
    canvas.bind("<ButtonRelease-1>", lambda e, key=key: print(key), add="+")

# Labels
action_label = tk.Label(
    label_frame,
    textvariable=action,
    justify="left",
    background=Color.CANVAS_BG,
    foreground=Color.TEXT,
    font=Font.TOOLTIP_BOLD,
)
modifier_label = tk.Label(
    label_frame,
    textvariable=modifier,
    justify="left",
    background=Color.CANVAS_BG,
    foreground=Color.TEXT,
    font=Font.TOOLTIP,
)

action_label.grid(sticky=tk.E, row=1, column=1)
modifier_label.grid(sticky=tk.E, row=1, column=2)


def describe(action_text: str, modifier_text: str):
    action.set(action_text.upper())
    modifier.set(modifier_text)


def clear():
    action.set("FuAlign")
    modifier.set("")


for key, canvas in canvases.items():
    a = "align"
    if key in ["horizontally", "vertically"]:
        a = "distribute"
    canvas.bind("<Enter>", lambda e, a=a, m=key: describe(a, m), add="+")
    canvas.bind("<Leave>", lambda e: clear(), add="+")


root.mainloop()
