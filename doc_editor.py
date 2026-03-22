#!/usr/bin/env python3
"""
עורך מסמכים v5 – הגדרות + צבעים תקינים
python3.14 doc_editor.py
python3.14 -m pip install pymupdf pillow --break-system-packages
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import os, io, copy, json

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── קובץ הגדרות ──────────────────────────────
SETTINGS_FILE = os.path.expanduser("~/.doc_editor_settings.json")

DEFAULT_SETTINGS = {
    "toolbar_bg":   "#2c3e50",
    "toolbar_fg":   "#ffffff",
    "btn_bg":       "#34495e",
    "btn_fg":       "#ffffff",
    "btn_active":   "#1a252f",
    "accent":       "#c0392b",
    "accent2":      "#2980b9",
    "success":      "#27ae60",
    "panel_bg":     "#ecf0f1",
    "panel_fg":     "#1a1a1a",
    "canvas_bg":    "#7f8c8d",
    "tab_act_bg":   "#2c3e50",
    "tab_act_fg":   "#ffffff",
    "tab_in_bg":    "#b2bec3",
    "tab_in_fg":    "#1a1a1a",
    "status_bg":    "#2c3e50",
    "status_fg":    "#ffffff",
    "font_size":    11,
    "font_family":  "Arial",
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                s = json.load(f)
                # Merge with defaults for any missing keys
                merged = dict(DEFAULT_SETTINGS)
                merged.update(s)
                return merged
    except:
        pass
    return dict(DEFAULT_SETTINGS)

def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
    except:
        pass

# ── כיתובים ──────────────────────────────────
T = {
    "title":         "עורך מסמכים",
    "open":          "פתח",
    "save":          "שמור",
    "save_as":       "שמור בשם",
    "builder":       "בנה קובץ חדש",
    "settings":      "הגדרות",
    "undo":          "בטל",
    "redo":          "חזור",
    "zoom_in":       "+",
    "zoom_out":      "-",
    "prev":          "<",
    "next":          ">",
    "color_lbl":     "צבע:",
    "size_lbl":      "עובי:",
    "page_of":       "מתוך",
    "open_more":     "+ פתח",
    "pages_lbl":     "עמודים",
    "layers_lbl":    "שכבות",
    "props_lbl":     "מאפיינים",
    "layer_up":      "מעלה",
    "layer_dn":      "למטה",
    "layer_del":     "מחק",
    "prop_font":     "גופן:",
    "prop_size":     "גודל:",
    "prop_color":    "צבע:",
    "prop_bold":     "מודגש",
    "prop_italic":   "נטוי",
    "prop_align":    "יישור:",
    "tool_region":   "בחר אזור",
    "tool_select":   "בחר",
    "tool_text":     "טקסט",
    "tool_sign":     "חתימה",
    "tool_pen":      "עיפרון",
    "tool_line":     "קו",
    "tool_arrow":    "חץ",
    "tool_rect":     "מלבן",
    "tool_ellipse":  "עיגול",
    "tool_highlight":"הדגשה",
    "tool_eraser":   "מחק",
    "tool_whiteout": "לבן",
    "tool_crop":     "חיתוך",
    "builder_title": "בונה קבצים",
    "builder_src":   "עמודים זמינים",
    "builder_dst":   "קובץ חדש",
    "builder_prev":  "תצוגה מקדימה",
    "builder_add":   "הוסף",
    "builder_rem":   "הסר",
    "builder_up":    "למעלה",
    "builder_dn":    "למטה",
    "builder_save":  "שמור קובץ חדש",
    "builder_open":  "+ פתח קובץ",
    "builder_clear": "נקה",
    "settings_title":"הגדרות תצוגה",
    "settings_save": "שמור והפעל מחדש",
    "settings_reset":"איפוס לברירת מחדל",
    "edit_labels":   "ערוך כיתובים",
    "save_labels":   "שמור",
    "cancel":        "ביטול",
    "no_file":       "אין קובץ פתוח",
    "saved_ok":      "נשמר בהצלחה",
    "loading":       "טוען...",
    "saving":        "שומר...",
    "ready":         "מוכן",
    "enter_text":    "הכנס טקסט:",
    "enter_sign":    "הכנס שם לחתימה:",
    "images_to_pdf": "תמונות ל-PDF",
}


class Element:
    _id = 0
    def __init__(self, kind, **kw):
        Element._id += 1
        self.id        = Element._id
        self.kind      = kind
        self.page      = kw.get("page", 0)
        self.x         = kw.get("x", 0.0)
        self.y         = kw.get("y", 0.0)
        self.x2        = kw.get("x2", 0.0)
        self.y2        = kw.get("y2", 0.0)
        self.text      = kw.get("text", "")
        self.color     = kw.get("color", "#c0392b")
        self.size      = kw.get("size", 2)
        self.font_size = kw.get("font_size", 14)
        self.points    = kw.get("points", [])
        self.pil_img   = kw.get("pil_img", None)
        self.visible   = True

    def clone(self):
        e = copy.copy(self)
        Element._id += 1
        e.id = Element._id
        e.x += 20; e.y += 20; e.x2 += 20; e.y2 += 20
        e.points  = [(px+20,py+20) for px,py in self.points]
        e.pil_img = self.pil_img.copy() if self.pil_img else None
        return e


class DocTab:
    def __init__(self, path):
        self.path        = path
        self.name        = os.path.basename(path)
        self.ext         = os.path.splitext(path)[1].lower()
        self.is_pdf      = self.ext == ".pdf"
        self.is_image    = self.ext in (".jpg",".jpeg",".png",".tiff",".tif",".bmp")
        self.doc         = None
        self.pil_base    = None
        self.page_idx    = 0
        self.total_pages = 1
        self.zoom        = 1.5
        self.elements    = []
        self.undo_stack  = []
        self.redo_stack  = []
        self.modified    = False

    def load(self):
        if self.is_pdf and FITZ_OK:
            self.doc = fitz.open(self.path)
            self.total_pages = len(self.doc)
        elif self.is_image and PIL_OK:
            self.pil_base = Image.open(self.path)
            self.total_pages = getattr(self.pil_base,"n_frames",1)
        return self

    def base_image(self):
        if self.is_pdf and self.doc:
            page = self.doc[self.page_idx]
            mat  = fitz.Matrix(self.zoom,self.zoom)
            pix  = page.get_pixmap(matrix=mat)
            return Image.open(io.BytesIO(pix.tobytes("ppm"))).convert("RGBA")
        elif self.is_image and self.pil_base:
            img = self.pil_base.copy().convert("RGBA")
            return img.resize((int(img.width*self.zoom),int(img.height*self.zoom)),Image.LANCZOS)
        return None

    def page_els(self):
        return [e for e in self.elements if e.page==self.page_idx]

    def push_undo(self):
        self.undo_stack.append(copy.deepcopy(self.elements))
        if len(self.undo_stack)>50: self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack: return False
        self.redo_stack.append(copy.deepcopy(self.elements))
        self.elements = self.undo_stack.pop(); return True

    def redo(self):
        if not self.redo_stack: return False
        self.undo_stack.append(copy.deepcopy(self.elements))
        self.elements = self.redo_stack.pop(); return True

    def close(self):
        if self.doc: self.doc.close()


class DocEditor:
    def __init__(self, root):
        self.root = root
        self.S    = load_settings()   # הגדרות נוכחיות
        self.root.title(T["title"])
        self.root.geometry("1420x900")
        self.root.configure(bg=self.S["panel_bg"])

        self.tabs        = []
        self.active_tab  = None
        self.photo_ref   = None
        self.edit_mode   = "select"
        self.draw_color  = "#c0392b"
        self.draw_size   = 2
        self.mouse_start = None
        self.temp_id     = None
        self.sel_el      = None
        self.drag_off    = (0,0)
        self.pen_pts     = []
        self.is_drag     = False
        self.region_rect = None
        self.region_moved= False
        self.region_doff = (0,0)
        self.clipboard   = None

        self._apply_ttk_style()
        self._build_ui()
        self._bind_keys()
        if not FITZ_OK or not PIL_OK:
            messagebox.showwarning("ספריות חסרות",
                "python3.14 -m pip install pymupdf pillow --break-system-packages")

    # ══ TTK Style – מכריח Mac לציית לצבעים ══════

    def _apply_ttk_style(self):
        """
        על Mac, tk.Button מתעלם מצבעים.
        הפתרון: ttk.Button עם Style מוגדר במפורש.
        """
        S = self.S
        style = ttk.Style(self.root)
        style.theme_use("default")

        # כפתור רגיל – כהה עם טקסט לבן
        style.configure("Dark.TButton",
            background=S["btn_bg"],
            foreground=S["btn_fg"],
            font=(S["font_family"], S["font_size"], "bold"),
            padding=(10,5),
            relief="flat",
            borderwidth=0)
        style.map("Dark.TButton",
            background=[("active",S["btn_active"]),("pressed",S["btn_active"])],
            foreground=[("active",S["btn_fg"])])

        # כפתור אדום – פעולה ראשית
        style.configure("Red.TButton",
            background=S["accent"],
            foreground=S["btn_fg"],
            font=(S["font_family"], S["font_size"], "bold"),
            padding=(10,5),
            relief="flat",
            borderwidth=0)
        style.map("Red.TButton",
            background=[("active","#a93226"),("pressed","#a93226")],
            foreground=[("active",S["btn_fg"])])

        # כפתור כחול – משני
        style.configure("Blue.TButton",
            background=S["accent2"],
            foreground=S["btn_fg"],
            font=(S["font_family"], S["font_size"], "bold"),
            padding=(10,5),
            relief="flat",
            borderwidth=0)
        style.map("Blue.TButton",
            background=[("active","#2471a3"),("pressed","#2471a3")],
            foreground=[("active",S["btn_fg"])])

        # כפתור ירוק – שמירה
        style.configure("Green.TButton",
            background=S["success"],
            foreground=S["btn_fg"],
            font=(S["font_family"], S["font_size"], "bold"),
            padding=(10,5),
            relief="flat",
            borderwidth=0)
        style.map("Green.TButton",
            background=[("active","#1e8449"),("pressed","#1e8449")],
            foreground=[("active",S["btn_fg"])])

        # כפתור כלי – רחב יותר
        style.configure("Tool.TButton",
            background=S["btn_bg"],
            foreground=S["btn_fg"],
            font=(S["font_family"], S["font_size"], "bold"),
            padding=(8,6),
            anchor="e",
            relief="flat",
            borderwidth=0)
        style.map("Tool.TButton",
            background=[("active",S["btn_active"]),("pressed",S["btn_active"])],
            foreground=[("active",S["btn_fg"])])

        # כלי פעיל – אדום
        style.configure("ActiveTool.TButton",
            background=S["accent"],
            foreground=S["btn_fg"],
            font=(S["font_family"], S["font_size"], "bold"),
            padding=(8,6),
            anchor="e",
            relief="flat",
            borderwidth=0)
        style.map("ActiveTool.TButton",
            background=[("active","#a93226")],
            foreground=[("active",S["btn_fg"])])

    # ══ בניית ממשק ════════════════════════════════

    def _build_ui(self):
        self._build_menu()
        self._build_toolbar()
        self._build_tabs_bar()
        body = tk.Frame(self.root, bg=self.S["panel_bg"])
        body.pack(fill=tk.BOTH, expand=True)
        self._build_left(body)
        self._build_canvas(body)
        self._build_right(body)
        self._build_status()
        self.set_mode("select")

    def _build_menu(self):
        S = self.S
        mb = tk.Menu(self.root, bg=S["toolbar_bg"], fg=S["toolbar_fg"],
                     activebackground=S["accent"], activeforeground=S["btn_fg"])
        self.root.config(menu=mb)
        fm = tk.Menu(mb, tearoff=0, bg=S["panel_bg"], fg=S["panel_fg"],
                     activebackground=S["accent2"], activeforeground=S["btn_fg"])
        fm.add_command(label=T["open"],          command=self.open_file)
        fm.add_command(label=T["save"],          command=self.save_file)
        fm.add_command(label=T["save_as"],       command=self.save_as)
        fm.add_separator()
        fm.add_command(label=T["images_to_pdf"], command=self.images_to_pdf)
        mb.add_cascade(label="קובץ", menu=fm)
        em = tk.Menu(mb, tearoff=0, bg=S["panel_bg"], fg=S["panel_fg"],
                     activebackground=S["accent2"], activeforeground=S["btn_fg"])
        em.add_command(label="בטל  Ctrl+Z",  command=self.undo)
        em.add_command(label="חזור  Ctrl+Y", command=self.redo)
        em.add_separator()
        em.add_command(label="העתק  Ctrl+C", command=self.copy_el)
        em.add_command(label="הדבק  Ctrl+V", command=self.paste_el)
        em.add_command(label="מחק   Delete", command=self.delete_sel)
        em.add_separator()
        em.add_command(label="סיבוב ימינה",  command=self.rotate_r)
        em.add_command(label="סיבוב שמאלה", command=self.rotate_l)
        em.add_command(label="מחק עמוד",     command=self.delete_page)
        mb.add_cascade(label="עריכה", menu=em)
        tm = tk.Menu(mb, tearoff=0, bg=S["panel_bg"], fg=S["panel_fg"],
                     activebackground=S["accent2"], activeforeground=S["btn_fg"])
        tm.add_command(label=T["builder"],     command=self.open_builder)
        tm.add_command(label=T["settings"],    command=self.open_settings)
        tm.add_separator()
        tm.add_command(label=T["edit_labels"], command=self.edit_labels)
        mb.add_cascade(label="כלים", menu=tm)

    def _build_toolbar(self):
        S  = self.S
        tb = tk.Frame(self.root, bg=S["toolbar_bg"], height=50)
        tb.pack(fill=tk.X); tb.pack_propagate(False)

        def sep():
            tk.Frame(tb, bg="#546e7a", width=1).pack(
                side=tk.LEFT, fill=tk.Y, padx=6, pady=8)

        def tbtn(text, cmd, style="Dark.TButton", **kw):
            b = ttk.Button(tb, text=text, command=cmd, style=style, **kw)
            b.pack(side=tk.LEFT, padx=3, pady=8)
            return b

        tbtn(T["open"],     self.open_file)
        tbtn(T["save"],     self.save_file)
        tbtn(T["builder"],  self.open_builder,  style="Red.TButton")
        tbtn(T["settings"], self.open_settings, style="Blue.TButton")
        sep()
        tbtn(T["undo"], self.undo)
        tbtn(T["redo"], self.redo)
        sep()
        tbtn(T["zoom_out"], self.zoom_out, width=2)
        self.zoom_lbl = tk.Label(tb, text="150%", bg=S["toolbar_bg"],
                                  fg=S["toolbar_fg"],
                                  font=(S["font_family"],10,"bold"), width=5)
        self.zoom_lbl.pack(side=tk.LEFT)
        tbtn(T["zoom_in"], self.zoom_in, width=2)
        sep()
        tbtn(T["prev"], self.prev_page, width=2)
        self.page_lbl = tk.Label(tb, text="- / -", bg=S["toolbar_bg"],
                                  fg=S["toolbar_fg"],
                                  font=(S["font_family"],10,"bold"), width=10)
        self.page_lbl.pack(side=tk.LEFT)
        tbtn(T["next"], self.next_page, width=2)
        sep()
        tk.Label(tb, text=T["color_lbl"], bg=S["toolbar_bg"],
                 fg=S["toolbar_fg"],
                 font=(S["font_family"],10,"bold")).pack(side=tk.LEFT, padx=4)
        self.color_btn = tk.Button(tb, bg=self.draw_color, width=3,
                                    relief=tk.GROOVE, cursor="hand2",
                                    command=self.pick_color)
        self.color_btn.pack(side=tk.LEFT, padx=3, pady=12)
        tk.Label(tb, text=T["size_lbl"], bg=S["toolbar_bg"],
                 fg=S["toolbar_fg"],
                 font=(S["font_family"],10,"bold")).pack(side=tk.LEFT, padx=4)
        self.size_var = tk.IntVar(value=2)
        tk.Spinbox(tb, from_=1, to=50, textvariable=self.size_var,
                   width=4, bg=S["btn_bg"], fg=S["btn_fg"],
                   buttonbackground=S["btn_bg"],
                   relief=tk.FLAT, font=(S["font_family"],10)
                   ).pack(side=tk.LEFT, padx=3, pady=12)
        self.mode_lbl = tk.Label(tb, text="", bg=S["toolbar_bg"],
                                  fg="#f39c12",
                                  font=(S["font_family"],10,"bold"))
        self.mode_lbl.pack(side=tk.RIGHT, padx=14)

    def _build_tabs_bar(self):
        S = self.S
        self.tabs_bar   = tk.Frame(self.root, bg="#dfe6e9", height=32)
        self.tabs_bar.pack(fill=tk.X); self.tabs_bar.pack_propagate(False)
        self.tab_frames = []
        ttk.Button(self.tabs_bar, text=T["open_more"],
                   command=self.open_file,
                   style="Blue.TButton"
                   ).pack(side=tk.LEFT, padx=6, pady=4)

    def _add_tab_btn(self, tab, idx):
        S  = self.S
        f  = tk.Frame(self.tabs_bar, bg=S["tab_in_bg"], padx=2)
        f.pack(side=tk.LEFT, padx=1, pady=4)
        name = (tab.name[:16]+"...") if len(tab.name)>18 else tab.name
        b = tk.Button(f, text=name, bg=S["tab_in_bg"], fg=S["tab_in_fg"],
                      relief=tk.FLAT, font=(S["font_family"],10,"bold"),
                      cursor="hand2", bd=0, padx=8,
                      command=lambda i=idx: self.switch_tab(i))
        b.pack(side=tk.LEFT)
        c = tk.Button(f, text="x", bg=S["tab_in_bg"], fg=S["tab_in_fg"],
                      relief=tk.FLAT, font=(S["font_family"],9),
                      cursor="hand2", bd=0, padx=4,
                      command=lambda i=idx: self.close_tab(i))
        c.pack(side=tk.LEFT)
        self.tab_frames.append((f,b,c))

    def switch_tab(self, idx):
        if idx >= len(self.tabs): return
        S = self.S
        self.active_tab  = idx
        self.sel_el      = None
        self.region_rect = None
        for i,(f,b,c) in enumerate(self.tab_frames):
            act = (i==idx)
            bg  = S["tab_act_bg"] if act else S["tab_in_bg"]
            fg  = S["tab_act_fg"] if act else S["tab_in_fg"]
            f.config(bg=bg); b.config(bg=bg,fg=fg); c.config(bg=bg,fg=fg)
        self._refresh_pages(); self._render()

    def close_tab(self, idx):
        if idx >= len(self.tabs): return
        self.tabs[idx].close()
        self.tabs.pop(idx)
        f,_,_ = self.tab_frames.pop(idx); f.destroy()
        if self.tabs: self.switch_tab(min(idx,len(self.tabs)-1))
        else:
            self.active_tab=None; self.canvas.delete("all"); self._update_nav()

    def _build_left(self, parent):
        S    = self.S
        left = tk.Frame(parent, bg=S["panel_bg"], width=152)
        left.pack(side=tk.LEFT, fill=tk.Y); left.pack_propagate(False)

        tk.Label(left, text="כלים", bg=S["accent"], fg=S["btn_fg"],
                 font=(S["font_family"],11,"bold"),
                 pady=5, anchor=tk.E, padx=8).pack(fill=tk.X)

        self.tool_btns = {}
        tools = [
            ("region",    T["tool_region"]),
            ("select",    T["tool_select"]),
            ("text",      T["tool_text"]),
            ("sign",      T["tool_sign"]),
            ("pen",       T["tool_pen"]),
            ("line",      T["tool_line"]),
            ("arrow",     T["tool_arrow"]),
            ("rect",      T["tool_rect"]),
            ("ellipse",   T["tool_ellipse"]),
            ("highlight", T["tool_highlight"]),
            ("eraser",    T["tool_eraser"]),
            ("whiteout",  T["tool_whiteout"]),
            ("crop",      T["tool_crop"]),
        ]
        for mode, label in tools:
            b = ttk.Button(left, text=label, style="Tool.TButton",
                           command=lambda m=mode: self.set_mode(m))
            b.pack(fill=tk.X, padx=4, pady=1)
            self.tool_btns[mode] = b

        tk.Frame(left, bg="#bdc3c7", height=1).pack(fill=tk.X, padx=4, pady=5)

        tk.Label(left, text=T["pages_lbl"], bg=S["accent2"], fg=S["btn_fg"],
                 font=(S["font_family"],10,"bold"),
                 pady=3, anchor=tk.E, padx=8).pack(fill=tk.X)

        self.pages_list = tk.Listbox(left,
                                      bg="#ffffff", fg="#1a1a1a",
                                      selectbackground=S["accent2"],
                                      selectforeground=S["btn_fg"],
                                      font=(S["font_family"],10),
                                      bd=0, highlightthickness=0, relief=tk.FLAT)
        self.pages_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.pages_list.bind("<<ListboxSelect>>", self._on_page_sel)

    def _build_canvas(self, parent):
        S  = self.S
        cf = tk.Frame(parent, bg="#555")
        cf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(cf, bg=S["canvas_bg"], cursor="arrow",
                                 highlightthickness=0)
        vs = ttk.Scrollbar(cf, orient=tk.VERTICAL,   command=self.canvas.yview)
        hs = ttk.Scrollbar(cf, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        hs.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>",   self._press)
        self.canvas.bind("<B1-Motion>",       self._drag_ev)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Double-Button-1>", self._dbl)
        self.canvas.bind("<MouseWheel>",      self._wheel)

    def _build_right(self, parent):
        S     = self.S
        right = tk.Frame(parent, bg=S["panel_bg"], width=205)
        right.pack(side=tk.RIGHT, fill=tk.Y); right.pack_propagate(False)

        tk.Label(right, text=T["layers_lbl"], bg=S["accent2"], fg=S["btn_fg"],
                 font=(S["font_family"],11,"bold"),
                 pady=5, anchor=tk.E, padx=8).pack(fill=tk.X)

        self.layers_list = tk.Listbox(right,
                                       bg="#ffffff", fg="#1a1a1a",
                                       selectbackground=S["accent"],
                                       selectforeground=S["btn_fg"],
                                       font=(S["font_family"],10),
                                       bd=0, highlightthickness=0,
                                       relief=tk.FLAT, height=7)
        self.layers_list.pack(fill=tk.X, padx=4, pady=4)
        self.layers_list.bind("<<ListboxSelect>>", self._on_layer_sel)

        lbf = tk.Frame(right, bg=S["panel_bg"]); lbf.pack(fill=tk.X, padx=4, pady=2)
        for lbl_t,cmd,sty in [
            (T["layer_up"],  self.layer_up,  "Dark.TButton"),
            (T["layer_dn"],  self.layer_dn,  "Dark.TButton"),
            (T["layer_del"], self.delete_sel,"Red.TButton"),
        ]:
            ttk.Button(lbf, text=lbl_t, command=cmd, style=sty
                       ).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(right, bg="#bdc3c7", height=1).pack(fill=tk.X, padx=4, pady=6)

        tk.Label(right, text=T["props_lbl"], bg=S["toolbar_bg"], fg=S["toolbar_fg"],
                 font=(S["font_family"],11,"bold"),
                 pady=5, anchor=tk.E, padx=8).pack(fill=tk.X)

        pf = tk.Frame(right, bg=S["panel_bg"]); pf.pack(fill=tk.X, padx=8, pady=6)

        def row(lbl_text):
            f = tk.Frame(pf, bg=S["panel_bg"]); f.pack(fill=tk.X, pady=3)
            tk.Label(f, text=lbl_text, bg=S["panel_bg"], fg=S["panel_fg"],
                     font=(S["font_family"],10,"bold"),
                     anchor=tk.E, width=7).pack(side=tk.RIGHT)
            return f

        r1 = row(T["prop_font"])
        self.prop_font = tk.StringVar(value="Arial")
        tk.Entry(r1, textvariable=self.prop_font,
                 bg="#ffffff", fg="#1a1a1a", relief=tk.GROOVE,
                 font=(S["font_family"],10), width=12).pack(side=tk.RIGHT)

        r2 = row(T["prop_size"])
        self.prop_sz = tk.IntVar(value=14)
        tk.Spinbox(r2, from_=6, to=72, textvariable=self.prop_sz,
                   width=5, bg="#ffffff", fg="#1a1a1a",
                   relief=tk.GROOVE, font=(S["font_family"],10)).pack(side=tk.RIGHT)

        r3 = row(T["prop_color"])
        self.prop_color_btn = tk.Button(r3, bg=self.draw_color, width=3,
                                         relief=tk.GROOVE, cursor="hand2",
                                         command=self.pick_color)
        self.prop_color_btn.pack(side=tk.RIGHT)

        r4 = tk.Frame(pf, bg=S["panel_bg"]); r4.pack(fill=tk.X, pady=3)
        self.bold_var   = tk.BooleanVar()
        self.italic_var = tk.BooleanVar()
        for txt,var in [(T["prop_bold"],self.bold_var),(T["prop_italic"],self.italic_var)]:
            tk.Checkbutton(r4, text=txt, variable=var,
                           bg=S["panel_bg"], fg=S["panel_fg"],
                           selectcolor="#ffffff",
                           activebackground=S["panel_bg"],
                           activeforeground=S["panel_fg"],
                           font=(S["font_family"],10,"bold")
                           ).pack(side=tk.RIGHT, padx=4)

        r5 = tk.Frame(pf, bg=S["panel_bg"]); r5.pack(fill=tk.X, pady=3)
        self.align_var = tk.StringVar(value="right")
        tk.Label(r5, text=T["prop_align"], bg=S["panel_bg"], fg=S["panel_fg"],
                 font=(S["font_family"],10,"bold")).pack(side=tk.RIGHT, padx=4)
        for val,sym in [("right","=>"),("center","<>"),("left","<=")]:
            tk.Radiobutton(r5, text=sym, variable=self.align_var, value=val,
                           bg=S["panel_bg"], fg=S["panel_fg"],
                           selectcolor="#ffffff",
                           activebackground=S["panel_bg"],
                           font=(S["font_family"],11)).pack(side=tk.RIGHT, padx=3)

    def _build_status(self):
        S  = self.S
        sb = tk.Frame(self.root, bg=S["status_bg"], height=28)
        sb.pack(fill=tk.X, side=tk.BOTTOM); sb.pack_propagate(False)
        self.status_var = tk.StringVar(value=T["ready"])
        tk.Label(sb, textvariable=self.status_var,
                 bg=S["status_bg"], fg=S["status_fg"],
                 font=(S["font_family"],10,"bold"),
                 anchor=tk.E, padx=12).pack(fill=tk.X)

    def _bind_keys(self):
        self.root.bind("<Control-z>",      lambda e: self.undo())
        self.root.bind("<Control-y>",      lambda e: self.redo())
        self.root.bind("<Control-c>",      lambda e: self.copy_el())
        self.root.bind("<Control-v>",      lambda e: self.paste_el())
        self.root.bind("<Control-x>",      lambda e: self.cut_el())
        self.root.bind("<Delete>",         lambda e: self.delete_sel())
        self.root.bind("<Control-s>",      lambda e: self.save_file())
        self.root.bind("<Control-o>",      lambda e: self.open_file())
        self.root.bind("<Control-comma>",  lambda e: self.open_settings())
        self.root.bind("<Escape>",         lambda e: self._cancel_region())

    # ══ הגדרות ════════════════════════════════════

    def open_settings(self):
        S   = self.S
        win = tk.Toplevel(self.root)
        win.title(T["settings_title"])
        win.geometry("520x600")
        win.configure(bg=S["panel_bg"])
        win.grab_set()

        tk.Label(win, text=T["settings_title"],
                 bg=S["accent"], fg=S["btn_fg"],
                 font=(S["font_family"],13,"bold"),
                 pady=8, anchor=tk.CENTER).pack(fill=tk.X)

        # גלילה
        cont = tk.Frame(win, bg=S["panel_bg"])
        cont.pack(fill=tk.BOTH, expand=True, padx=10)
        cv   = tk.Canvas(cont, bg=S["panel_bg"], highlightthickness=0)
        sb   = ttk.Scrollbar(cont, orient=tk.VERTICAL, command=cv.yview)
        inner= tk.Frame(cv, bg=S["panel_bg"])
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=inner, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # קטגוריות הגדרות
        sections = [
            ("סרגל כלים", [
                ("toolbar_bg",  "רקע סרגל כלים"),
                ("toolbar_fg",  "טקסט סרגל כלים"),
                ("btn_bg",      "רקע כפתורים"),
                ("btn_fg",      "טקסט כפתורים"),
                ("btn_active",  "כפתור לחוץ"),
            ]),
            ("צבעי הדגש", [
                ("accent",   "אדום – פעולה ראשית"),
                ("accent2",  "כחול – פעולות משניות"),
                ("success",  "ירוק – שמירה"),
            ]),
            ("פאנלים", [
                ("panel_bg",  "רקע פאנלים"),
                ("panel_fg",  "טקסט פאנלים"),
                ("canvas_bg", "רקע אזור עבודה"),
            ]),
            ("לשוניות", [
                ("tab_act_bg", "לשונית פעילה – רקע"),
                ("tab_act_fg", "לשונית פעילה – טקסט"),
                ("tab_in_bg",  "לשונית רגילה – רקע"),
                ("tab_in_fg",  "לשונית רגילה – טקסט"),
            ]),
            ("שורת סטטוס", [
                ("status_bg", "רקע"),
                ("status_fg", "טקסט"),
            ]),
        ]

        entries = {}

        for sec_title, fields in sections:
            tk.Label(inner, text=sec_title,
                     bg=S["accent2"], fg=S["btn_fg"],
                     font=(S["font_family"],10,"bold"),
                     pady=3, anchor=tk.E, padx=8
                     ).pack(fill=tk.X, padx=4, pady=(8,2))

            for key, label in fields:
                row = tk.Frame(inner, bg=S["panel_bg"])
                row.pack(fill=tk.X, padx=8, pady=3)

                # תצוגת צבע
                preview = tk.Frame(row, bg=S.get(key,"#cccccc"),
                                    width=28, height=22,
                                    relief=tk.GROOVE, bd=1)
                preview.pack(side=tk.LEFT, padx=4)
                preview.pack_propagate(False)

                # תווית
                tk.Label(row, text=label, bg=S["panel_bg"], fg=S["panel_fg"],
                         font=(S["font_family"],10), width=20,
                         anchor=tk.E).pack(side=tk.RIGHT)

                # שדה ערך
                var = tk.StringVar(value=S.get(key,"#000000"))
                e   = tk.Entry(row, textvariable=var,
                               bg="#ffffff", fg="#1a1a1a",
                               relief=tk.GROOVE, font=("Courier",10), width=10)
                e.pack(side=tk.RIGHT, padx=4)

                def pick(k=key, v=var, p=preview):
                    c = colorchooser.askcolor(color=v.get(), title=k)[1]
                    if c: v.set(c); p.config(bg=c)

                tk.Button(row, text="בחר", command=pick,
                          bg=S["btn_bg"], fg=S["btn_fg"],
                          relief=tk.FLAT, font=(S["font_family"],9),
                          cursor="hand2", padx=6
                          ).pack(side=tk.RIGHT, padx=2)

                # עדכון preview בהקלדה
                def update_preview(event, v=var, p=preview):
                    try: p.config(bg=v.get())
                    except: pass
                e.bind("<KeyRelease>", update_preview)

                entries[key] = var

        # גודל פונט
        tk.Label(inner, text="גופן",
                 bg=S["accent2"], fg=S["btn_fg"],
                 font=(S["font_family"],10,"bold"),
                 pady=3, anchor=tk.E, padx=8
                 ).pack(fill=tk.X, padx=4, pady=(8,2))

        font_row = tk.Frame(inner, bg=S["panel_bg"])
        font_row.pack(fill=tk.X, padx=8, pady=3)
        tk.Label(font_row, text="גודל פונט:", bg=S["panel_bg"], fg=S["panel_fg"],
                 font=(S["font_family"],10), anchor=tk.E
                 ).pack(side=tk.RIGHT, padx=4)
        font_sz_var = tk.IntVar(value=S.get("font_size",11))
        tk.Spinbox(font_row, from_=8, to=16, textvariable=font_sz_var,
                   width=4, bg="#ffffff", fg="#1a1a1a",
                   relief=tk.GROOVE, font=(S["font_family"],10)
                   ).pack(side=tk.RIGHT, padx=4)

        font_row2 = tk.Frame(inner, bg=S["panel_bg"])
        font_row2.pack(fill=tk.X, padx=8, pady=3)
        tk.Label(font_row2, text="משפחת גופן:", bg=S["panel_bg"], fg=S["panel_fg"],
                 font=(S["font_family"],10), anchor=tk.E
                 ).pack(side=tk.RIGHT, padx=4)
        font_fam_var = tk.StringVar(value=S.get("font_family","Arial"))
        ttk.Combobox(font_row2, textvariable=font_fam_var,
                     values=["Arial","Helvetica","Times New Roman",
                             "Courier New","Tahoma","Verdana"],
                     width=15, state="readonly"
                     ).pack(side=tk.RIGHT, padx=4)

        # כפתורים תחתונים
        bf = tk.Frame(win, bg=S["panel_bg"]); bf.pack(pady=10)

        def apply_and_restart():
            new_s = dict(S)
            for k,v in entries.items():
                new_s[k] = v.get()
            new_s["font_size"]   = font_sz_var.get()
            new_s["font_family"] = font_fam_var.get()
            save_settings(new_s)
            win.destroy()
            messagebox.showinfo("הגדרות",
                "ההגדרות נשמרו!\nיש לסגור ולפתוח מחדש את התוכנה כדי לראות את השינויים.")

        def reset_defaults():
            if messagebox.askyesno("איפוס","לאפס לברירת מחדל?"):
                save_settings(DEFAULT_SETTINGS)
                win.destroy()
                messagebox.showinfo("","אופסן. פתח מחדש את התוכנה.")

        ttk.Button(bf, text=T["settings_save"],  command=apply_and_restart,
                   style="Green.TButton").pack(side=tk.LEFT, padx=6)
        ttk.Button(bf, text=T["settings_reset"], command=reset_defaults,
                   style="Red.TButton").pack(side=tk.LEFT, padx=6)
        ttk.Button(bf, text=T["cancel"],         command=win.destroy,
                   style="Dark.TButton").pack(side=tk.LEFT, padx=6)

    # ══ פתיחה ══════════════════════════════════════

    def open_file(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("קבצים נתמכים","*.pdf *.jpg *.jpeg *.png *.tiff *.tif *.bmp"),
                       ("PDF","*.pdf"),("תמונות","*.jpg *.jpeg *.png *.tiff *.tif *.bmp")])
        for p in paths: self._load(p)

    def _load(self, path):
        try:
            self.status_var.set(T["loading"]); self.root.update_idletasks()
            tab = DocTab(path).load()
            self.tabs.append(tab); idx = len(self.tabs)-1
            self._add_tab_btn(tab,idx); self.switch_tab(idx)
            self.status_var.set(T["ready"])
        except Exception as e:
            messagebox.showerror("שגיאה",str(e))
            self.status_var.set(T["ready"])

    # ══ תצוגה ══════════════════════════════════════

    def _tab(self):
        if self.active_tab is not None and self.active_tab < len(self.tabs):
            return self.tabs[self.active_tab]
        return None

    def _refresh_pages(self):
        self.pages_list.delete(0,tk.END)
        tab = self._tab()
        if not tab: return
        for i in range(tab.total_pages):
            self.pages_list.insert(tk.END,f"עמוד {i+1}")
        self.pages_list.selection_set(tab.page_idx)

    def _render(self):
        tab = self._tab()
        if not tab: return
        try:
            base = tab.base_image()
            if not base: return
            drw = ImageDraw.Draw(base,"RGBA")
            for el in tab.page_els():
                if el.visible: self._draw_el(drw,el,tab.zoom,base)
            self.photo_ref = ImageTk.PhotoImage(base.convert("RGB"))
            self.canvas.delete("all")
            self.canvas.create_image(20,20,anchor=tk.NW,image=self.photo_ref,tags="page")
            if self.region_rect and self.edit_mode=="region":
                rx,ry,rx2,ry2 = self.region_rect; z=tab.zoom
                self.canvas.create_rectangle(rx*z+20,ry*z+20,rx2*z+20,ry2*z+20,
                                              outline="#2980b9",width=2,dash=(6,3))
            if self.sel_el and self.sel_el.page==tab.page_idx:
                self._sel_box(tab.zoom)
            w,h = base.size
            self.canvas.configure(scrollregion=(0,0,w+40,h+40))
            self._update_nav(); self._update_layers()
        except Exception as e:
            print(f"render: {e}")

    def _draw_el(self, drw, el, z, base_img=None):
        c = el.color or "#000000"
        if el.kind=="text":
            try: fnt=ImageFont.truetype("/System/Library/Fonts/Arial.ttf",int(el.font_size*z))
            except: fnt=ImageFont.load_default()
            drw.text((el.x*z,el.y*z),el.text,fill=c,font=fnt)
        elif el.kind=="sign":
            try: fnt=ImageFont.truetype("/System/Library/Fonts/Arial.ttf",int(el.font_size*z))
            except: fnt=ImageFont.load_default()
            drw.text((el.x*z,el.y*z),el.text,fill="#1a56db",font=fnt)
            ly=el.y*z+el.font_size*z+2
            drw.line([(el.x*z,ly),(el.x*z+len(el.text)*el.font_size*z*0.55,ly)],fill="#1a56db",width=max(1,int(z)))
        elif el.kind=="pen":
            if len(el.points)>=2: drw.line([(px*z,py*z) for px,py in el.points],fill=c,width=el.size)
        elif el.kind=="eraser":
            if len(el.points)>=2: drw.line([(px*z,py*z) for px,py in el.points],fill="white",width=el.size*4)
        elif el.kind=="line":
            drw.line([(el.x*z,el.y*z),(el.x2*z,el.y2*z)],fill=c,width=el.size)
        elif el.kind=="arrow":
            drw.line([(el.x*z,el.y*z),(el.x2*z,el.y2*z)],fill=c,width=el.size)
            r=max(4,el.size*2); drw.ellipse([(el.x2*z-r,el.y2*z-r),(el.x2*z+r,el.y2*z+r)],fill=c)
        elif el.kind=="rect":
            drw.rectangle([(el.x*z,el.y*z),(el.x2*z,el.y2*z)],outline=c,width=el.size)
        elif el.kind=="ellipse":
            drw.ellipse([(el.x*z,el.y*z),(el.x2*z,el.y2*z)],outline=c,width=el.size)
        elif el.kind=="highlight":
            drw.rectangle([(el.x*z,el.y*z),(el.x2*z,el.y2*z)],fill=(255,255,0,80))
        elif el.kind=="whiteout":
            drw.rectangle([(el.x*z,el.y*z),(el.x2*z,el.y2*z)],fill=(255,255,255,255))
        elif el.kind=="region_img" and el.pil_img and base_img:
            rw=int((el.x2-el.x)*z); rh=int((el.y2-el.y)*z)
            if rw>0 and rh>0:
                sc=el.pil_img.resize((rw,rh),Image.LANCZOS).convert("RGBA")
                base_img.paste(sc,(int(el.x*z),int(el.y*z)))

    def _sel_box(self, z):
        el=self.sel_el; m=6
        if el.kind in ("text","sign"):
            w=len(el.text)*el.font_size*z*0.6; h=el.font_size*z*1.5
            self.canvas.create_rectangle(el.x*z+20-m,el.y*z+20-m,el.x*z+20+w+m,el.y*z+20+h+m,outline=self.S["accent"],width=2,dash=(4,2))
        else:
            self.canvas.create_rectangle(el.x*z+20-m,el.y*z+20-m,el.x2*z+20+m,el.y2*z+20+m,outline=self.S["accent"],width=2,dash=(4,2))

    def _update_nav(self):
        tab=self._tab()
        if tab:
            self.page_lbl.config(text=f"{tab.page_idx+1} {T['page_of']} {tab.total_pages}")
            self.zoom_lbl.config(text=f"{int(tab.zoom*100)}%")
        else:
            self.page_lbl.config(text="- / -"); self.zoom_lbl.config(text="--")

    def _update_layers(self):
        self.layers_list.delete(0,tk.END)
        tab=self._tab()
        if not tab: return
        icons={"text":"T","sign":"S","pen":"P","eraser":"E","line":"L",
               "arrow":"A","rect":"R","ellipse":"O","highlight":"H",
               "whiteout":"W","region_img":"Z"}
        for el in reversed(tab.page_els()):
            icon=icons.get(el.kind,"?")
            name=el.text[:10] if el.text else el.kind
            mark=">> " if el==self.sel_el else "   "
            self.layers_list.insert(tk.END,f"{mark}{icon} {name}")

    # ══ ניווט ══════════════════════════════════════

    def prev_page(self):
        tab=self._tab()
        if tab and tab.page_idx>0:
            tab.page_idx-=1; self.sel_el=None; self._refresh_pages(); self._render()

    def next_page(self):
        tab=self._tab()
        if tab and tab.page_idx<tab.total_pages-1:
            tab.page_idx+=1; self.sel_el=None; self._refresh_pages(); self._render()

    def _on_page_sel(self,_e):
        tab=self._tab(); sel=self.pages_list.curselection()
        if tab and sel: tab.page_idx=sel[0]; self.sel_el=None; self._render()

    def zoom_in(self):
        tab=self._tab()
        if tab: tab.zoom=min(tab.zoom+0.25,5.0); self._render()

    def zoom_out(self):
        tab=self._tab()
        if tab: tab.zoom=max(tab.zoom-0.25,0.25); self._render()

    def _wheel(self,event):
        if event.delta>0: self.zoom_in()
        else: self.zoom_out()

    # ══ כלים ══════════════════════════════════════

    def set_mode(self, mode):
        self.edit_mode=mode
        if mode!="region": self.region_rect=None
        cursors={"region":"crosshair","select":"arrow","text":"xterm","sign":"hand2",
                 "pen":"pencil","line":"crosshair","arrow":"crosshair","rect":"crosshair",
                 "ellipse":"crosshair","highlight":"crosshair","eraser":"X_cursor",
                 "whiteout":"crosshair","crop":"sizing"}
        hints={"region":"גרור לסמן אזור | Delete=מחק | גרור להזיז",
               "select":"לחץ לבחירה | גרור להזזה | לחיצה כפולה=עריכה",
               "text":"לחץ לקביעת מיקום הטקסט","sign":"לחץ לקביעת מיקום החתימה",
               "pen":"גרור לציור","line":"גרור לציור קו","arrow":"גרור לציור חץ",
               "rect":"גרור לציור מלבן","ellipse":"גרור לציור עיגול",
               "highlight":"גרור להדגשה","eraser":"גרור למחיקה",
               "whiteout":"גרור לכיסוי לבן","crop":"גרור לחיתוך עמוד"}
        if hasattr(self,"canvas"): self.canvas.config(cursor=cursors.get(mode,"crosshair"))
        if hasattr(self,"mode_lbl"): self.mode_lbl.config(text=hints.get(mode,""))
        if hasattr(self,"tool_btns"):
            for m,b in self.tool_btns.items():
                b.config(style="ActiveTool.TButton" if m==mode else "Tool.TButton")

    def pick_color(self):
        c=colorchooser.askcolor(color=self.draw_color,title="בחר צבע")[1]
        if c:
            self.draw_color=c
            self.color_btn.config(bg=c)
            self.prop_color_btn.config(bg=c)

    # ══ עכבר ══════════════════════════════════════

    def _to_doc(self,cx,cy):
        tab=self._tab()
        if not tab: return 0.0,0.0
        return (cx-20)/tab.zoom,(cy-20)/tab.zoom

    def _press(self,event):
        self.mouse_start=(event.x,event.y); self.pen_pts=[(event.x,event.y)]; self.is_drag=False
        tab=self._tab()
        if not tab: return
        dx,dy=self._to_doc(event.x,event.y)
        if self.edit_mode=="region":
            if self.region_rect:
                rx,ry,rx2,ry2=self.region_rect
                if rx<=dx<=rx2 and ry<=dy<=ry2:
                    self.region_doff=(dx-rx,dy-ry); self.region_moved=True; return
            self.region_rect=None; self.region_moved=False
        elif self.edit_mode=="select":
            self._try_sel(dx,dy)
            if self.sel_el: self.drag_off=(dx-self.sel_el.x,dy-self.sel_el.y)
        elif self.edit_mode=="text":  self._do_text(dx,dy)
        elif self.edit_mode=="sign":  self._do_sign(dx,dy)

    def _drag_ev(self,event):
        if not self.mouse_start: return
        tab=self._tab()
        if not tab: return
        self.is_drag=True
        dx,dy=self._to_doc(event.x,event.y); x0,y0=self.mouse_start
        if self.edit_mode=="region" and self.region_moved and self.region_rect:
            rx,ry,rx2,ry2=self.region_rect; w=rx2-rx; h=ry2-ry
            nx=dx-self.region_doff[0]; ny=dy-self.region_doff[1]
            self.region_rect=(nx,ny,nx+w,ny+h)
            els=[e for e in tab.page_els() if e.kind=="region_img"]
            if els: e=els[-1]; e.x=nx; e.y=ny; e.x2=nx+w; e.y2=ny+h
            self._render(); return
        if self.edit_mode=="select" and self.sel_el:
            w=self.sel_el.x2-self.sel_el.x; h=self.sel_el.y2-self.sel_el.y
            self.sel_el.x=dx-self.drag_off[0]; self.sel_el.y=dy-self.drag_off[1]
            self.sel_el.x2=self.sel_el.x+w; self.sel_el.y2=self.sel_el.y+h
            tab.modified=True; self._render(); return
        if self.temp_id: self.canvas.delete(self.temp_id)
        if self.edit_mode=="region":
            self.temp_id=self.canvas.create_rectangle(x0,y0,event.x,event.y,outline="#2980b9",width=2,dash=(6,3))
        elif self.edit_mode=="pen":
            self.pen_pts.append((event.x,event.y))
            if len(self.pen_pts)>=2:
                flat=[c for p in self.pen_pts for c in p]
                self.temp_id=self.canvas.create_line(*flat,fill=self.draw_color,width=self.size_var.get(),smooth=True)
        elif self.edit_mode=="eraser": self.pen_pts.append((event.x,event.y))
        elif self.edit_mode=="line":
            self.temp_id=self.canvas.create_line(x0,y0,event.x,event.y,fill=self.draw_color,width=self.size_var.get())
        elif self.edit_mode=="arrow":
            self.temp_id=self.canvas.create_line(x0,y0,event.x,event.y,fill=self.draw_color,width=self.size_var.get(),arrow=tk.LAST)
        elif self.edit_mode=="rect":
            self.temp_id=self.canvas.create_rectangle(x0,y0,event.x,event.y,outline=self.draw_color,width=self.size_var.get())
        elif self.edit_mode=="ellipse":
            self.temp_id=self.canvas.create_oval(x0,y0,event.x,event.y,outline=self.draw_color,width=self.size_var.get())
        elif self.edit_mode in ("highlight","whiteout"):
            fill="#ffff00" if self.edit_mode=="highlight" else "#ffffff"
            self.temp_id=self.canvas.create_rectangle(x0,y0,event.x,event.y,fill=fill,outline="",stipple="gray25")
        elif self.edit_mode=="crop":
            self.temp_id=self.canvas.create_rectangle(x0,y0,event.x,event.y,outline=self.S["accent"],width=2,dash=(6,3))

    def _release(self,event):
        if not self.mouse_start: return
        tab=self._tab()
        if not tab: self.mouse_start=None; return
        if self.temp_id: self.canvas.delete(self.temp_id); self.temp_id=None
        x0,y0=self.mouse_start; dx0,dy0=self._to_doc(x0,y0); dx1,dy1=self._to_doc(event.x,event.y)
        if self.edit_mode=="region" and self.region_moved:
            self.region_moved=False; self.mouse_start=None; return
        if self.edit_mode=="select" and self.sel_el and self.is_drag:
            tab.modified=True; self.mouse_start=None; self.is_drag=False; return
        if not self.is_drag and self.edit_mode not in ("text","sign","select","region"):
            self.mouse_start=None; return
        def add(el):
            el.page=tab.page_idx; tab.push_undo()
            tab.elements.append(el); tab.modified=True; self.sel_el=el; self._render()
        if self.edit_mode=="region" and self.is_drag:
            rx=min(dx0,dx1); ry=min(dy0,dy1); rx2=max(dx0,dx1); ry2=max(dy0,dy1)
            if rx2-rx>5 and ry2-ry>5:
                base=tab.base_image()
                if base:
                    z=tab.zoom; rp=base.crop((int(rx*z),int(ry*z),int(rx2*z),int(ry2*z)))
                    self.region_rect=(rx,ry,rx2,ry2); tab.push_undo()
                    ew=Element("whiteout",x=rx,y=ry,x2=rx2,y2=ry2,page=tab.page_idx); tab.elements.append(ew)
                    ei=Element("region_img",x=rx,y=ry,x2=rx2,y2=ry2,page=tab.page_idx); ei.pil_img=rp; tab.elements.append(ei)
                    tab.modified=True; self.sel_el=ei; self._render()
        elif self.edit_mode=="pen":
            pts=[self._to_doc(px,py) for px,py in self.pen_pts]
            if len(pts)>=2: add(Element("pen",x=pts[0][0],y=pts[0][1],color=self.draw_color,size=self.size_var.get(),points=pts))
        elif self.edit_mode=="eraser":
            pts=[self._to_doc(px,py) for px,py in self.pen_pts]
            if len(pts)>=2: add(Element("eraser",size=self.size_var.get(),points=pts))
        elif self.edit_mode=="line":   add(Element("line",x=dx0,y=dy0,x2=dx1,y2=dy1,color=self.draw_color,size=self.size_var.get()))
        elif self.edit_mode=="arrow":  add(Element("arrow",x=dx0,y=dy0,x2=dx1,y2=dy1,color=self.draw_color,size=self.size_var.get()))
        elif self.edit_mode=="rect":   add(Element("rect",x=min(dx0,dx1),y=min(dy0,dy1),x2=max(dx0,dx1),y2=max(dy0,dy1),color=self.draw_color,size=self.size_var.get()))
        elif self.edit_mode=="ellipse":add(Element("ellipse",x=min(dx0,dx1),y=min(dy0,dy1),x2=max(dx0,dx1),y2=max(dy0,dy1),color=self.draw_color,size=self.size_var.get()))
        elif self.edit_mode=="highlight":add(Element("highlight",x=min(dx0,dx1),y=min(dy0,dy1),x2=max(dx0,dx1),y2=max(dy0,dy1)))
        elif self.edit_mode=="whiteout": add(Element("whiteout",x=min(dx0,dx1),y=min(dy0,dy1),x2=max(dx0,dx1),y2=max(dy0,dy1)))
        elif self.edit_mode=="crop" and tab.is_pdf:
            tab.doc[tab.page_idx].set_cropbox(fitz.Rect(min(dx0,dx1),min(dy0,dy1),max(dx0,dx1),max(dy0,dy1)))
            tab.modified=True; self._render()
        self.mouse_start=None; self.is_drag=False

    def _dbl(self,event):
        if self.edit_mode!="select" or not self.sel_el: return
        if self.sel_el.kind not in ("text","sign"): return
        tab=self._tab()
        new=simpledialog.askstring("עריכה",T["enter_text"],initialvalue=self.sel_el.text)
        if new is not None:
            tab.push_undo(); self.sel_el.text=new; tab.modified=True; self._render()

    def _cancel_region(self):
        self.region_rect=None; self._render()

    def _try_sel(self,dx,dy):
        tab=self._tab()
        if not tab: self.sel_el=None; return
        for el in reversed(tab.page_els()):
            if el.visible and self._hit(el,dx,dy):
                self.sel_el=el; self._render(); return
        self.sel_el=None; self._render()

    def _hit(self,el,dx,dy):
        m=max(8,el.size*2 if hasattr(el,"size") else 8)
        if el.kind in ("text","sign"):
            return el.x-m<=dx<=el.x+len(el.text)*el.font_size*0.6+m and el.y-m<=dy<=el.y+el.font_size*1.5+m
        return min(el.x,el.x2)-m<=dx<=max(el.x,el.x2)+m and min(el.y,el.y2)-m<=dy<=max(el.y,el.y2)+m

    # ══ עריכה ══════════════════════════════════════

    def _do_text(self,dx,dy):
        t=simpledialog.askstring("טקסט",T["enter_text"])
        if not t: return
        tab=self._tab(); tab.push_undo()
        el=Element("text",x=dx,y=dy,text=t,color=self.draw_color,font_size=self.prop_sz.get())
        el.page=tab.page_idx; tab.elements.append(el); tab.modified=True; self.sel_el=el; self._render()

    def _do_sign(self,dx,dy):
        n=simpledialog.askstring("חתימה",T["enter_sign"])
        if not n: return
        tab=self._tab(); tab.push_undo()
        el=Element("sign",x=dx,y=dy,text=f"* {n}",font_size=self.prop_sz.get())
        el.page=tab.page_idx; tab.elements.append(el); tab.modified=True; self.sel_el=el; self._render()

    def undo(self):
        tab=self._tab()
        if tab and tab.undo(): self.sel_el=None; self._render()

    def redo(self):
        tab=self._tab()
        if tab and tab.redo(): self.sel_el=None; self._render()

    def copy_el(self):
        if self.sel_el: self.clipboard=self.sel_el.clone()

    def paste_el(self):
        if not self.clipboard: return
        tab=self._tab()
        if not tab: return
        tab.push_undo(); new=self.clipboard.clone(); new.page=tab.page_idx
        tab.elements.append(new); self.sel_el=new; tab.modified=True; self._render()

    def cut_el(self):
        self.copy_el(); self.delete_sel()

    def delete_sel(self):
        tab=self._tab()
        if not tab: return
        if self.edit_mode=="region" and self.region_rect:
            els=[e for e in tab.page_els() if e.kind in ("whiteout","region_img")]
            if els:
                tab.push_undo()
                for e in els: tab.elements.remove(e)
                tab.modified=True
            self.region_rect=None; self._render(); return
        if not self.sel_el: return
        tab.push_undo(); tab.elements.remove(self.sel_el)
        self.sel_el=None; tab.modified=True; self._render()

    def layer_up(self):
        tab=self._tab()
        if not tab or not self.sel_el: return
        els=tab.elements; i=els.index(self.sel_el)
        if i<len(els)-1: els[i],els[i+1]=els[i+1],els[i]; self._render()

    def layer_dn(self):
        tab=self._tab()
        if not tab or not self.sel_el: return
        els=tab.elements; i=els.index(self.sel_el)
        if i>0: els[i],els[i-1]=els[i-1],els[i]; self._render()

    def _on_layer_sel(self,_e):
        tab=self._tab()
        if not tab: return
        sel=self.layers_list.curselection()
        if not sel: return
        els=list(reversed(tab.page_els()))
        if sel[0]<len(els): self.sel_el=els[sel[0]]; self._render()

    # ══ שמירה ══════════════════════════════════════

    def save_file(self):
        tab=self._tab()
        if not tab: messagebox.showwarning("",T["no_file"]); return
        if tab.path: self._save(tab,tab.path)
        else: self.save_as()

    def save_as(self):
        tab=self._tab()
        if not tab: messagebox.showwarning("",T["no_file"]); return
        ext=".pdf" if tab.is_pdf else tab.ext
        path=filedialog.asksaveasfilename(defaultextension=ext,
            filetypes=[("PDF","*.pdf"),("PNG","*.png"),("JPG","*.jpg")])
        if path: self._save(tab,path)

    def _save(self,tab,path):
        try:
            self.status_var.set(T["saving"]); self.root.update_idletasks()
            self._flatten(tab,path); tab.path=path; tab.modified=False
            messagebox.showinfo("שמירה",T["saved_ok"])
        except Exception as e:
            messagebox.showerror("שגיאה",str(e))
        finally:
            self.status_var.set(T["ready"])

    def _flatten(self,tab,path):
        if tab.is_pdf and tab.doc:
            for pi in range(tab.total_pages):
                p_els=[e for e in tab.elements if e.page==pi]
                if p_els:
                    page=tab.doc[pi]
                    for el in p_els: self._embed(page,el)
            tmp=path+".tmp"; tab.doc.save(tmp); os.replace(tmp,path)
        else:
            old_z=tab.zoom; tab.zoom=2.0; img=tab.base_image()
            drw=ImageDraw.Draw(img,"RGBA")
            for el in tab.page_els(): self._draw_el(drw,el,tab.zoom,img)
            tab.zoom=old_z; img.convert("RGB").save(path)

    def _embed(self,page,el):
        c=self._hex_rgb(el.color or "#000000")
        if el.kind=="text":
            page.insert_text((el.x,el.y),el.text,fontsize=el.font_size,color=c)
        elif el.kind=="sign":
            page.insert_text((el.x,el.y),el.text,fontsize=el.font_size,color=(0.1,0.34,0.86))
            page.draw_line((el.x,el.y+el.font_size+2),(el.x+len(el.text)*el.font_size*0.55,el.y+el.font_size+2),color=(0.1,0.34,0.86),width=1)
        elif el.kind=="line":   page.draw_line((el.x,el.y),(el.x2,el.y2),color=c,width=el.size)
        elif el.kind=="arrow":
            page.draw_line((el.x,el.y),(el.x2,el.y2),color=c,width=el.size)
            page.draw_circle((el.x2,el.y2),el.size*2,color=c,fill=c)
        elif el.kind=="rect":      page.draw_rect(fitz.Rect(el.x,el.y,el.x2,el.y2),color=c,width=el.size)
        elif el.kind=="ellipse":   page.draw_oval(fitz.Rect(el.x,el.y,el.x2,el.y2),color=c,width=el.size)
        elif el.kind=="highlight": page.draw_rect(fitz.Rect(el.x,el.y,el.x2,el.y2),color=None,fill=(1,1,0),fill_opacity=0.3)
        elif el.kind in ("whiteout","eraser"): page.draw_rect(fitz.Rect(el.x,el.y,el.x2,el.y2),color=None,fill=(1,1,1))
        elif el.kind=="pen" and el.points:
            for i in range(len(el.points)-1): page.draw_line(el.points[i],el.points[i+1],color=c,width=el.size)
        elif el.kind=="region_img" and el.pil_img:
            buf=io.BytesIO(); el.pil_img.convert("RGB").save(buf,format="PNG")
            page.insert_image(fitz.Rect(el.x,el.y,el.x2,el.y2),stream=buf.getvalue())

    # ══ עמודים ════════════════════════════════════

    def rotate_r(self):
        tab=self._tab()
        if not tab or not tab.is_pdf: return
        tab.doc[tab.page_idx].set_rotation((tab.doc[tab.page_idx].rotation+90)%360)
        tab.modified=True; self._render()

    def rotate_l(self):
        tab=self._tab()
        if not tab or not tab.is_pdf: return
        tab.doc[tab.page_idx].set_rotation((tab.doc[tab.page_idx].rotation-90)%360)
        tab.modified=True; self._render()

    def delete_page(self):
        tab=self._tab()
        if not tab or not tab.is_pdf: return
        if tab.total_pages<=1: messagebox.showwarning("","לא ניתן למחוק עמוד יחיד"); return
        if messagebox.askyesno("מחיקה","למחוק עמוד זה?"):
            tab.doc.delete_page(tab.page_idx); tab.total_pages-=1
            tab.page_idx=min(tab.page_idx,tab.total_pages-1); tab.modified=True
            self._refresh_pages(); self._render()

    def images_to_pdf(self):
        files=filedialog.askopenfilenames(filetypes=[("תמונות","*.jpg *.jpeg *.png *.tiff *.bmp")])
        if not files: return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
        if not path: return
        try:
            doc=fitz.open()
            for f in files:
                img=Image.open(f).convert("RGB"); buf=io.BytesIO()
                img.save(buf,format="PDF"); d=fitz.open("pdf",buf.getvalue()); doc.insert_pdf(d)
            doc.save(path); doc.close()
            messagebox.showinfo("הצלחה","תמונות הומרו ל-PDF"); self._load(path)
        except Exception as e: messagebox.showerror("שגיאה",str(e))

    # ══ בונה קבצים ════════════════════════════════

    def open_builder(self):
        S=self.S; win=tk.Toplevel(self.root)
        win.title(T["builder_title"]); win.geometry("1100x620")
        win.configure(bg=S["panel_bg"]); win.grab_set()
        tk.Label(win,text=T["builder_title"],bg=S["accent"],fg=S["btn_fg"],
                 font=(S["font_family"],13,"bold"),pady=8,anchor=tk.E,padx=16).pack(fill=tk.X)
        main=tk.Frame(win,bg=S["panel_bg"]); main.pack(fill=tk.BOTH,expand=True,padx=8,pady=8)
        sf=tk.Frame(main,bg=S["panel_bg"],relief=tk.GROOVE,bd=1)
        sf.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True,padx=4)
        tk.Label(sf,text=T["builder_src"],bg=S["toolbar_bg"],fg=S["toolbar_fg"],
                 font=(S["font_family"],10,"bold"),pady=4,anchor=tk.E,padx=8).pack(fill=tk.X)
        src_data=[]
        ttk.Button(sf,text=T["builder_open"],style="Blue.TButton",
                   command=lambda:self._builder_open(src_list,src_data)
                   ).pack(fill=tk.X,padx=4,pady=4)
        src_list=tk.Listbox(sf,bg="#ffffff",fg="#1a1a1a",
                             selectbackground=S["accent2"],selectforeground=S["btn_fg"],
                             font=(S["font_family"],10),selectmode=tk.EXTENDED,
                             bd=0,highlightthickness=0)
        src_list.pack(fill=tk.BOTH,expand=True,padx=4,pady=4)
        mid=tk.Frame(main,bg=S["panel_bg"],width=110)
        mid.pack(side=tk.RIGHT,fill=tk.Y,padx=4); mid.pack_propagate(False)
        tk.Frame(mid,bg=S["panel_bg"]).pack(expand=True)
        dst_ref=[None]
        def add_p():
            for i in src_list.curselection():
                if i<len(src_data): dst_data.append(src_data[i]); dst_ref[0].insert(tk.END,src_data[i][2])
            upd_prev()
        def rem_p():
            for i in list(dst_ref[0].curselection())[::-1]: dst_ref[0].delete(i); dst_data.pop(i)
            upd_prev()
        def mv_u():
            sel=dst_ref[0].curselection()
            if not sel or sel[0]==0: return
            i=sel[0]; dst_data[i],dst_data[i-1]=dst_data[i-1],dst_data[i]
            lt=dst_ref[0].get(i); dst_ref[0].delete(i); dst_ref[0].insert(i-1,lt); dst_ref[0].selection_set(i-1); upd_prev()
        def mv_d():
            sel=dst_ref[0].curselection()
            if not sel or sel[0]>=dst_ref[0].size()-1: return
            i=sel[0]; dst_data[i],dst_data[i+1]=dst_data[i+1],dst_data[i]
            lt=dst_ref[0].get(i); dst_ref[0].delete(i); dst_ref[0].insert(i+1,lt); dst_ref[0].selection_set(i+1); upd_prev()
        for lt,cmd in [(T["builder_add"],add_p),(T["builder_rem"],rem_p),(T["builder_up"],mv_u),(T["builder_dn"],mv_d)]:
            ttk.Button(mid,text=lt,command=cmd,style="Dark.TButton").pack(pady=4,fill=tk.X,padx=4)
        tk.Frame(mid,bg=S["panel_bg"]).pack(expand=True)
        df=tk.Frame(main,bg=S["panel_bg"],relief=tk.GROOVE,bd=1)
        df.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True,padx=4)
        tk.Label(df,text=T["builder_dst"],bg=S["toolbar_bg"],fg=S["toolbar_fg"],
                 font=(S["font_family"],10,"bold"),pady=4,anchor=tk.E,padx=8).pack(fill=tk.X)
        dst_data=[]
        dst_list=tk.Listbox(df,bg="#ffffff",fg="#1a1a1a",
                             selectbackground=S["accent"],selectforeground=S["btn_fg"],
                             font=(S["font_family"],10),bd=0,highlightthickness=0)
        dst_list.pack(fill=tk.BOTH,expand=True,padx=4,pady=4); dst_ref[0]=dst_list
        dst_list.bind("<<ListboxSelect>>",lambda e:upd_prev())
        pf=tk.Frame(main,bg=S["panel_bg"],relief=tk.GROOVE,bd=1,width=220)
        pf.pack(side=tk.RIGHT,fill=tk.Y,padx=4); pf.pack_propagate(False)
        tk.Label(pf,text=T["builder_prev"],bg=S["toolbar_bg"],fg=S["toolbar_fg"],
                 font=(S["font_family"],10,"bold"),pady=4,anchor=tk.CENTER).pack(fill=tk.X)
        self.bprev_lbl=tk.Label(pf,text="",bg=S["panel_bg"],fg=S["panel_fg"],font=(S["font_family"],9),pady=2)
        self.bprev_lbl.pack(fill=tk.X,padx=4)
        self.bprev_canvas=tk.Label(pf,bg="#cccccc",relief=tk.SUNKEN,bd=1)
        self.bprev_canvas.pack(fill=tk.BOTH,expand=True,padx=6,pady=6)
        self.bprev_photo=None
        def upd_prev():
            sel=dst_ref[0].curselection()
            if not sel or sel[0]>=len(dst_data):
                self.bprev_canvas.config(image="",text="בחר עמוד לתצוגה",fg="#1a1a1a",font=(S["font_family"],10)); self.bprev_lbl.config(text=""); return
            doc,pidx,lt=dst_data[sel[0]]
            try:
                page=doc[pidx]; mat=fitz.Matrix(0.6,0.6); pix=page.get_pixmap(matrix=mat)
                img=Image.open(io.BytesIO(pix.tobytes("ppm"))); img.thumbnail((200,260),Image.LANCZOS)
                self.bprev_photo=ImageTk.PhotoImage(img)
                self.bprev_canvas.config(image=self.bprev_photo,text=""); self.bprev_lbl.config(text=lt)
            except Exception as ex: self.bprev_canvas.config(image="",text=f"שגיאה: {ex}",fg="#1a1a1a")
        tab=self._tab()
        if tab and tab.is_pdf:
            for i in range(tab.total_pages):
                lt=f"{tab.name} | עמוד {i+1}"; src_data.append((tab.doc,i,lt)); src_list.insert(tk.END,lt)
        bf=tk.Frame(win,bg=S["panel_bg"]); bf.pack(fill=tk.X,padx=8,pady=8)
        def save_new():
            if not dst_data: messagebox.showwarning("","אין עמודים"); return
            path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
            if not path: return
            try:
                new=fitz.open()
                for doc,pidx,_ in dst_data: new.insert_pdf(doc,from_page=pidx,to_page=pidx)
                new.save(path); new.close(); messagebox.showinfo("הצלחה",T["saved_ok"]); win.destroy(); self._load(path)
            except Exception as e: messagebox.showerror("שגיאה",str(e))
        ttk.Button(bf,text=T["builder_save"],command=save_new,style="Green.TButton").pack(side=tk.LEFT,padx=4)
        ttk.Button(bf,text=T["cancel"],command=win.destroy,style="Dark.TButton").pack(side=tk.LEFT,padx=4)
        ttk.Button(bf,text=T["builder_clear"],command=lambda:[dst_data.clear(),dst_list.delete(0,tk.END)],style="Dark.TButton").pack(side=tk.LEFT,padx=4)

    def _builder_open(self,src_list,src_data):
        S=self.S
        paths=filedialog.askopenfilenames(filetypes=[("PDF","*.pdf")])
        for path in paths:
            try:
                doc=fitz.open(path); name=os.path.basename(path)
                for i in range(len(doc)):
                    lt=f"{name} | עמוד {i+1}"; src_data.append((doc,i,lt)); src_list.insert(tk.END,lt)
            except Exception as e: messagebox.showerror("שגיאה",str(e))

    # ══ עריכת כיתובים ══════════════════════════════

    def edit_labels(self):
        S=self.S; win=tk.Toplevel(self.root)
        win.title(T["edit_labels"]); win.geometry("540x560")
        win.configure(bg=S["panel_bg"]); win.grab_set()
        tk.Label(win,text=T["edit_labels"],bg=S["accent"],fg=S["btn_fg"],
                 font=(S["font_family"],11,"bold"),pady=6).pack(fill=tk.X)
        cont=tk.Frame(win,bg=S["panel_bg"]); cont.pack(fill=tk.BOTH,expand=True,padx=8)
        cv=tk.Canvas(cont,bg=S["panel_bg"],highlightthickness=0)
        sb=ttk.Scrollbar(cont,orient=tk.VERTICAL,command=cv.yview)
        inner=tk.Frame(cv,bg=S["panel_bg"])
        inner.bind("<Configure>",lambda e:cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0),window=inner,anchor="nw"); cv.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT,fill=tk.Y); cv.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        entries={}
        for key,val in T.items():
            row=tk.Frame(inner,bg=S["panel_bg"]); row.pack(fill=tk.X,padx=6,pady=2)
            tk.Label(row,text=key,width=18,anchor=tk.W,bg=S["panel_bg"],fg=S["panel_fg"],font=("Courier",9)).pack(side=tk.LEFT)
            e=tk.Entry(row,bg="#ffffff",fg="#1a1a1a",relief=tk.GROOVE,font=(S["font_family"],10))
            e.insert(0,val); e.pack(side=tk.LEFT,fill=tk.X,expand=True); entries[key]=e
        def apply():
            for k,e in entries.items(): T[k]=e.get()
            win.destroy(); messagebox.showinfo("","כיתובים עודכנו!")
        bf=tk.Frame(win,bg=S["panel_bg"]); bf.pack(pady=8)
        ttk.Button(bf,text=T["save_labels"],command=apply,style="Red.TButton").pack(side=tk.LEFT,padx=6)
        ttk.Button(bf,text=T["cancel"],command=win.destroy,style="Dark.TButton").pack(side=tk.LEFT,padx=6)

    def _hex_rgb(self,h):
        h=h.lstrip("#"); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))


if __name__ == "__main__":
    root = tk.Tk()
    DocEditor(root)
    root.mainloop()
