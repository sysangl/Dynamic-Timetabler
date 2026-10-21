import tkinter as tk
from tkinter import ttk
from helpers.paths import resource_path
from helpers.config import get_config, write_config, _deep_merge
import toml
from run import run_server

HEADING_FONT = (resource_path('static/fonts/Aleo/static/Aleo-Regular.ttf'),32)
SUBHEADING_FONT = (resource_path('static/fonts/Aleo/static/Aleo-Regular.ttf'),18)
original_config = get_config(True)


def finalise_settings(config:dict, controller):
    current_config = original_config
    new_config = _deep_merge(current_config, config)
    write_config(new_config)
    
    controller.show_frame(FinalisePage)

def finalise_installation(controller, run: bool = True):
    controller.destroy()
    run_server()


class installerApp(tk.Tk):
    def __init__(self, screenName: str | None = None, baseName: str | None = None, className: str = 'Tk', useTk: bool = True, sync: bool = False, use: str | None = None) -> None:
        super().__init__(screenName, baseName, className, useTk, sync, use)
        container = tk.Frame(self)
        container.pack(side='top',fill='both',expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for FRAME in (StartPage, ModeSelectPage, FolderSelectPage,SettingsPage,FinalisePage):
            frame = FRAME(container, self)
            self.frames[FRAME] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(StartPage)

    def show_frame(self, container):
        frame=self.frames[container]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text='Canopy Suite', font=HEADING_FONT)
        label.pack(anchor='n',pady=20)

        start_btn = ttk.Button(self, text='Start', command=lambda:controller.show_frame(ModeSelectPage))
        start_btn.pack(anchor='se', padx=20)

class ModeSelectPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text='Select Installation Mode', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)


        installation_modes = ['Portable', 'User Install']

        installation_mode = tk.StringVar(self, 'portable')
        r1=tk.Radiobutton(
            self,
            text='Portable (Only creates the data folder. The program runs from this executable)',
            variable=installation_mode,
            indicatoron=True,
            value='portable',
        )
        r1.pack(anchor='w', padx=20, pady=5)

        r2 = tk.Radiobutton(
            self,
            text='User Installation (Installs the program to a folder. Creates a shortcut.)',
            variable=installation_mode,
            indicatoron=False,
            value='user_install',
        )
        r2.pack(anchor='w', padx=20, pady=5)
        r2['state'] = 'disabled'


        back_btn = ttk.Button(self, text='Back', command=lambda:controller.show_frame(StartPage))
        back_btn.pack(anchor='sw',padx=20)
        next_btn = ttk.Button(self, text='Next', command=lambda:controller.show_frame(FolderSelectPage))
        next_btn.pack(anchor='se', padx=20)

class FolderSelectPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text='Select Installation Folder', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)
        label = ttk.Label(self, text='SKIP FOR NOW', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)

        back_btn = ttk.Button(self, text='Back', command=lambda:controller.show_frame(ModeSelectPage))
        back_btn.pack(anchor='sw',padx=20)
        next_btn = ttk.Button(self, text='Next', command=lambda:controller.show_frame(SettingsPage))
        next_btn.pack(anchor='se', padx=20)

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.widgets = {}
        label = ttk.Label(self, text='Settings', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scroll_frame = ttk.Frame(canvas)
        scroll_bar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        scroll_bar.pack(side='right', fill='y')

        canvas.configure(yscrollcommand=scroll_bar.set)
        canvas.pack(side='left',fill='both',expand=True)
        canvas.create_window((0,0), window=self.scroll_frame, anchor='w')

        self.scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))


        config = original_config
        row = 0
        self.build_widgets(config,row)

        back_btn = ttk.Button(self, text='Back', command=lambda:controller.show_frame(FolderSelectPage))
        back_btn.pack(anchor='sw',padx=20)
        next_btn = ttk.Button(self, text='Next', command=self.finalise_settings)
        next_btn.pack(anchor='se', padx=20)

    def build_widgets(self, config, row, prefix="")->int:
        for key,value in config.items():
            if isinstance(value, dict):
                row += 1
                label = tk.Label(self.scroll_frame, text=(prefix+key).replace('.', ' ').title(), font=SUBHEADING_FONT)
                label.grid(row=row, column=1, sticky='w', padx=10, pady=5)
                row += 1
                row = self.build_widgets(value, row, prefix=prefix+key+'.')
            else:
                ttk.Label(self.scroll_frame, text=key).grid(row=row, column=0, sticky='w', padx=10, pady=5)
            if isinstance(value, bool): # type: ignore
                var = tk.BooleanVar(value=value)
                check_btn = ttk.Checkbutton(self.scroll_frame, variable=var)
                check_btn.grid(row=row, column=1, sticky='e', padx=10)
                self.widgets[prefix+key] = (check_btn, var) # type: ignore
            elif isinstance(value, int): # type: ignore
                var = tk.IntVar(value=value)
                int_entry = ttk.Spinbox(self.scroll_frame, textvariable=var, from_=0, to=65535)
                int_entry.grid(row=row, column=1, sticky='e', padx=10)
                self.widgets[prefix+key] = (int_entry, var) # type: ignore
            elif isinstance(value, str):
                var = tk.StringVar(value=str(value)) # type: ignore
                entry = ttk.Entry(self.scroll_frame, textvariable=var, width=40)
                entry.grid(row=row, column=1, sticky='e',padx=10)
                self.widgets[prefix+key] = (entry, var) # type: ignore

            row += 1
        return row

    def finalise_settings(self):
        edited_config = {}
        for key, (widget, var) in self.widgets.items():
            raw_var = var.get()
            orig_var = original_config.get(key)
            if isinstance(orig_var, bool):
                edited_config[key] = bool(raw_var)
            elif isinstance(orig_var, int):
                edited_config[key] = int(raw_var)
            elif isinstance(orig_var, float):
                edited_config[key] = float(raw_var)
            else:
                edited_config[key] = raw_var

        finalise_settings(edited_config, self.controller)


class FinalisePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text='Finished Setup', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)
        ttk.Label(self,
            text=(
                "Your configuration has been saved.\n"
                "Click 'Finish' to close the installer."
            ),
            justify="center",
        ).pack(anchor="center", pady=10)

        run_var = tk.BooleanVar(value=True)
        run_check = tk.Checkbutton(self, variable=run_var, text="Run program on exit?")
        run_check.pack(anchor="center", pady=10)

        
        back_btn = ttk.Button(self, text='Back', command=lambda:controller.show_frame(SettingsPage))
        back_btn.pack(anchor='sw',padx=20)
        next_btn = ttk.Button(self, text='Finish', command=lambda:finalise_installation(controller, run_var.get()))
        next_btn.pack(anchor='se', padx=20)


app = installerApp()
app.title('Canopy Installer')
app.minsize(700,500)
app.maxsize(700,500)
app.resizable(False,False)
app.geometry('700x700+50+50')
app.mainloop()