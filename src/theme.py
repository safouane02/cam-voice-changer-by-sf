import tkinter as tk

COLORS = {
    "bg":       "#0a0a12",
    "sidebar":  "#0d0d1a",
    "card":     "#12121e",
    "card2":    "#181828",
    "border":   "#1e1e32",
    "accent":   "#5865f2",
    "accent2":  "#4752c4",
    "green":    "#23a55a",
    "red":      "#ed4245",
    "yellow":   "#fee75c",
    "orange":   "#f0a500",
    "text":     "#dde1f5",
    "muted":    "#4a4a6a",
    "white":    "#ffffff",
    "step_bg":  "#10101e",
}

FONTS = {
    "title":  ("Segoe UI Semibold", 12),
    "body":   ("Segoe UI", 9),
    "small":  ("Segoe UI", 8),
    "mono":   ("Consolas", 9),
    "big":    ("Segoe UI Semibold", 14),
    "huge":   ("Segoe UI Semibold", 22),
    "brand":  ("Segoe UI Semibold", 28),
    "sub":    ("Segoe UI", 11),
}


def lighten(hex_color, delta=20):
    try:
        r = min(int(hex_color[1:3], 16) + delta, 255)
        g = min(int(hex_color[3:5], 16) + delta, 255)
        b = min(int(hex_color[5:7], 16) + delta, 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def make_button(parent, text, cmd, bg=None, fg=None, padx=14, pady=7):
    bg = bg or COLORS["border"]
    fg = fg or COLORS["text"]
    hover_bg = lighten(bg)

    btn = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg, font=FONTS["body"],
        relief="flat", padx=padx, pady=pady,
        cursor="hand2", activebackground=hover_bg,
        activeforeground=fg, bd=0
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def make_card(parent, title=None, bg=None):
    bg = bg or COLORS["card"]
    outer = tk.Frame(parent, bg=bg,
                     highlightbackground=COLORS["border"], highlightthickness=1)
    if title:
        header = tk.Frame(outer, bg=COLORS["card2"])
        header.pack(fill="x")
        tk.Label(header, text=title, font=FONTS["title"],
                 fg=COLORS["text"], bg=COLORS["card2"],
                 padx=14, pady=9).pack(anchor="w")
        tk.Frame(outer, bg=COLORS["border"], height=1).pack(fill="x")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(fill="both", expand=True, padx=14, pady=12)
    return outer, inner


def make_label(parent, text="", font=None, fg=None, bg=None, **kw):
    return tk.Label(
        parent, text=text,
        font=font or FONTS["body"],
        fg=fg or COLORS["text"],
        bg=bg or COLORS["card"],
        **kw
    )


def make_status_dot(parent, color, bg=None):
    bg = bg or COLORS["card"]
    canvas = tk.Canvas(parent, width=10, height=10,
                       bg=bg, highlightthickness=0, bd=0)
    canvas.create_oval(1, 1, 9, 9, fill=color, outline="")
    return canvas
