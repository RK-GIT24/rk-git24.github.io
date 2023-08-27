import os
from pathlib import Path
from os import name
import platform
from tkinter import filedialog, messagebox, StringVar, BooleanVar
from tkinter.ttk import (
    Entry,
    Button,
    Labelframe,
    Frame,
    Checkbutton,
    Treeview,
    Scrollbar,
    Combobox,
    Style,
)
from tkinter import font, END, Listbox, Text, Tk, BOTH, X
import re
import ctypes
from mimetypes import init, guess_type

FONT_SIZE = 16

if name == "nt":
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    FONT_SIZE = 11

init()
COLORS = {
    "slate400": "#94a3b8",
    "red600": "#dc2626",
    "amber400": "#fbbf24",
    "emerald500": "#10b981",
    "sky500": "#0ea5e9",
}

"""
color schemes for file types
music -> emerald500
"""


class RenameTool:
    def __init__(self, title) -> None:
        self.__WINDOW = Tk()
        self.__WINDOW.title(title)
        self.__WINDOW.geometry("1000x800")
        self.__WINDOW.tk.call("source", "azure.tcl")
        self.__WINDOW.tk.call("set_theme", "dark")
        new_font = font.nametofont("TkDefaultFont")
        new_font.configure(family="Consolas", size=FONT_SIZE)
        self.__WINDOW.option_add("*Font", new_font)
        self.__WINDOW.columnconfigure(0, weight=1, uniform="horz")
        self.__WINDOW.columnconfigure(1, weight=1, uniform="horz")
        self.__WINDOW.rowconfigure(0, weight=1, uniform="horz")

        self.field_frame = Frame(self.__WINDOW, name="field_frame", relief="solid")
        self.visual_frame = Frame(self.__WINDOW, name="visual_frame", relief="solid")
        self.field_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.visual_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.field_frame.columnconfigure(0, weight=1, uniform="horz")
        self.__file_names = []
        self.visual_frame.columnconfigure(0, weight=1, uniform="vert")
        self.visual_frame.rowconfigure(0, weight=1, uniform="vert")
        self.visual_frame.rowconfigure(1, weight=1, uniform="vert")

        self.label_frames: dict[str, Labelframe] = {}
        self.__str_vars: dict[str, StringVar] = {
            "path": StringVar(),
            "filter": StringVar(),
        }
        self._file_list: Treeview
        self.__bool_vars: dict[str, BooleanVar] = {
            "use_filter_regex": BooleanVar(value=False),
            "use_rename_regex": BooleanVar(value=False),
        }

    def __create_gui(self):
        # path --------------------
        self.label_frames["path"] = Labelframe(self.field_frame, text="Path")
        path_entry = Entry(
            self.label_frames["path"],
            textvariable=self.__str_vars["path"],
            foreground="#cbd5e1",
        )
        path_entry.bind("<1>", lambda _: self.__browse())
        path_entry.config(state="disabled")
        path_entry.pack(padx=10, pady=5, expand=1, fill=X)
        self.confirm_btn = Button(
            self.label_frames["path"], text="Confirm", command=self.on_path_confirm
        )
        self.confirm_btn.config(state="disabled")
        self.confirm_btn.pack(padx=10, pady=5, anchor="se", side="right")
        self.label_frames["path"].grid(row=0, column=0, padx=10, pady=5, sticky="new")
        # path --------------------

        # filter --------------------
        self.label_frames["filter"] = Labelframe(self.field_frame, text="Filter")
        filter_entry = Entry(
            self.label_frames["filter"], textvariable=self.__str_vars["filter"]
        )
        filter_entry.pack(padx=10, pady=5, expand=1, fill=X)
        use_filter_reg = Checkbutton(
            self.label_frames["filter"],
            text="Use Regex",
            variable=self.__bool_vars["use_filter_regex"],
            command=self.on_use_regex,
        )
        use_filter_reg.pack(padx=10, pady=10, anchor="sw", side="left")
        apply_filter = Button(
            self.label_frames["filter"], text="Apply", command=self._apply_filter
        )
        apply_filter.pack(padx=10, pady=5, anchor="se")
        self.label_frames["filter"].grid(row=1, column=0, padx=10, pady=5, sticky="new")
        # filter --------------------
        # rename --------------------
        self.label_frames["rename"] = Labelframe(self.field_frame, text="Rename")
        new_name_entry = Entry(
            self.label_frames["rename"],
        )
        new_name_entry.pack(padx=10, pady=5, expand=1, fill=X)
        use_rename_reg = Checkbutton(
            self.label_frames["rename"],
            text="Use Regex",
            variable=self.__bool_vars["use_rename_regex"],
        )
        use_rename_reg.pack(padx=10, pady=10, anchor="sw", side="left")
        apply_rename = Button(
            self.label_frames["rename"],
            text="Apply",
        )
        apply_rename.pack(padx=10, pady=5, anchor="se")
        self.label_frames["rename"].grid(row=3, column=0, padx=10, pady=5, sticky="new")
        # rename --------------------
        # options --------------------
        self.label_frames["options"] = Labelframe(self.field_frame, text="Options")
        add_selected = Button(self.label_frames["options"], text="Preview")
        add_selected.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
        )
        rename_selected = Button(self.label_frames["options"], text="Rename")
        rename_selected.grid(
            row=0,
            column=1,
            padx=10,
            pady=10,
        )
        self.label_frames["options"].grid(
            row=4, column=0, padx=10, pady=5, sticky="new"
        )
        # options --------------------

        # trees ---------------------
        file_container = Frame(self.visual_frame, name="file_container")
        file_container.columnconfigure(0, weight=1, uniform="file_tree")
        file_container.rowconfigure(0, weight=1, uniform="file_tree")

        self._file_list = Treeview(
            file_container, columns=("file_names"), show="headings"
        )
        self._file_list.heading("file_names", text="File Name")

        tree_scroll = Scrollbar(file_container, orient="vertical")
        tree_scroll.config(command=self._file_list.yview)
        self._file_list.config(yscrollcommand=tree_scroll.set)

        # tags --------------------
        self._file_list.tag_configure("audio", foreground=COLORS["sky500"])
        # tags --------------------

        self._file_list.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="nse")
        file_container.grid(row=0, column=0, sticky="nsew")

        # renamed ------------------
        renamed_container = Frame(self.visual_frame, name="renamed_container")
        renamed_container.columnconfigure(0, weight=1, uniform="renamed_tree")
        renamed_container.rowconfigure(0, weight=1, uniform="renamed_tree")

        self._renamed_list = Treeview(
            renamed_container, columns=("new_names"), show="headings"
        )
        self._renamed_list.heading("new_names", text="New Names")
        self._renamed_list.grid(row=0, column=0, sticky="nsew")

        renamed_scroll = Scrollbar(renamed_container, orient="vertical")
        renamed_scroll.config(command=self._renamed_list.yview)
        self._renamed_list.config(yscrollcommand=renamed_scroll.set)

        # tags --------------------
        self._renamed_list.tag_configure("audio", foreground=COLORS["sky500"])
        # tags --------------------

        renamed_scroll.grid(row=0, column=1, sticky="nse")
        renamed_container.grid(row=1, column=0, sticky="nsew")

    def __browse(self):
        file_path = filedialog.askdirectory()
        if file_path != "":
            self.__str_vars["path"].set(file_path)
            self.confirm_btn.config(state="normal")
        else:
            self.confirm_btn.config(state="disabled")
            print("Cancelled")

    def on_use_regex(self):
        print(self.__bool_vars["use_filter_regex"].get())

    def _get_path_contents(self, path: str | Path):
        return os.listdir(path=path)

    def add_to_filelist(self, files_names: list[str]):
        self._file_list.delete(*self._file_list.get_children())
        for content in files_names:
            self._file_list.insert("", END, values=(content, ""), tags="audio")

    def _apply_filter(self):
        # print("yes")
        file_list = []
        filt_str = self.__str_vars["filter"].get()
        if self.__bool_vars["use_filter_regex"].get():
            filt_str_pat = re.compile(filt_str)
            file_list = list(
                filter(
                    lambda x: re.match(filt_str_pat, x) is not None, self.__file_names
                )
            )
        else:
            file_list = list(
                filter(lambda x: filt_str in x or filt_str == x, self.__file_names)
            )
        # print(file_list)
        self.add_to_filelist(file_list)

    def on_path_confirm(self):
        dir_path = self.__str_vars["path"].get()
        _path: Path = Path(dir_path)
        self.__file_names = self._get_path_contents(_path)
        self.add_to_filelist(self.__file_names)
        self.confirm_btn.config(state="disabled")

    def run(self):
        self.__create_gui()
        self.__WINDOW.mainloop()


if __name__ == "__main__":
    app = RenameTool(title="Rename Tool")
    app.run()
