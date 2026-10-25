import tkinter as tk
from tkinter import ttk, filedialog
from helpers.paths import resource_path
from helpers.config import get_config, write_config, _deep_merge, _get_data_dir, _set_data_dir
import toml
from run import run_server

ALEO = resource_path('static/fonts/Aleo/static/Aleo-Regular.ttf')
HEADING_FONT = (ALEO,28, 'bold')
SUBHEADING_FONT = (ALEO,22)
BTN_FONT = (ALEO, 18, 'bold')
TEXT_FONT = (ALEO, 14)
original_config = get_config(True)
BG_COLOUR = '#1e1e1e'
FG_COLOUR = '#e0e0e0'
ACCENT = '#a0e0a0'
ACCENT_MUTED = "#749e74"
BTN_BG = '#6ea2aa'
BTN_BG_DISABLED = "#55797e"
BTN_FG = FG_COLOUR



def finalise_settings(config:dict, controller):
    current_config = original_config
    new_config = _deep_merge(current_config, config)
    write_config(new_config)
    
    controller.show_frame(FinalisePage)

def finalise_installation(controller, run: bool = True):
    controller.destroy()
    if run:
        run_server()


class installerApp(tk.Tk):
    def __init__(self, screenName: str | None = None, baseName: str | None = None, className: str = 'Tk', useTk: bool = True, sync: bool = False, use: str | None = None) -> None:
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.title('Canopy Setup')
        self.minsize(700,500)
        self.maxsize(700,500)
        self.resizable(False,False)
        self.geometry('700x700+50+50')

        style = ttk.Style()
        base_theme = 'clam'
        style.theme_use(base_theme)

        self.configure(background=BG_COLOUR)
        style.configure('TFrame', background=BG_COLOUR)
        style.configure('TLabel', background=BG_COLOUR, foreground=FG_COLOUR)

        style.configure('Header.TLabel', font=HEADING_FONT,background=BG_COLOUR, foreground=FG_COLOUR)
        style.map('Accent.TButton', 
                foreground=[('active', BTN_FG),("!disabled", BTN_FG)],
                background=[('active', ACCENT), ('!disabled', BTN_BG_DISABLED)]
                )
        style.configure("Accent.TButton",font=BTN_FONT, foreground=BTN_FG, background=BTN_BG, borderwidth=0, focusthickness=0, padding=(10,5))


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
        label = ttk.Label(self, text='Canopy Setup', font=HEADING_FONT)
        label.pack(anchor='n',pady=20)
        self.configure(background=BG_COLOUR)

        start_btn = ttk.Button(self, text='Start', command=lambda:controller.show_frame(ModeSelectPage))
        start_btn.pack(anchor='se', padx=20)

class ModeSelectPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text='Select Installation Mode', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)
        self.configure(background=BG_COLOUR)


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
        self.configure(background=BG_COLOUR)


        self.e1 = tk.Label(self, text=_get_data_dir().as_posix(), justify='left',width=100)
        self.e1.pack(anchor='nw',padx=(20,50))
        b1 = tk.Button(self, text='...', command=self.data_folder)
        b1.pack(anchor='ne',padx=(0,20))

        back_btn = ttk.Button(self, text='Back', command=lambda:controller.show_frame(ModeSelectPage))
        back_btn.pack(anchor='sw', padx=20)
        next_btn = ttk.Button(self, text='Next', command=lambda:controller.show_frame(SettingsPage))
        next_btn.pack(anchor='se', padx=20)

    def data_folder(self):
        dir = filedialog.askdirectory(initialdir=_get_data_dir())
        _set_data_dir(dir)
        print(_get_data_dir())
        self.e1.configure(text=dir)

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.widgets = {}
        label = ttk.Label(self, text='Settings', font=HEADING_FONT)
        label.pack(anchor='n', pady=20)
        self.configure(background=BG_COLOUR)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        canvas.configure(background=BG_COLOUR)
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

    def build_widgets(self, config, row, prefix='')->int:
        for key,value in config.items():
            if isinstance(value, dict):
                row += 1
                label = tk.Label(self.scroll_frame, text=(prefix+key).replace('.', ' ').title(), font=SUBHEADING_FONT, bg=BG_COLOUR, fg=FG_COLOUR)
                label.grid(row=row, column=1, sticky='w', padx=10, pady=5)
                row += 1
                row = self.build_widgets(value, row, prefix=prefix+key+'.')
            else:
                ttk.Label(self.scroll_frame, text=key, font=TEXT_FONT).grid(row=row, column=0, sticky='w', padx=10, pady=5)
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
        self.configure(background=BG_COLOUR)
        ttk.Label(self,
            text=(
                'Your configuration has been saved.\n'
                'Click **Finish** to close the installer.'
            ),
            justify='center',
        ).pack(anchor='center', pady=10)

        run_var = tk.BooleanVar(value=True)
        run_check = tk.Checkbutton(self, variable=run_var, text='Run program on exit?')
        run_check.pack(anchor='center', pady=10)

        
        back_btn = ttk.Button(self, text='Back', command=lambda:controller.show_frame(SettingsPage))
        back_btn.pack(anchor='sw',padx=20)
        next_btn = ttk.Button(self, text='Finish', command=lambda:finalise_installation(controller, run_var.get()))
        next_btn.pack(anchor='se', padx=20)


app = installerApp()
app.mainloop()