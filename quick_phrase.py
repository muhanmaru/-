import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import time
import uuid

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "phrases.json")
RECENT_MAX = 20

COLORS = {
    "primary": "#1565C0",
    "primary_light": "#1976D2",
    "primary_dark": "#0D47A1",
    "accent": "#2196F3",
    "success": "#43A047",
    "success_hover": "#388E3C",
    "danger": "#E53935",
    "danger_hover": "#C62828",
    "warning": "#FB8C00",
    "bg": "#F5F5F5",
    "surface": "#FFFFFF",
    "text": "#212121",
    "text_secondary": "#757575",
    "border": "#E0E0E0",
    "hover": "#E3F2FD",
    "selected": "#BBDEFB",
    "divider": "#EEEEEE",
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


def do_clipboard_paste(text):
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
    def __init__(self, parent, text, command=None, bg_color="#2196F3",
                 hover_color="#1976D2", fg="white", width=80, height=32,
                 font_size=9, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, **kwargs)
        self._bg = bg_color
        self._hover = hover_color
        self._fg = fg
        self._text = text
        self._cmd = command
        self._cw = width
        self._ch = height
        self._font_size = font_size
        self._draw(bg_color)
        self.bind("<Enter>", lambda e: self._draw(hover_color))
        self.bind("<Leave>", lambda e: self._draw(bg_color))
        self.bind("<Button-1>", lambda e: self._cmd() if self._cmd else None)
        self.configure(cursor="hand2")

    def _draw(self, color):
        self.delete("all")
        r = 6
        w, h = self._cw, self._ch
        self.create_arc(0, 0, r * 2, r * 2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(w - r * 2, 0, w, r * 2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, h - r * 2, r * 2, h, start=180, extent=90, fill=color, outline=color)
        self.create_arc(w - r * 2, h - r * 2, w, h, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(r, 0, w - r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h - r, fill=color, outline=color)
        self.create_text(w // 2, h // 2, text=self._text,
                         font=(FONT, self._font_size), fill=self._fg)

    def set_text(self, text):
        self._text = text
        self._draw(self._bg)


class PhraseItem(tk.Frame):
    def __init__(self, parent, phrase_data, on_use, on_edit, on_delete, **kwargs):
        super().__init__(parent, bg=COLORS["surface"], cursor="hand2", **kwargs)
        self.phrase = phrase_data
        self._on_use = on_use
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._is_hovered = False

        self.configure(highlightthickness=0)

        self.inner = tk.Frame(self, bg=COLORS["surface"], padx=12, pady=8)
        self.inner.pack(fill="x", expand=True)

        top = tk.Frame(self.inner, bg=COLORS["surface"])
        top.pack(fill="x")

        self.text_label = tk.Label(
            top, text=phrase_data["text"], font=(FONT, 11),
            bg=COLORS["surface"], fg=COLORS["text"], anchor="w",
            wraplength=280, justify="left"
        )
        self.text_label.pack(side="left", fill="x", expand=True)

        btn_frame = tk.Frame(top, bg=COLORS["surface"])
        btn_frame.pack(side="right")

        self.edit_btn = tk.Label(
            btn_frame, text="✏", font=(FONT, 10), bg=COLORS["surface"],
            fg=COLORS["text_secondary"], cursor="hand2", padx=4
        )
        self.edit_btn.pack(side="left")
        self.edit_btn.bind("<Button-1>", lambda e: self._on_edit(self.phrase))

        self.del_btn = tk.Label(
            btn_frame, text="🗑", font=(FONT, 10), bg=COLORS["surface"],
            fg=COLORS["text_secondary"], cursor="hand2", padx=4
        )
        self.del_btn.pack(side="left")
        self.del_btn.bind("<Button-1>", lambda e: self._on_delete(self.phrase))

        meta = tk.Frame(self.inner, bg=COLORS["surface"])
        meta.pack(fill="x", pady=(2, 0))
        cat_text = phrase_data.get("category", "일반")
        tk.Label(
            meta, text=cat_text, font=(FONT, 8),
            bg="#E3F2FD", fg=COLORS["primary"], padx=6, pady=1
        ).pack(side="left")
        tk.Label(
            meta, text=f"사용 {phrase_data.get('use_count', 0)}회",
            font=(FONT, 8), bg=COLORS["surface"], fg=COLORS["text_secondary"]
        ).pack(side="right")

        sep = tk.Frame(self, bg=COLORS["divider"], height=1)
        sep.pack(fill="x", side="bottom")

        for w in [self, self.inner, top, self.text_label, meta]:
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)
            w.bind("<Double-1>", lambda e: self._on_use(self.phrase))

    def _set_bg(self, color):
        for w in [self, self.inner, self.text_label, self.edit_btn, self.del_btn]:
            try:
                w.configure(bg=color)
            except Exception:
                pass
        for w in self.inner.winfo_children():
            try:
                w.configure(bg=color)
                for c in w.winfo_children():
                    try:
                        if not isinstance(c, tk.Label) or c.cget("bg") != "#E3F2FD":
                            c.configure(bg=color)
                    except Exception:
                        pass
            except Exception:
                pass

    def _hover_in(self, event):
        if not self._is_hovered:
            self._is_hovered = True
            self._set_bg(COLORS["hover"])

    def _hover_out(self, event):
        x, y = self.winfo_pointerxy()
        wx = self.winfo_rootx()
        wy = self.winfo_rooty()
        ww = self.winfo_width()
        wh = self.winfo_height()
        if not (wx <= x <= wx + ww and wy <= y <= wy + wh):
            self._is_hovered = False
            self._set_bg(COLORS["surface"])


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

        self.scrollable.bind("<Enter>", self._bind_mousewheel)
        self.scrollable.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
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
        self.configure(bg=COLORS["bg"])

        panel_w, panel_h = 440, 580
        btn_x = master.winfo_x()
        btn_y = master.winfo_y()
        x = max(0, btn_x - panel_w - 12)
        y = btn_y

        screen_h = self.winfo_screenheight()
        if y + panel_h > screen_h:
            y = max(0, screen_h - panel_h - 20)

        self.geometry(f"{panel_w}x{panel_h}+{x}+{y}")

        self._drag_data = {"x": 0, "y": 0}
        self.current_tab = "recent" if master.data.get("recent_ids") else "all"
        self.current_category = "전체"

        self._build_titlebar()
        self._build_search()
        self._build_tabs()
        self._build_category_filter()
        self._build_list()
        self._build_bottom_bar()
        self._populate()

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=COLORS["primary_dark"], height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.bind("<ButtonPress-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_move)

        tk.Label(
            bar, text="  Quick Phrase", font=(FONT, 13, "bold"),
            bg=COLORS["primary_dark"], fg="white"
        ).pack(side="left", padx=(8, 0))

        close_btn = tk.Label(
            bar, text="  ✕  ", font=(FONT, 12), bg=COLORS["primary_dark"],
            fg="#BBDEFB", cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg="white", bg=COLORS["danger"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg="#BBDEFB", bg=COLORS["primary_dark"]))

        quit_btn = tk.Label(
            bar, text=" 종료 ", font=(FONT, 9), bg=COLORS["primary_dark"],
            fg="#BBDEFB", cursor="hand2"
        )
        quit_btn.pack(side="right", padx=(0, 2))
        quit_btn.bind("<Button-1>", lambda e: self.app._quit_app())
        quit_btn.bind("<Enter>", lambda e: quit_btn.configure(fg="white", bg=COLORS["danger"]))
        quit_btn.bind("<Leave>", lambda e: quit_btn.configure(fg="#BBDEFB", bg=COLORS["primary_dark"]))

    def _drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _drag_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    def _build_search(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=14)
        frame.pack(fill="x", pady=(10, 6))

        search_border = tk.Frame(frame, bg=COLORS["border"], padx=1, pady=1)
        search_border.pack(fill="x")
        search_inner = tk.Frame(search_border, bg=COLORS["surface"])
        search_inner.pack(fill="x")

        tk.Label(
            search_inner, text=" 🔍 ", font=(FONT, 11),
            bg=COLORS["surface"], fg=COLORS["text_secondary"]
        ).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._populate())
        self.search_entry = tk.Entry(
            search_inner, textvariable=self.search_var,
            font=(FONT, 11), bd=0, bg=COLORS["surface"], fg=COLORS["text"],
            insertbackground=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.search_entry.focus_set()
        self.search_entry.bind("<Escape>", lambda e: self.destroy())

        clear_btn = tk.Label(
            search_inner, text=" ✕ ", font=(FONT, 9),
            bg=COLORS["surface"], fg=COLORS["text_secondary"], cursor="hand2"
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda e: self.search_var.set(""))

    def _build_tabs(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=14)
        frame.pack(fill="x", pady=(0, 4))

        self.tab_buttons = {}
        for val, label in [("recent", "최근 사용"), ("all", "전체"), ("frequent", "자주 사용")]:
            btn = tk.Label(
                frame, text=f" {label} ", font=(FONT, 9),
                bg=COLORS["bg"], fg=COLORS["text_secondary"],
                cursor="hand2", padx=8, pady=4
            )
            btn.pack(side="left", padx=(0, 2))
            btn.bind("<Button-1>", lambda e, v=val: self._switch_tab(v))
            self.tab_buttons[val] = btn

        self._highlight_tab(self.current_tab)

    def _switch_tab(self, tab):
        self.current_tab = tab
        self._highlight_tab(tab)
        self._populate()

    def _highlight_tab(self, active):
        for val, btn in self.tab_buttons.items():
            if val == active:
                btn.configure(bg=COLORS["primary"], fg="white")
            else:
                btn.configure(bg=COLORS["bg"], fg=COLORS["text_secondary"])

    def _build_category_filter(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=14)
        frame.pack(fill="x", pady=(0, 4))

        self.cat_frame = frame
        self._rebuild_category_chips()

    def _rebuild_category_chips(self):
        for w in self.cat_frame.winfo_children():
            w.destroy()

        cats = ["전체"] + self.app.data["categories"]
        for cat in cats:
            fg = "white" if cat == self.current_category else COLORS["text_secondary"]
            bg = COLORS["accent"] if cat == self.current_category else COLORS["divider"]
            lbl = tk.Label(
                self.cat_frame, text=f" {cat} ", font=(FONT, 8),
                bg=bg, fg=fg, cursor="hand2", padx=4, pady=2
            )
            lbl.pack(side="left", padx=(0, 3))
            lbl.bind("<Button-1>", lambda e, c=cat: self._filter_category(c))

        add_cat = tk.Label(
            self.cat_frame, text=" + ", font=(FONT, 8, "bold"),
            bg=COLORS["divider"], fg=COLORS["text_secondary"],
            cursor="hand2", padx=4, pady=2
        )
        add_cat.pack(side="left", padx=(4, 0))
        add_cat.bind("<Button-1>", lambda e: self._add_category())

    def _filter_category(self, cat):
        self.current_category = cat
        self._rebuild_category_chips()
        self._populate()

    def _build_list(self):
        self.scroll_frame = ScrollableFrame(self, bg=COLORS["surface"])
        self.scroll_frame.pack(fill="both", expand=True, padx=14, pady=(0, 6))

    def _build_bottom_bar(self):
        bar = tk.Frame(self, bg=COLORS["bg"], padx=14)
        bar.pack(fill="x", pady=(0, 10))

        RoundedButton(
            bar, text="+ 새 문장 추가", command=self._add_phrase,
            bg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            width=120, height=34, font_size=10
        ).pack(side="left")

        RoundedButton(
            bar, text="가져오기/내보내기", command=self._import_export,
            bg_color=COLORS["primary_light"], hover_color=COLORS["primary_dark"],
            width=120, height=34, font_size=9
        ).pack(side="right")

        self.count_label = tk.Label(
            bar, text="", font=(FONT, 8), bg=COLORS["bg"], fg=COLORS["text_secondary"]
        )
        self.count_label.pack(side="right", padx=8)

    def _get_filtered_phrases(self):
        query = self.search_var.get().strip().lower()
        phrases = self.app.data["phrases"]

        if self.current_tab == "recent":
            id_order = self.app.data["recent_ids"]
            id_map = {p["id"]: p for p in phrases}
            phrases = [id_map[pid] for pid in id_order if pid in id_map]
        elif self.current_tab == "frequent":
            phrases = sorted(phrases, key=lambda p: p.get("use_count", 0), reverse=True)

        if self.current_category != "전체":
            phrases = [p for p in phrases if p.get("category") == self.current_category]

        if query:
            phrases = [p for p in phrases if query in p["text"].lower()]

        return phrases

    def _populate(self):
        self.scroll_frame.clear()
        phrases = self._get_filtered_phrases()
        self.count_label.configure(text=f"{len(phrases)}개 항목")

        if not phrases:
            msg = "저장된 문장이 없습니다.\n아래 '+ 새 문장 추가' 버튼으로 추가하세요." \
                if not self.app.data["phrases"] else "검색 결과가 없습니다."
            tk.Label(
                self.scroll_frame.scrollable, text=msg,
                font=(FONT, 11), bg=COLORS["surface"], fg=COLORS["text_secondary"],
                pady=40
            ).pack(fill="x")
            return

        for p in phrases:
            item = PhraseItem(
                self.scroll_frame.scrollable, p,
                on_use=self._use_phrase,
                on_edit=self._edit_phrase,
                on_delete=self._delete_phrase,
            )
            item.pack(fill="x")

    def _use_phrase(self, phrase):
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

        text = phrase["text"]
        self.destroy()
        self.app.withdraw()
        self.app.after(150, lambda: self._do_paste(text))

    def _do_paste(self, text):
        do_clipboard_paste(text)
        self.app.after(100, self.app.deiconify)

    def _add_phrase(self):
        self._open_editor(None)

    def _edit_phrase(self, phrase):
        self._open_editor(phrase)

    def _open_editor(self, phrase):
        win = tk.Toplevel(self)
        win.title("문장 편집" if phrase else "새 문장 추가")
        win.attributes("-topmost", True)
        win.configure(bg=COLORS["bg"])
        win.resizable(False, False)

        w, h = 440, 280
        x = self.winfo_x() + 20
        y = self.winfo_y() + 60
        win.geometry(f"{w}x{h}+{x}+{y}")

        title_bar = tk.Frame(win, bg=COLORS["primary_dark"], height=36)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(
            title_bar,
            text="  ✏ 문장 편집" if phrase else "  + 새 문장 추가",
            font=(FONT, 11, "bold"), bg=COLORS["primary_dark"], fg="white"
        ).pack(side="left")

        body = tk.Frame(win, bg=COLORS["bg"], padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="문장 내용", font=(FONT, 10, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        text_frame = tk.Frame(body, bg=COLORS["border"], padx=1, pady=1)
        text_frame.pack(fill="x", pady=(4, 10))
        text_box = tk.Text(text_frame, font=(FONT, 11), height=4, bd=0, wrap="word",
                           bg=COLORS["surface"], fg=COLORS["text"])
        text_box.pack(fill="x", padx=2, pady=2)
        if phrase:
            text_box.insert("1.0", phrase["text"])

        tk.Label(body, text="카테고리", font=(FONT, 10, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        cat_var = tk.StringVar(value=phrase["category"] if phrase else "일반")
        cat_combo = ttk.Combobox(
            body, textvariable=cat_var, values=self.app.data["categories"],
            font=(FONT, 10), state="normal"
        )
        cat_combo.pack(fill="x", pady=(4, 12))

        btn_frame = tk.Frame(body, bg=COLORS["bg"])
        btn_frame.pack(fill="x")

        def do_save():
            txt = text_box.get("1.0", "end").strip()
            cat = cat_var.get().strip()
            if not txt:
                messagebox.showinfo("알림", "문장을 입력해주세요.", parent=win)
                return
            if cat and cat not in self.app.data["categories"]:
                self.app.data["categories"].append(cat)

            if phrase:
                for p in self.app.data["phrases"]:
                    if p["id"] == phrase["id"]:
                        p["text"] = txt
                        p["category"] = cat or "일반"
                        break
            else:
                new_p = {
                    "id": str(uuid.uuid4())[:8],
                    "text": txt,
                    "category": cat or "일반",
                    "use_count": 0,
                }
                self.app.data["phrases"].append(new_p)

            save_data(self.app.data)
            win.destroy()
            self._rebuild_category_chips()
            self._populate()

        RoundedButton(
            btn_frame, text="저장", command=do_save,
            bg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            width=80, height=32
        ).pack(side="right")
        RoundedButton(
            btn_frame, text="취소", command=win.destroy,
            bg_color=COLORS["text_secondary"], hover_color="#616161",
            width=80, height=32
        ).pack(side="right", padx=(0, 8))

        text_box.focus_set()

    def _delete_phrase(self, phrase):
        if messagebox.askyesno(
            "삭제 확인",
            f"이 문장을 삭제하시겠습니까?\n\n\"{phrase['text'][:60]}\"",
            parent=self
        ):
            self.app.data["phrases"] = [
                p for p in self.app.data["phrases"] if p["id"] != phrase["id"]
            ]
            if phrase["id"] in self.app.data["recent_ids"]:
                self.app.data["recent_ids"].remove(phrase["id"])
            save_data(self.app.data)
            self._populate()

    def _add_category(self):
        win = tk.Toplevel(self)
        win.title("카테고리 추가")
        win.attributes("-topmost", True)
        win.configure(bg=COLORS["bg"])
        win.geometry("300x130")
        win.resizable(False, False)

        tk.Label(win, text="새 카테고리 이름:", font=(FONT, 10),
                 bg=COLORS["bg"]).pack(pady=(16, 4), padx=16, anchor="w")
        var = tk.StringVar()
        entry = tk.Entry(win, textvariable=var, font=(FONT, 11), bd=1, relief="solid")
        entry.pack(fill="x", padx=16)
        entry.focus_set()

        def do_add():
            name = var.get().strip()
            if name and name not in self.app.data["categories"]:
                self.app.data["categories"].append(name)
                save_data(self.app.data)
                self._rebuild_category_chips()
                win.destroy()
            elif name in self.app.data["categories"]:
                messagebox.showinfo("알림", "이미 존재하는 카테고리입니다.", parent=win)

        entry.bind("<Return>", lambda e: do_add())
        RoundedButton(
            win, text="추가", command=do_add,
            bg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            width=60, height=28
        ).pack(pady=10)

    def _import_export(self):
        win = tk.Toplevel(self)
        win.title("가져오기 / 내보내기")
        win.attributes("-topmost", True)
        win.configure(bg=COLORS["bg"])
        win.geometry("400x340")
        win.resizable(False, False)

        tk.Label(win, text="내보내기 (아래 텍스트를 복사하세요)", font=(FONT, 10, "bold"),
                 bg=COLORS["bg"]).pack(pady=(12, 4), padx=12, anchor="w")

        export_text = tk.Text(win, font=(FONT, 9), height=4, bd=1, relief="solid",
                              wrap="word", bg=COLORS["surface"])
        export_text.pack(fill="x", padx=12)
        export_data = json.dumps(self.app.data, ensure_ascii=False, indent=2)
        export_text.insert("1.0", export_data)
        export_text.configure(state="disabled")

        tk.Frame(win, bg=COLORS["divider"], height=1).pack(fill="x", padx=12, pady=10)

        tk.Label(win, text="가져오기 (JSON 데이터를 붙여넣으세요)", font=(FONT, 10, "bold"),
                 bg=COLORS["bg"]).pack(pady=(0, 4), padx=12, anchor="w")

        import_text = tk.Text(win, font=(FONT, 9), height=4, bd=1, relief="solid",
                              wrap="word", bg=COLORS["surface"])
        import_text.pack(fill="x", padx=12)

        def do_import():
            try:
                raw = import_text.get("1.0", "end").strip()
                new_data = json.loads(raw)
                if "phrases" in new_data:
                    for p in new_data["phrases"]:
                        if "id" not in p:
                            p["id"] = str(uuid.uuid4())[:8]
                        if "category" not in p:
                            p["category"] = "일반"
                        if "use_count" not in p:
                            p["use_count"] = 0
                    existing_texts = {p["text"] for p in self.app.data["phrases"]}
                    added = 0
                    for p in new_data["phrases"]:
                        if p["text"] not in existing_texts:
                            self.app.data["phrases"].append(p)
                            existing_texts.add(p["text"])
                            added += 1
                    for cat in new_data.get("categories", []):
                        if cat not in self.app.data["categories"]:
                            self.app.data["categories"].append(cat)
                    save_data(self.app.data)
                    self._rebuild_category_chips()
                    self._populate()
                    messagebox.showinfo("완료", f"{added}개 문장을 가져왔습니다.", parent=win)
                    win.destroy()
            except json.JSONDecodeError:
                messagebox.showerror("오류", "올바른 JSON 형식이 아닙니다.", parent=win)

        RoundedButton(
            win, text="가져오기 실행", command=do_import,
            bg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            width=100, height=32
        ).pack(pady=10)


class FloatingButton(tk.Tk):
    def __init__(self):
        super().__init__()
        self.data = load_data()
        self.panel = None
        self._click_time = None

        self.title("Quick Phrase")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)
        self.protocol("WM_DELETE_WINDOW", self._quit_app)

        btn_size = 50
        screen_w = self.winfo_screenwidth()
        self.geometry(f"{btn_size}x{btn_size}+{screen_w - btn_size - 16}+16")

        self.canvas = tk.Canvas(
            self, width=btn_size, height=btn_size,
            highlightthickness=0, cursor="hand2"
        )
        self.canvas.pack()
        self._draw_button("#1565C0")

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._show_menu)
        self.canvas.bind("<Enter>", lambda e: self._draw_button("#1976D2"))
        self.canvas.bind("<Leave>", lambda e: self._draw_button("#1565C0"))

        self._drag_data = {"x": 0, "y": 0, "moved": False}

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="열기 / 닫기", command=self._toggle_panel)
        self.menu.add_separator()
        self.menu.add_command(label="종료", command=self._quit_app)

        # Show the borderless window in the Windows taskbar.
        self.after(10, self._set_appwindow)

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

    def _draw_button(self, color):
        self.canvas.delete("all")
        self.canvas.configure(bg=color)
        self.canvas.create_oval(3, 3, 47, 47, fill=color, outline="#BBDEFB", width=2)
        self.canvas.create_text(25, 22, text="Q", font=(FONT, 20, "bold"), fill="white")
        self.canvas.create_text(25, 40, text="phrase", font=(FONT, 7), fill="#BBDEFB")

    def _on_press(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["moved"] = False
        self._click_time = time.time()

    def _on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        if abs(dx) > 3 or abs(dy) > 3:
            self._drag_data["moved"] = True
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    def _on_release(self, event):
        if self._drag_data["moved"]:
            return
        self._toggle_panel()


if __name__ == "__main__":
    app = FloatingButton()
    app.mainloop()
