import tkinter as tk
from tkinter import ttk


def apply_styles(root):

    style = ttk.Style()

    # Try modern theme
    try:
        style.theme_use("clam")
    except:
        pass

    # Colors
    bg_color = "#1a1625"
    panel_color = "#231f33"
    purple = "#9b5cff"
    purple_hover = "#b084ff"
    text_color = "#ffffff"

    root.configure(bg=bg_color)

    # Frame styling
    style.configure(
        "Main.TFrame",
        background=bg_color
    )

    style.configure(
        "Panel.TFrame",
        background=panel_color
    )

    # Button styling
    style.configure(
        "Purple.TButton",
        background=purple,
        foreground="white",
        borderwidth=0,
        padding=6,
        font=("Segoe UI", 10)
    )

    style.map(
        "Purple.TButton",
        background=[("active", purple_hover)]
    )

    # Entry styling
    style.configure(
        "Purple.TEntry",
        fieldbackground=panel_color,
        foreground=text_color,
        padding=5
    )

    # Progress bar
    style.configure(
        "Purple.Horizontal.TProgressbar",
        troughcolor=panel_color,
        background=purple,
        bordercolor=panel_color
    )

    return {
        "bg": bg_color,
        "panel": panel_color,
        "purple": purple,
        "text": text_color
    }