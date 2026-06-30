import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import time
import uuid

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "phrases.json")
RECENT_MAX = 20

# Clean, minimal palette (single accent, soft neutrals).
COLORS = {
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent_light": "#EFF6FF",
    "bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "border": "#E5E7EB",
    "track": "#EEF0F3",
    "hover": "#F3F4F6",
    "success": "#059669",
    "danger": "#DC2626",
}

FONT = "Segoe UI"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "categories" not in data:
            data["categories"] = ["일반"]
        if "phrases" not in data:
            data["phrases"] = []
        for p in data["phrases"]:
            if "id" not in p:
                p["id"] = str(uuid.uuid4())[:8]
            if "category" not in p:
                p["category"] = "일반"
            if "use_count" not in p:
                p["use_count"] = 0
        if "recent_ids" not in data:
            data["recent_ids"] = []
        return data
    return {
        "categories": ["일반", "진료", "처방", "안내"],
        "phrases": [
            {"id": "sample01", "text": "특이사항 없음", "category": "진료", "use_count": 0},
            {"id": "sample02", "text": "경과 관찰 필요", "category": "진료", "use_count": 0},
            {"id": "sample03", "text": "다음 외래 시 재평가 예정", "category": "진료", "use_count": 0},
            {"id": "sample04", "text": "처방전 발행 완료", "category": "처방", "use_count": 0},
            {"id": "sample05", "text": "다음 방문 시 검사 결과 확인 예정", "category": "안내", "use_count": 0},
        ],
        "recent_ids": [],
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_clipboard(text, widget=None):
    """Copy text to the clipboard. Returns True on success."""
    try:
        import ctypes

        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        h = ctypes.windll.kernel32.GlobalAlloc(0x0042, len(encoded))
        ptr = ctypes.windll.kernel32.GlobalLock(h)
        ctypes.cdll.msvcrt.memcpy(ptr, encoded, len(encoded))
        ctypes.windll.kernel32.GlobalUnlock(h)
        ctypes.windll.user32.SetClipboardData(13, h)
        ctypes.windll.user32.CloseClipboard()
        return True
    except Exception:
        pass
    if widget is not None:
        try:
            widget.clipboard_clear()
            widget.clipboard_append(text)
            widget.update()
            return True
        except Exception:
            pass
    return False


def send_paste():
    """Simulate Ctrl+V into the currently focused window (Windows only)."""
    try:
        import ctypes

        VK_CONTROL, VK_V = 0x11, 0x56
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]
            _fields_ = [("type", ctypes.c_ulong), ("ii", _INPUT)]

        def key_input(vk, flags=0):
            inp = INPUT()
            inp.type = 1
            inp.ii.ki.wVk = vk
            inp.ii.ki.dwFlags = flags
            return inp

        inputs = (INPUT * 4)(
            key_input(VK_CONTROL),
            key_input(VK_V),
            key_input(VK_V, KEYEVENTF_KEYUP),
            key_input(VK_CONTROL, KEYEVENTF_KEYUP),
        )
        ctypes.windll.user32.SendInput(4, ctypes.pointer(inputs[0]), ctypes.sizeof(INPUT))
    except Exception:
        pass


class RoundedButton(tk.Canvas):
    """A flat, rounded-rectangle button drawn on a canvas."""

    def __init__(self, parent, text, command=None, bg_color="#2563EB",
                 hover_color="#1D4ED8", fg="white", width=96, height=34,
                 font_size=10, radius=8, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, **kwargs)
        self._bg = bg_color
        self._hover = hover_color
        self._fg = fg
        self._text = text
        self._cmd = command
        self._cw = width
        self._ch = height
        self._radius = radius
        self._font_size = font_size
        self._draw(bg_color)
        self.bind("<Enter>", lambda e: self._draw(self._hover))
        self.bind("<Leave>", lambda e: self._draw(self._bg))
        self.bind("<Button-1>", lambda e: self._cmd() if self._cmd else None)
        self.configure(cursor="hand2")

    def _round_rect(self, color):
        r = self._radius
        w, h = self._cw, self._ch
        self.create_arc(0, 0, r * 2, r * 2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(w - r * 2, 0, w, r * 2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, h - r * 2, r * 2, h, start=180, extent=90, fill=color, outline=color)
        self.create_arc(w - r * 2, h - r * 2, w, h, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(r, 0, w - r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h - r, fill=color, outline=color)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(color)
        self.create_text(self._cw // 2, self._ch // 2, text=self._text,
                         font=(FONT, self._font_size), fill=self._fg)


class PhraseItem(tk.Frame):
    """A single phrase row: click to copy, double-click to copy+paste."""

    def __init__(self, parent, phrase_data, on_copy, on_paste, on_edit, on_delete, **kwargs):
        super().__init__(parent, bg=COLORS["surface"], cursor="hand2", **kwargs)
        self.phrase = phrase_data
        self._on_copy = on_copy
        self._on_paste = on_paste
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._hovered = False

        self.inner = tk.Frame(self, bg=COLORS["surface"], padx=16, pady=11)
        self.inner.pack(fill="x")

        top = tk.Frame(self.inner, bg=COLORS["surface"])
        top.pack(fill="x")

        self.text_label = tk.Label(
            top, text=phrase_data["text"], font=(FONT, 11),
            bg=COLORS["surface"], fg=COLORS["text"], anchor="w",
            wraplength=250, justify="left"
        )
        self.text_label.pack(side="left", fill="x", expand=True)

        actions = tk.Frame(top, bg=COLORS["surface"])
        actions.pack(side="right")
        self.edit_btn = tk.Label(
            actions, text="✎", font=(FONT, 11), bg=COLORS["surface"],
            fg=COLORS["surface"], cursor="hand2", padx=5
        )
        self.edit_btn.pack(side="left")
        self.edit_btn.bind("<Button-1>", self._edit_click)
        self.del_btn = tk.Label(
            actions, text="🗑", font=(FONT, 10), bg=COLORS["surface"],
            fg=COLORS["surface"], cursor="hand2", padx=2
        )
        self.del_btn.pack(side="left")
        self.del_btn.bind("<Button-1>", self._del_click)

        meta = tk.Label(
            self.inner,
            text=f"{phrase_data.get('category', '일반')}  ·  {phrase_data.get('use_count', 0)}회",
            font=(FONT, 8), bg=COLORS["surface"], fg=COLORS["text_muted"], anchor="w"
        )
        meta.pack(fill="x", pady=(3, 0))
        self.meta = meta

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", side="bottom")

        self._row_widgets = [self, self.inner, top, self.text_label, meta, actions]
        for w in self._row_widgets:
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)
            w.bind("<Button-1>", self._copy_click)
            w.bind("<Double-1>", self._paste_click)

    def _copy_click(self, event):
        self._on_copy(self.phrase)

    def _paste_click(self, event):
        self._on_paste(self.phrase)

    def _edit_click(self, event):
        self._on_edit(self.phrase)
        return "break"

    def _del_click(self, event):
        self._on_delete(self.phrase)
        return "break"

    def _paint(self, bg, show_actions):
        for w in [self, self.inner, self.text_label, self.meta]:
            try:
                w.configure(bg=bg)
            except Exception:
                pass
        for w in self.inner.winfo_children():
            try:
                w.configure(bg=bg)
                for c in w.winfo_children():
                    c.configure(bg=bg)
            except Exception:
                pass
        action_fg = COLORS["text_secondary"] if show_actions else bg
        self.edit_btn.configure(bg=bg, fg=action_fg)
        self.del_btn.configure(bg=bg, fg=action_fg)

    def _hover_in(self, event):
        if not self._hovered:
            self._hovered = True
            self._paint(COLORS["hover"], True)

    def _hover_out(self, event):
        x, y = self.winfo_pointerxy()
        wx, wy = self.winfo_rootx(), self.winfo_rooty()
        if not (wx <= x <= wx + self.winfo_width() and wy <= y <= wy + self.winfo_height()):
            self._hovered = False
            self._paint(COLORS["surface"], False)

    def flash(self):
        self._paint(COLORS["accent_light"], self._hovered)
        self.after(220, lambda: self._paint(
            COLORS["hover"] if self._hovered else COLORS["surface"], self._hovered))


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, bg=COLORS["surface"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg=COLORS["surface"])

        self.scrollable.bind("<Configure>",
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable.bind("<Enter>", self._bind_wheel)
        self.scrollable.bind("<Leave>", self._unbind_wheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _bind_wheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        for w in self.scrollable.winfo_children():
            w.destroy()


class PhrasePanel(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.app = master
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=COLORS["surface"], highlightbackground=COLORS["border"],
                       highlightthickness=1)

        panel_w, panel_h = 400, 560
        btn_x, btn_y = master.winfo_x(), master.winfo_y()
        x = max(8, btn_x - panel_w - 12)
        y = btn_y
        screen_h = self.winfo_screenheight()
        if y + panel_h > screen_h:
            y = max(8, screen_h - panel_h - 20)
        self.geometry(f"{panel_w}x{panel_h}+{x}+{y}")

        self._drag = {"x": 0, "y": 0}
        self.current_tab = "recent" if master.data.get("recent_ids") else "all"
        self.current_category = "전체"
        self._toast_lbl = None

        self._build_header()
        self._build_search()
        self._build_segments()
        self._build_categories()
        self._build_list()
        self._build_footer()
        self._populate()

    # ---- header ----
    def _build_header(self):
        bar = tk.Frame(self, bg=COLORS["surface"], height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.bind("<ButtonPress-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_move)

        title = tk.Label(bar, text="Quick Phrase", font=(FONT, 12, "bold"),
                         bg=COLORS["surface"], fg=COLORS["text"])
        title.pack(side="left", padx=16)
        title.bind("<ButtonPress-1>", self._drag_start)
        title.bind("<B1-Motion>", self._drag_move)

        close = tk.Label(bar, text="✕", font=(FONT, 11), bg=COLORS["surface"],
                         fg=COLORS["text_muted"], cursor="hand2", padx=12)
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: self.destroy())
        close.bind("<Enter>", lambda e: close.configure(fg=COLORS["text"]))
        close.bind("<Leave>", lambda e: close.configure(fg=COLORS["text_muted"]))

        quit_b = tk.Label(bar, text="종료", font=(FONT, 9), bg=COLORS["surface"],
                          fg=COLORS["text_muted"], cursor="hand2", padx=4)
        quit_b.pack(side="right")
        quit_b.bind("<Button-1>", lambda e: self.app._quit_app())
        quit_b.bind("<Enter>", lambda e: quit_b.configure(fg=COLORS["danger"]))
        quit_b.bind("<Leave>", lambda e: quit_b.configure(fg=COLORS["text_muted"]))

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

    def _drag_start(self, event):
        self._drag["x"], self._drag["y"] = event.x, event.y

    def _drag_move(self, event):
        dx, dy = event.x - self._drag["x"], event.y - self._drag["y"]
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    # ---- search ----
    def _build_search(self):
        wrap = tk.Frame(self, bg=COLORS["surface"], padx=16)
        wrap.pack(fill="x", pady=(14, 8))
        box = tk.Frame(wrap, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                       highlightthickness=1)
        box.pack(fill="x")
        tk.Label(box, text="🔍", font=(FONT, 10), bg=COLORS["surface"],
                 fg=COLORS["text_muted"]).pack(side="left", padx=(10, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._populate())
        entry = tk.Entry(box, textvariable=self.search_var, font=(FONT, 11), bd=0,
                         bg=COLORS["surface"], fg=COLORS["text"],
                         insertbackground=COLORS["text"])
        entry.pack(side="left", fill="x", expand=True, ipady=7)
        entry.focus_set()
        entry.bind("<Escape>", lambda e: self.destroy())
        self.search_entry = entry
        clear = tk.Label(box, text="✕", font=(FONT, 9), bg=COLORS["surface"],
                         fg=COLORS["text_muted"], cursor="hand2", padx=8)
        clear.pack(side="right")
        clear.bind("<Button-1>", lambda e: self.search_var.set(""))

    # ---- segmented tabs ----
    def _build_segments(self):
        wrap = tk.Frame(self, bg=COLORS["surface"], padx=16)
        wrap.pack(fill="x")
        track = tk.Frame(wrap, bg=COLORS["track"])
        track.pack(fill="x")
        self.seg_buttons = {}
        for val, label in [("recent", "최근"), ("all", "전체"), ("frequent", "자주 사용")]:
            b = tk.Label(track, text=label, font=(FONT, 9), bg=COLORS["track"],
                         fg=COLORS["text_secondary"], cursor="hand2", pady=6)
            b.pack(side="left", fill="x", expand=True, padx=3, pady=3)
            b.bind("<Button-1>", lambda e, v=val: self._switch_tab(v))
            self.seg_buttons[val] = b
        self._highlight_segment()

    def _switch_tab(self, tab):
        self.current_tab = tab
        self._highlight_segment()
        self._populate()

    def _highlight_segment(self):
        for val, b in self.seg_buttons.items():
            if val == self.current_tab:
                b.configure(bg=COLORS["surface"], fg=COLORS["accent"], font=(FONT, 9, "bold"))
            else:
                b.configure(bg=COLORS["track"], fg=COLORS["text_secondary"], font=(FONT, 9))

    # ---- category chips ----
    def _build_categories(self):
        self.cat_frame = tk.Frame(self, bg=COLORS["surface"], padx=14)
        self.cat_frame.pack(fill="x", pady=(10, 2))
        self._rebuild_categories()

    def _rebuild_categories(self):
        for w in self.cat_frame.winfo_children():
            w.destroy()
        for cat in ["전체"] + self.app.data["categories"]:
            active = cat == self.current_category
            chip = tk.Label(
                self.cat_frame, text=cat, font=(FONT, 8),
                bg=COLORS["accent_light"] if active else COLORS["surface"],
                fg=COLORS["accent"] if active else COLORS["text_secondary"],
                cursor="hand2", padx=8, pady=3,
                highlightbackground=COLORS["accent"] if active else COLORS["border"],
                highlightthickness=1,
            )
            chip.pack(side="left", padx=2)
            chip.bind("<Button-1>", lambda e, c=cat: self._filter_category(c))
        add = tk.Label(self.cat_frame, text="+", font=(FONT, 9, "bold"),
                       bg=COLORS["surface"], fg=COLORS["text_muted"], cursor="hand2",
                       padx=7, pady=2, highlightbackground=COLORS["border"],
                       highlightthickness=1)
        add.pack(side="left", padx=2)
        add.bind("<Button-1>", lambda e: self._add_category())

    def _filter_category(self, cat):
        self.current_category = cat
        self._rebuild_categories()
        self._populate()

    # ---- list ----
    def _build_list(self):
        self.scroll = ScrollableFrame(self, bg=COLORS["surface"])
        self.scroll.pack(fill="both", expand=True, padx=0, pady=(6, 0))
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

    # ---- footer ----
    def _build_footer(self):
        bar = tk.Frame(self, bg=COLORS["surface"], padx=16)
        bar.pack(fill="x", pady=10)
        RoundedButton(bar, text="+ 새 문장 추가", command=self._add_phrase,
                      bg_color=COLORS["accent"], hover_color=COLORS["accent_dark"],
                      width=118, height=34, font_size=10).pack(side="left")

        more = tk.Label(bar, text="⋯", font=(FONT, 14, "bold"), bg=COLORS["surface"],
                        fg=COLORS["text_secondary"], cursor="hand2", padx=8)
        more.pack(side="right")
        more.bind("<Button-1>", self._show_more_menu)

        self.count_label = tk.Label(bar, text="", font=(FONT, 8),
                                    bg=COLORS["surface"], fg=COLORS["text_muted"])
        self.count_label.pack(side="right", padx=6)

        self.more_menu = tk.Menu(self, tearoff=0)
        self.more_menu.add_command(label="가져오기 / 내보내기", command=self._import_export)

    def _show_more_menu(self, event):
        try:
            self.more_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.more_menu.grab_release()

    # ---- data / list population ----
    def _get_filtered(self):
        query = self.search_var.get().strip().lower()
        phrases = self.app.data["phrases"]
        if self.current_tab == "recent":
            id_map = {p["id"]: p for p in phrases}
            phrases = [id_map[i] for i in self.app.data["recent_ids"] if i in id_map]
        elif self.current_tab == "frequent":
            phrases = sorted(phrases, key=lambda p: p.get("use_count", 0), reverse=True)
        if self.current_category != "전체":
            phrases = [p for p in phrases if p.get("category") == self.current_category]
        if query:
            phrases = [p for p in phrases if query in p["text"].lower()]
        return phrases

    def _populate(self):
        self.scroll.clear()
        phrases = self._get_filtered()
        self.count_label.configure(text=f"{len(phrases)}개")
        if not phrases:
            msg = ("문장이 없습니다.\n아래 ‘＋ 새 문장 추가’로 시작하세요."
                   if not self.app.data["phrases"] else "검색 결과가 없습니다.")
            tk.Label(self.scroll.scrollable, text=msg, font=(FONT, 10),
                     bg=COLORS["surface"], fg=COLORS["text_muted"], pady=48).pack(fill="x")
            return
        for p in phrases:
            PhraseItem(self.scroll.scrollable, p,
                       on_copy=self._copy_phrase, on_paste=self._paste_phrase,
                       on_edit=self._edit_phrase, on_delete=self._delete_phrase).pack(fill="x")

    # ---- actions ----
    def _record_use(self, phrase):
        pid = phrase["id"]
        for p in self.app.data["phrases"]:
            if p["id"] == pid:
                p["use_count"] = p.get("use_count", 0) + 1
                break
        recent = self.app.data["recent_ids"]
        if pid in recent:
            recent.remove(pid)
        recent.insert(0, pid)
        self.app.data["recent_ids"] = recent[:RECENT_MAX]
        save_data(self.app.data)

    def _find_item(self, phrase):
        for w in self.scroll.scrollable.winfo_children():
            if isinstance(w, PhraseItem) and w.phrase.get("id") == phrase.get("id"):
                return w
        return None

    def _copy_phrase(self, phrase):
        self._record_use(phrase)
        set_clipboard(phrase["text"], self)
        item = self._find_item(phrase)
        if item:
            item.flash()
        self._toast("복사됨  ·  Ctrl+V로 붙여넣기")

    def _paste_phrase(self, phrase):
        self._record_use(phrase)
        set_clipboard(phrase["text"], self)
        self.destroy()
        self.app.panel = None
        self.app.withdraw()
        self.app.after(160, self._do_paste)

    def _do_paste(self):
        send_paste()
        self.app.after(100, self.app.deiconify)

    def _toast(self, msg):
        if self._toast_lbl is not None and self._toast_lbl.winfo_exists():
            self._toast_lbl.destroy()
        self._toast_lbl = tk.Label(self, text=msg, font=(FONT, 9, "bold"),
                                   bg=COLORS["text"], fg="white", padx=14, pady=6)
        self._toast_lbl.place(relx=0.5, rely=0.93, anchor="center")
        self.after(1200, self._hide_toast)

    def _hide_toast(self):
        if self._toast_lbl is not None and self._toast_lbl.winfo_exists():
            self._toast_lbl.destroy()
            self._toast_lbl = None

    def _add_phrase(self):
        self._open_editor(None)

    def _edit_phrase(self, phrase):
        self._open_editor(phrase)

    def _open_editor(self, phrase):
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=COLORS["surface"], highlightbackground=COLORS["border"],
                      highlightthickness=1)
        w, h = 420, 300
        win.geometry(f"{w}x{h}+{self.winfo_x() + 20}+{self.winfo_y() + 70}")

        head = tk.Frame(win, bg=COLORS["surface"], height=44)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text="문장 편집" if phrase else "새 문장 추가",
                 font=(FONT, 12, "bold"), bg=COLORS["surface"],
                 fg=COLORS["text"]).pack(side="left", padx=16)
        tk.Frame(win, bg=COLORS["border"], height=1).pack(fill="x")

        body = tk.Frame(win, bg=COLORS["surface"], padx=16, pady=14)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="문장", font=(FONT, 9), bg=COLORS["surface"],
                 fg=COLORS["text_secondary"]).pack(anchor="w")
        tbox_wrap = tk.Frame(body, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                             highlightthickness=1)
        tbox_wrap.pack(fill="x", pady=(4, 12))
        tbox = tk.Text(tbox_wrap, font=(FONT, 11), height=4, bd=0, wrap="word",
                       bg=COLORS["surface"], fg=COLORS["text"], padx=8, pady=6)
        tbox.pack(fill="x")
        if phrase:
            tbox.insert("1.0", phrase["text"])

        tk.Label(body, text="카테고리", font=(FONT, 9), bg=COLORS["surface"],
                 fg=COLORS["text_secondary"]).pack(anchor="w")
        cat_var = tk.StringVar(value=phrase["category"] if phrase else "일반")
        ttk.Combobox(body, textvariable=cat_var, values=self.app.data["categories"],
                     font=(FONT, 10)).pack(fill="x", pady=(4, 14))

        btns = tk.Frame(body, bg=COLORS["surface"])
        btns.pack(fill="x")

        def save():
            txt = tbox.get("1.0", "end").strip()
            cat = cat_var.get().strip() or "일반"
            if not txt:
                return
            if cat not in self.app.data["categories"]:
                self.app.data["categories"].append(cat)
            if phrase:
                for p in self.app.data["phrases"]:
                    if p["id"] == phrase["id"]:
                        p["text"], p["category"] = txt, cat
                        break
            else:
                self.app.data["phrases"].append(
                    {"id": str(uuid.uuid4())[:8], "text": txt, "category": cat, "use_count": 0})
            save_data(self.app.data)
            win.destroy()
            self._rebuild_categories()
            self._populate()

        RoundedButton(btns, text="저장", command=save, bg_color=COLORS["accent"],
                      hover_color=COLORS["accent_dark"], width=84, height=32).pack(side="right")
        RoundedButton(btns, text="취소", command=win.destroy, bg_color=COLORS["hover"],
                      hover_color=COLORS["border"], fg=COLORS["text"],
                      width=84, height=32).pack(side="right", padx=(0, 8))
        tbox.focus_set()

    def _delete_phrase(self, phrase):
        if messagebox.askyesno("삭제", f"삭제하시겠습니까?\n\n“{phrase['text'][:60]}”", parent=self):
            self.app.data["phrases"] = [p for p in self.app.data["phrases"]
                                        if p["id"] != phrase["id"]]
            if phrase["id"] in self.app.data["recent_ids"]:
                self.app.data["recent_ids"].remove(phrase["id"])
            save_data(self.app.data)
            self._populate()

    def _add_category(self):
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=COLORS["surface"], highlightbackground=COLORS["border"],
                      highlightthickness=1)
        win.geometry(f"300x150+{self.winfo_x() + 40}+{self.winfo_y() + 90}")
        tk.Label(win, text="새 카테고리", font=(FONT, 11, "bold"), bg=COLORS["surface"],
                 fg=COLORS["text"]).pack(anchor="w", padx=16, pady=(16, 8))
        var = tk.StringVar()
        wrap = tk.Frame(win, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                        highlightthickness=1)
        wrap.pack(fill="x", padx=16)
        entry = tk.Entry(wrap, textvariable=var, font=(FONT, 11), bd=0,
                         bg=COLORS["surface"], fg=COLORS["text"])
        entry.pack(fill="x", ipady=6, padx=6)
        entry.focus_set()

        def add():
            name = var.get().strip()
            if name and name not in self.app.data["categories"]:
                self.app.data["categories"].append(name)
                save_data(self.app.data)
                self._rebuild_categories()
                win.destroy()

        entry.bind("<Return>", lambda e: add())
        row = tk.Frame(win, bg=COLORS["surface"])
        row.pack(fill="x", padx=16, pady=14)
        RoundedButton(row, text="추가", command=add, bg_color=COLORS["accent"],
                      hover_color=COLORS["accent_dark"], width=70, height=30).pack(side="right")
        RoundedButton(row, text="취소", command=win.destroy, bg_color=COLORS["hover"],
                      hover_color=COLORS["border"], fg=COLORS["text"],
                      width=70, height=30).pack(side="right", padx=(0, 8))

    def _import_export(self):
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=COLORS["surface"], highlightbackground=COLORS["border"],
                      highlightthickness=1)
        win.geometry(f"420x380+{self.winfo_x() + 20}+{self.winfo_y() + 50}")

        tk.Label(win, text="가져오기 / 내보내기", font=(FONT, 12, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Frame(win, bg=COLORS["border"], height=1).pack(fill="x")

        body = tk.Frame(win, bg=COLORS["surface"], padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="내보내기 — 아래 내용을 복사해 보관하세요", font=(FONT, 9),
                 bg=COLORS["surface"], fg=COLORS["text_secondary"]).pack(anchor="w")
        exp = tk.Text(body, font=(FONT, 9), height=5, bd=0, wrap="word",
                      bg=COLORS["bg"], fg=COLORS["text"], padx=8, pady=6)
        exp.pack(fill="x", pady=(4, 12))
        exp.insert("1.0", json.dumps(self.app.data, ensure_ascii=False, indent=2))
        exp.configure(state="disabled")

        tk.Label(body, text="가져오기 — JSON을 붙여넣고 실행", font=(FONT, 9),
                 bg=COLORS["surface"], fg=COLORS["text_secondary"]).pack(anchor="w")
        imp = tk.Text(body, font=(FONT, 9), height=5, bd=0, wrap="word",
                      bg=COLORS["bg"], fg=COLORS["text"], padx=8, pady=6)
        imp.pack(fill="x", pady=(4, 10))

        def do_import():
            try:
                new = json.loads(imp.get("1.0", "end").strip())
            except json.JSONDecodeError:
                messagebox.showerror("오류", "올바른 JSON이 아닙니다.", parent=win)
                return
            existing = {p["text"] for p in self.app.data["phrases"]}
            added = 0
            for p in new.get("phrases", []):
                p.setdefault("id", str(uuid.uuid4())[:8])
                p.setdefault("category", "일반")
                p.setdefault("use_count", 0)
                if p["text"] not in existing:
                    self.app.data["phrases"].append(p)
                    existing.add(p["text"])
                    added += 1
            for c in new.get("categories", []):
                if c not in self.app.data["categories"]:
                    self.app.data["categories"].append(c)
            save_data(self.app.data)
            self._rebuild_categories()
            self._populate()
            messagebox.showinfo("완료", f"{added}개 문장을 가져왔습니다.", parent=win)
            win.destroy()

        row = tk.Frame(body, bg=COLORS["surface"])
        row.pack(fill="x")
        RoundedButton(row, text="가져오기 실행", command=do_import, bg_color=COLORS["accent"],
                      hover_color=COLORS["accent_dark"], width=110, height=32).pack(side="left")
        RoundedButton(row, text="닫기", command=win.destroy, bg_color=COLORS["hover"],
                      hover_color=COLORS["border"], fg=COLORS["text"],
                      width=70, height=32).pack(side="right")


class FloatingButton(tk.Tk):
    def __init__(self):
        super().__init__()
        self.data = load_data()
        self.panel = None

        self.title("Quick Phrase")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._quit_app)

        self.size = 52
        screen_w = self.winfo_screenwidth()
        self.geometry(f"{self.size}x{self.size}+{screen_w - self.size - 18}+18")

        self.canvas = tk.Canvas(self, width=self.size, height=self.size,
                                highlightthickness=0, bg=COLORS["bg"], cursor="hand2")
        self.canvas.pack()
        self._draw(COLORS["accent"])

        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Button-3>", self._show_menu)
        self.canvas.bind("<Enter>", lambda e: self._draw(COLORS["accent_dark"]))
        self.canvas.bind("<Leave>", lambda e: self._draw(COLORS["accent"]))

        self._dd = {"x": 0, "y": 0, "moved": False}

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="열기 / 닫기", command=self._toggle_panel)
        self.menu.add_separator()
        self.menu.add_command(label="종료", command=self._quit_app)

        self.after(10, self._set_appwindow)

    def _draw(self, color):
        s = self.size
        self.canvas.delete("all")
        self.canvas.create_oval(4, 4, s - 4, s - 4, fill=color, outline="")
        self.canvas.create_text(s // 2, s // 2, text="Q", font=(FONT, 22, "bold"), fill="white")

    def _set_appwindow(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes

            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            ctypes.windll.user32.SetWindowTextW(hwnd, "Quick Phrase")
            self.withdraw()
            self.after(20, self._reshow)
        except Exception:
            pass

    def _reshow(self):
        self.deiconify()
        self.attributes("-topmost", True)

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _toggle_panel(self):
        if self.panel and self.panel.winfo_exists():
            self.panel.destroy()
            self.panel = None
        else:
            self.panel = PhrasePanel(self)

    def _quit_app(self):
        if self.panel and self.panel.winfo_exists():
            self.panel.destroy()
            self.panel = None
        if messagebox.askyesno("종료", "Quick Phrase를 종료하시겠습니까?", parent=self):
            self.destroy()

    def _press(self, event):
        self._dd["x"], self._dd["y"], self._dd["moved"] = event.x, event.y, False

    def _drag(self, event):
        dx, dy = event.x - self._dd["x"], event.y - self._dd["y"]
        if abs(dx) > 3 or abs(dy) > 3:
            self._dd["moved"] = True
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    def _release(self, event):
        if not self._dd["moved"]:
            self._toggle_panel()


if __name__ == "__main__":
    app = FloatingButton()
    app.mainloop()
