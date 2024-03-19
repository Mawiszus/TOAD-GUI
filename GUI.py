from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import ImageTk, Image, ImageDraw
from py4j.java_gateway import JavaGateway
import os
import platform
import time
import threading
import queue
import torch
import math
import sys

from utils.scrollable_image import ScrollableImage
from utils.tooltip import Tooltip
from utils.level_utils import read_level_from_file, one_hot_to_ascii_level, place_a_mario_token, ascii_to_one_hot_level
from utils.level_image_gen import LevelImageGen
from utils.toad_gan_utils import load_trained_pyramid, generate_sample, TOADGAN_obj

# Path to the AI Framework jar for Playing levels
MARIO_AI_PATH = os.path.abspath(os.path.join(os.path.curdir, "Mario-AI-Framework/mario-1.0-SNAPSHOT.jar"))

# Check if windows user
if platform.system() == "Windows":
    import ctypes
    # Set Taskbar Icon
    my_appid = u'toad-gui.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)

    # Make DPI aware - if size is too small or weird turn on/off
    # ctypes.windll.shcore.SetProcessDpiAwareness(True)


# Validate Function for Entries
def on_validate(in_str, act_type):
    if act_type == '1':  # insertion
        if not in_str.isdigit():
            return False
    return True


# Object holding important data about the current level
class LevelObject:
    def __init__(self, ascii_level, oh_level, image, tokens, scales, noises):
        self.ascii_level = ascii_level
        self.oh_level = oh_level  # one-hot encoded
        self.image = image
        self.tokens = tokens
        self.scales = scales
        self.noises = noises


# Main GUI code
def TOAD_GUI():
    # Init Window
    root = Tk(className=" TOAD-GUI")

    # Thread Functions to keep GUI alive when playing/loading/generating
    class ThreadedClient(threading.Thread):
        def __init__(self, que, fcn):
            threading.Thread.__init__(self)
            self.que = que
            self.fcn = fcn

        def run(self):
            time.sleep(0.01)
            self.que.put(self.fcn())

    def spawn_thread(que, fcn):
        thread = ThreadedClient(que, fcn)
        thread.start()
        periodic_call(thread)

    def periodic_call(thread):
        if thread.is_alive():
            root.after(100, lambda: periodic_call(thread))

    # Load Icons
    toad_icon = ImageTk.PhotoImage(Image.open('icons/toad_icon.png'))
    banner_icon = ImageTk.PhotoImage(Image.open('icons/banner.png'))
    load_level_icon = ImageTk.PhotoImage(Image.open('icons/folder_level.png'))
    load_generator_icon = ImageTk.PhotoImage(Image.open('icons/folder_toad.png'))
    generate_level_icon = ImageTk.PhotoImage(Image.open('icons/gear_toad.png'))
    play_level_icon = ImageTk.PhotoImage(Image.open('icons/play_button.png'))
    save_level_icon = ImageTk.PhotoImage(Image.open('icons/save_button.png'))

    root.iconphoto(False, toad_icon)

    # Level to Image renderer
    ImgGen = LevelImageGen(os.path.join(os.path.join(os.curdir, "utils"), "sprites"))

    # Get images of tokens for edit context menu
    full_token_list = torch.load("files/token_list.pth")
    token_img_dict = {}
    for token in full_token_list:
        token_img_dict[token] = ImageTk.PhotoImage(ImgGen.render([token]))

    # Placeholder image for the preview
    placeholder = Image.new('RGB', (890, 256), (255, 255, 255))
    draw = ImageDraw.Draw(placeholder)
    draw.text((356, 128), "Level Preview will appear here.", (0, 0, 0))
    levelimage = ImageTk.PhotoImage(placeholder)

    # Define Variables
    level_obj = LevelObject('-', None, levelimage, ['-'], None, None)
    toadgan_obj = TOADGAN_obj(None, None, None, None, None, None)

    level_l = IntVar()
    level_h = IntVar()
    load_string_gen = StringVar()
    load_string_txt = StringVar()
    error_msg = StringVar()
    use_gen = BooleanVar()
    is_loaded = BooleanVar()
    q = queue.Queue()

    # Set values
    level_l.set(0)
    level_h.set(0)
    load_string_gen.set("Click the buttons to open a level or generator.")
    load_string_txt.set(os.path.join(os.curdir, "levels"))
    error_msg.set("No Errors")
    use_gen.set(False)
    is_loaded.set(False)

    # ---------------------------------------- Define Callbacks ----------------------------------------
    def load_level():
        fname = fd.askopenfilename(title='Load Level', initialdir=os.path.join(os.curdir, 'levels'),
                                   filetypes=[("level .txt files", "*.txt")])
        if len(fname) == 0:
            return  # loading was cancelled
        try:
            error_msg.set("Loading level...")
            is_loaded.set(False)
            use_gen.set(False)

            if fname[-3:] == "txt":
                load_string_gen.set('Path: ' + fname)
                folder, lname = os.path.split(fname)

                # Load level
                lev, tok = read_level_from_file(folder, lname)

                level_obj.oh_level = torch.Tensor(lev)  # casting to Tensor to keep consistency with generated levels
                level_obj.ascii_level = one_hot_to_ascii_level(lev, tok)

                # Check if a Mario token exists - if not, we need to place one
                m_exists = False
                for line in level_obj.ascii_level:
                    if 'M' in line:
                        m_exists = True
                if not m_exists:
                    level_obj.ascii_level = place_a_mario_token(level_obj.ascii_level)
                level_obj.tokens = tok

                img = ImageTk.PhotoImage(ImgGen.render(level_obj.ascii_level))
                level_obj.image = img

                level_obj.scales = None
                level_obj.noises = None

                level_l.set(lev.shape[-1])
                level_h.set(lev.shape[-2])

                is_loaded.set(True)
                use_gen.set(False)
                error_msg.set("Level loaded")
            else:
                error_msg.set("No level file selected.")
        except Exception:
            error_msg.set("No level file selected.")
        return

    def load_generator():
        fname = fd.askdirectory(title='Load Generator Directory', initialdir=os.path.join(os.curdir, 'generators'))

        if len(fname) == 0:
            return  # loading was cancelled
        try:
            error_msg.set("Loading generator...")
            use_gen.set(False)
            is_loaded.set(False)
            load_string_gen.set('Path: ' + fname)
            folder = fname

            # Load TOAD-GAN
            loadgan, msg = load_trained_pyramid(folder)
            toadgan_obj.Gs = loadgan.Gs
            toadgan_obj.Zs = loadgan.Zs
            toadgan_obj.reals = loadgan.reals
            toadgan_obj.NoiseAmp = loadgan.NoiseAmp
            toadgan_obj.token_list = loadgan.token_list
            toadgan_obj.num_layers = loadgan.num_layers

            level_l.set(toadgan_obj.reals[-1].shape[-1])
            level_h.set(toadgan_obj.reals[-1].shape[-2])

            error_msg.set(msg)

            is_loaded.set(False)
            use_gen.set(True)

        except Exception:
            error_msg.set("Could not load generator. Confirm that all needed .pth files are in the chosen folder.")

        return

    def save_txt():
        save_name = fd.asksaveasfile(title='Save level (.txt/.png)', initialdir=os.path.join(os.curdir, "levels"),
                                     mode='w', defaultextension=".txt",
                                     filetypes=[("txt files", ".txt"), ("png files", ".png")])
        if save_name is None:
            return  # saving was cancelled
        elif save_name.name[-3:] == "txt":
            text2save = ''.join(level_obj.ascii_level)
            save_name.write(text2save)
            save_name.close()
        elif save_name.name[-3:] == "png":
            ImgGen.render(level_obj.ascii_level).save(save_name.name)
        else:
            error_msg.set("Could not save level with this extension. Supported: .txt, .png")
        return

    def generate():
        if toadgan_obj.Gs is None:
            error_msg.set("Generator did not load correctly. Are all necessary files in the folder?")
        else:
            error_msg.set("Generating level...")
            is_loaded.set(False)
            # Get scaling from height and length
            sc_h = level_h.get() / toadgan_obj.reals[-1].shape[-2]
            sc_l = level_l.get() / toadgan_obj.reals[-1].shape[-1]

            # Generate level
            level, scales, noises = generate_sample(toadgan_obj.Gs, toadgan_obj.Zs, toadgan_obj.reals,
                                                    toadgan_obj.NoiseAmp, toadgan_obj.num_layers,
                                                    toadgan_obj.token_list,
                                                    scale_h=sc_l, scale_v=sc_h)
            level_obj.oh_level = level.cpu()
            level_obj.scales = scales
            level_obj.noises = noises

            level_obj.ascii_level = one_hot_to_ascii_level(level, toadgan_obj.token_list)
            redraw_image()

            is_loaded.set(True)
            set_button_state(None, None, None)
            print("Level generated!")
            error_msg.set("Level generated!")
        return

    def redraw_image(edit_mode=False, rectangle=[(0, 0), (16, 16)], scale=0):
        if is_loaded.get():
            # Check if a Mario token exists - if not, we need to place one
            m_exists = False
            for line in level_obj.ascii_level:
                if 'M' in line:
                    m_exists = True
            if not m_exists:
                level_obj.ascii_level = place_a_mario_token(level_obj.ascii_level)
            if use_gen.get():
                level_obj.tokens = toadgan_obj.token_list

            # Render Image
            pil_img = ImgGen.render(level_obj.ascii_level)

            if edit_mode:
                # Add numbers to rows and cols
                l_draw = ImageDraw.Draw(pil_img)
                for y in range(level_obj.oh_level.shape[-2]):
                    l_draw.multiline_text((1, 4+y*16), str(y), (255, 255, 255),
                                          stroke_width=-1, stroke_fill=(0, 0, 0))
                for x in range(level_obj.oh_level.shape[-1]):
                    l_draw.multiline_text((6+x*16, 0), '\n'.join(list(str(x))), (255,255,255),
                                          stroke_width=-1, stroke_fill=(0, 0, 0),  spacing=3,
                                          align='right')
                # Add bounding box rectangle
                l_draw.rectangle(rectangle, outline=(255, 0, 0), width=2)

                # Affected tokens rectangle
                n_pads = len(level_obj.scales) - scale
                if n_pads > 0:  # if scale is chosen too big, this just does not render
                    padding_effect = 3 * n_pads
                    sc = level_obj.scales[scale].shape[-1] / level_obj.oh_level.shape[-1]
                    scaling_effect = math.ceil((1/sc - 1) / 2)  # affected tokens in every direction
                    aoe = (padding_effect + scaling_effect) * 16
                    affected_rect = [(rectangle[0][0] - aoe, rectangle[0][1] - aoe),
                                     (rectangle[1][0] + aoe, rectangle[1][1] + aoe)]
                    l_draw.rectangle(affected_rect, outline=(255, 255, 0), width=2)

            # Cast image
            img = ImageTk.PhotoImage(pil_img)

            level_obj.image = img
            image_label.change_image(level_obj.image)

    def play_level():
        error_msg.set("Playing level...")
        is_loaded.set(False)
        remember_use_gen = use_gen.get()
        use_gen.set(False)
        # Py4j Java bridge uses Mario AI Framework
        gateway = JavaGateway.launch_gateway(classpath=MARIO_AI_PATH, die_on_exit=True, redirect_stdout=sys.stdout, redirect_stderr=sys.stderr)
        game = gateway.jvm.engine.core.MarioGame()
        try:
            game.initVisuals(2.0)
            agent = gateway.jvm.agents.human.Agent()
            game.setAgent(agent)
            while True:
                result = game.gameLoop(''.join(level_obj.ascii_level), 200, 0, True, 30)
                perc = int(result.getCompletionPercentage() * 100)
                error_msg.set("Level Played. Completion Percentage: %d%%" % perc)
        except Exception:
            error_msg.set("Level Play was interrupted.")
            is_loaded.set(True)
            use_gen.set(remember_use_gen)
        finally:
            game.getWindow().dispose()
            gateway.java_process.kill()
            gateway.close()

        is_loaded.set(True)
        use_gen.set(remember_use_gen)  # only set use_gen to True if it was previously
        return

    # ---------------------------------------- Layout ----------------------------------------

    settings = ttk.Frame(root, padding=(15, 15, 15, 15), width=1000, height=1000)  # Main Frame

    banner = ttk.Label(settings, image=banner_icon)
    welcome_message = ttk.Label(settings, text="Welcome to TOAD-GUI, a Framework to view and playtest Mario levels "
                                               "generated by TOAD-GAN.", width=95, anchor='center')

    # Displays loaded path
    fpath_label = ttk.Label(settings, textvariable=load_string_gen, width=100)

    # Top Buttons
    load_lev_button = ttk.Button(settings, compound='top', image=load_level_icon, width=35,
                                 text='Open Level', command=lambda: spawn_thread(q, load_level))
    load_gen_button = ttk.Button(settings, compound='top', image=load_generator_icon, width=35,
                                 text='Open Generator', command=lambda: spawn_thread(q, load_generator))
    save_button = ttk.Button(settings, compound='top', image=save_level_icon,
                             text='Save Level/Image', state='disabled', command=lambda: spawn_thread(q, save_txt))
    gen_button = ttk.Button(settings, compound='top', image=generate_level_icon,
                            text='Generate level', state='disabled', command=lambda: spawn_thread(q, generate))

    # Size Entries
    size_frame = ttk.Frame(settings, padding=(1, 1, 1, 1))
    h_label = ttk.Label(size_frame, text="Size:")
    h_entry = ttk.Entry(size_frame, textvariable=level_h, validate="key", width=3, justify='right', state='disabled')
    l_label = ttk.Label(size_frame, text="X")
    l_entry = ttk.Entry(size_frame, textvariable=level_l, validate="key", width=3, justify='right', state='disabled')

    vcmd_h = (h_entry.register(on_validate), '%P', '%d')
    vcmd_l = (l_entry.register(on_validate), '%P', '%d')

    h_entry.configure(validatecommand=vcmd_h)
    l_entry.configure(validatecommand=vcmd_l)

    # Callback to set buttons active/inactive depending on load state
    def set_button_state(t1, t2, t3):
        if use_gen.get():
            gen_button.state(['!disabled'])
            if not is_loaded.get():
                save_button.state(['disabled'])
            else:
                save_button.state(['!disabled'])
            h_entry.state(['!disabled'])
            l_entry.state(['!disabled'])
            emode_box.state(['!disabled'])
        else:
            gen_button.state(['disabled'])
            if not is_loaded.get():
                save_button.state(['disabled'])
            else:
                save_button.state(['!disabled'])
                editmode.set(False)
            h_entry.state(['disabled'])
            l_entry.state(['disabled'])
            emode_box.state(['disabled'])
        return

    use_gen.trace("w", callback=set_button_state)

    # Play and Controls frame
    p_c_frame = ttk.Frame(settings)
    play_button = ttk.Button(p_c_frame, compound='top', image=play_level_icon, text='Play level',
                             state='disabled', command=lambda: spawn_thread(q, play_level))

    # Level Preview image
    image_label = ScrollableImage(settings, image=levelimage, height=271)

    # Token edit function
    def change_token(tok, x, y):
        level_obj.oh_level[0, :, y, x] = 0
        level_obj.oh_level[0, level_obj.tokens.index(tok), y, x] = 1
        level_obj.ascii_level = one_hot_to_ascii_level(level_obj.oh_level, level_obj.tokens)
        toggle_editmode(None, None, None)

    # Popup Menu for the token edit function
    def popup_edit(event):
        e_menu = Menu(root, tearoff=0)
        # Get actual x,y position from click position
        tok_x = int(event.widget.canvasx(event.x) / 16)
        tok_y = int(event.widget.canvasy(event.y) / 16)

        if is_loaded.get():
            try:
                for i, t in enumerate(level_obj.tokens):
                    if not (t == 'M' or t == 'F'):  # Mario or Flag can not be placed, but are placed automatically
                        e_menu.add_command(image=token_img_dict[t], label=t, compound='left',
                                           command=lambda tok=t: change_token(tok, tok_x, tok_y))
            except TypeError:
                e_menu.add_command(label="No changeable Level loaded")
        else:
            e_menu.add_command(label="No changeable Level loaded")

        e_menu.tk_popup(event.x_root, event.y_root)

    # Bind right-click to pop-up menu
    if platform.system() == 'Darwin':
        image_label.bind("<Button-2>", popup_edit)  # MacOS has Button 2 for some reason
    else:
        image_label.bind("<Button-3>", popup_edit)

    # Enable/Disable Play Button when loaded/unloaded
    def set_play_state(t1, t2, t3):
        if is_loaded.get():
            play_button.state(['!disabled'])
            image_label.change_image(level_obj.image)
        else:
            play_button.state(['disabled'])
        toggle_editmode(t1, t2, t3)
        return

    is_loaded.trace("w", callback=set_play_state)

    # Frame displaying the Game's controls
    controls_frame = ttk.LabelFrame(p_c_frame, padding=(5, 5, 5, 5), text='Controls')
    contr_a = ttk.Label(controls_frame, text=' a :')
    contr_s = ttk.Label(controls_frame, text=' s :')
    contr_l = ttk.Label(controls_frame, text='<- :')
    contr_r = ttk.Label(controls_frame, text='-> :')

    descr_a = ttk.Label(controls_frame, text='Sprint/Throw Fireball')
    descr_s = ttk.Label(controls_frame, text='Jump')
    descr_l = ttk.Label(controls_frame, text='Move left')
    descr_r = ttk.Label(controls_frame, text='Move right')

    error_label = ttk.Label(settings, textvariable=error_msg)

    # ---------------------------------------- Grid Layout ----------------------------------------

    # On root:
    settings.grid(column=0, row=0, sticky=(N, S, E, W))

    # On settings:
    banner.grid(column=1, row=0, columnspan=2, sticky=(N, S))
    welcome_message.grid(column=1, row=1, columnspan=2, sticky=(N, S), padx=5, pady=8)
    load_lev_button.grid(column=2, row=3, sticky=(N, S, E, W), padx=5, pady=5)
    load_gen_button.grid(column=1, row=3, sticky=(N, S, E, W), padx=5, pady=5)
    gen_button.grid(column=1, row=4, sticky=(N, S, E, W), padx=5, pady=5)
    save_button.grid(column=2, row=4, sticky=(N, S, E, W), padx=5, pady=5)
    image_label.grid(column=0, row=6, columnspan=4, sticky=(N, E, W), padx=5, pady=8)
    p_c_frame.grid(column=1, row=7, columnspan=2, sticky=(N, S, E, W), padx=5, pady=5)
    fpath_label.grid(column=0, row=99, columnspan=4, sticky=(S, E, W), padx=5, pady=5)
    error_label.grid(column=0, row=100, columnspan=4, sticky=(S, E, W), padx=5, pady=1)
    size_frame.grid(column=1, row=5, columnspan=1, sticky=(N, S), padx=5, pady=2)

    # On size_frame:
    h_label.grid(column=0, row=0, sticky=(N, S, E), padx=1, pady=0)
    l_entry.grid(column=1, row=0, sticky=(N, S), padx=1, pady=0)
    l_label.grid(column=2, row=0, sticky=(N, S), padx=1, pady=0)
    h_entry.grid(column=3, row=0, sticky=(N, S), padx=1, pady=0)

    # On p_c_frame:
    play_button.grid(column=1, row=0, sticky=(N, S, E, W), padx=5, pady=5)
    controls_frame.grid(column=2, row=0, sticky=(N, S, E, W), padx=5, pady=5)

    # On controls_frame
    contr_a.grid(column=0, row=0, sticky=(N, S, E), padx=1, pady=1)
    contr_s.grid(column=0, row=1, sticky=(N, S, E), padx=1, pady=1)
    contr_l.grid(column=0, row=2, sticky=(N, S, E), padx=1, pady=1)
    contr_r.grid(column=0, row=3, sticky=(N, S, E), padx=1, pady=1)
    descr_a.grid(column=1, row=0, sticky=(N, S, W), padx=1, pady=1)
    descr_s.grid(column=1, row=1, sticky=(N, S, W), padx=1, pady=1)
    descr_l.grid(column=1, row=2, sticky=(N, S, W), padx=1, pady=1)
    descr_r.grid(column=1, row=3, sticky=(N, S, W), padx=1, pady=1)

    # Column/Rowconfigure
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    settings.columnconfigure(0, weight=1)
    settings.columnconfigure(1, weight=1)
    settings.columnconfigure(2, weight=1)
    settings.columnconfigure(3, weight=1)
    settings.rowconfigure(0, weight=1)
    settings.rowconfigure(1, weight=1)
    settings.rowconfigure(2, weight=1)
    settings.rowconfigure(3, weight=1)
    settings.rowconfigure(4, weight=1)
    settings.rowconfigure(5, weight=1)
    settings.rowconfigure(6, weight=2)
    settings.rowconfigure(7, weight=1)
    settings.rowconfigure(99, weight=1)
    settings.rowconfigure(100, weight=1)

    p_c_frame.columnconfigure(1, weight=2)
    p_c_frame.columnconfigure(2, weight=0)
    p_c_frame.rowconfigure(0, weight=1)

    controls_frame.columnconfigure(0, weight=1)
    controls_frame.columnconfigure(1, weight=1)
    controls_frame.rowconfigure(0, weight=1)
    controls_frame.rowconfigure(1, weight=1)
    controls_frame.rowconfigure(2, weight=1)
    controls_frame.rowconfigure(3, weight=1)

    # ---------------------------------------- Edit Mode ----------------------------------------

    # Define Variables
    editmode = BooleanVar()
    bbox_x1 = IntVar()
    bbox_x2 = IntVar()
    bbox_y1 = IntVar()
    bbox_y2 = IntVar()
    edit_scale = IntVar()
    scale_info = StringVar()

    # Set values
    editmode.set(False)
    bbox_x1.set(0)
    bbox_x2.set(16)
    bbox_y1.set(0)
    bbox_y2.set(16)
    edit_scale.set(0)
    scale_info.set("Scale 0 window: 8x8")

    # Placeholder for the noise representation
    noise_holder = Image.new('RGB', (8, 8), (255, 255, 255))
    noiseimage = ImageTk.PhotoImage(noise_holder)

    # ---------------------------------------- Edit Mode Widgets ----------------------------------------

    # Set Edit mode Checkbox
    emode_box = ttk.Checkbutton(settings, text="Edit mode", variable=editmode, state='disabled')
    em_tooltip = Tooltip(emode_box,
                         text="Right click the image to change a token directly. \n"
                              "Edit mode allows for resampling parts of a generated level.",
                         wraplength=250, bg="white", enabled=True, waittime=100)
    emode_box.grid(column=1, row=8, columnspan=2, sticky=(N, S, E, W), padx=5, pady=5)
    settings.rowconfigure(8, weight=1)

    # Edit mode frame
    emode_frame = ttk.LabelFrame(p_c_frame, text="Edit mode controls", padding=(5, 5, 5, 5))
    # Bounding Box frame
    bbox_frame = ttk.LabelFrame(emode_frame, text="Bounding Box", padding=(5, 5, 5, 5))

    # Bounding box Entries
    x1_label = ttk.Label(bbox_frame, text="x1:", width=5, anchor="e")
    x1_entry = ttk.Entry(bbox_frame, textvariable=bbox_y1, validate="key", width=3, justify='right')
    x2_label = ttk.Label(bbox_frame, text="x2:")
    x2_entry = ttk.Entry(bbox_frame, textvariable=bbox_y2, validate="key", width=3, justify='right')
    y1_label = ttk.Label(bbox_frame, text=" y1:", width=5, anchor="e")
    y1_entry = ttk.Entry(bbox_frame, textvariable=bbox_x1, validate="key", width=3, justify='right')
    y2_label = ttk.Label(bbox_frame, text=" y2:")
    y2_entry = ttk.Entry(bbox_frame, textvariable=bbox_x2, validate="key", width=3, justify='right')

    bbox_tt_string = "Controls the red bounding box. The yellow box shows which tokens are also " \
                     "influenced by a change in this scale."

    x1_tooltip = Tooltip(x1_label, text=bbox_tt_string, wraplength=250, bg="white", enabled=False)
    x2_tooltip = Tooltip(x2_label, text=bbox_tt_string,  wraplength=250, bg="white", enabled=False)
    y1_tooltip = Tooltip(y1_label, text=bbox_tt_string, wraplength=250, bg="white", enabled=False)
    y2_tooltip = Tooltip(y2_label, text=bbox_tt_string, wraplength=250, bg="white", enabled=False)

    # Scale entry and
    sc_frame = ttk.Frame(emode_frame, padding=(0, 5, 0, 5))
    sc_label = ttk.Label(sc_frame, text="Scale:")
    sc_entry = ttk.Entry(sc_frame, textvariable=edit_scale, validate="key", width=3, justify='right')

    # Noise image and info label
    sc_noise_image = ScrollableImage(emode_frame, image=noiseimage, height=50, width=300)
    noise_tooltip = Tooltip(sc_noise_image,
                            text="This is a visualization of the noise map in the chosen scale. "
                                 "Pixels to be resampled are marked red.",
                            wraplength=250, bg="white", enabled=False)

    sc_info_label = ttk.Label(sc_frame, textvariable=scale_info)
    sc_tooltip = Tooltip(sc_info_label,
                         text="Noise influence is a learned parameter that indicates "
                              "how much influence a change of the noise map will have on this scale.",
                         wraplength=250, bg="white", enabled=False)

    # Entry Validation
    vcmd_x1 = (x1_entry.register(on_validate), '%P', '%d')
    vcmd_x2 = (x2_entry.register(on_validate), '%P', '%d')
    vcmd_y1 = (y1_entry.register(on_validate), '%P', '%d')
    vcmd_y2 = (y2_entry.register(on_validate), '%P', '%d')
    vcmd_sc = (sc_entry.register(on_validate), '%P', '%d')

    x1_entry.configure(validatecommand=vcmd_x1)
    x2_entry.configure(validatecommand=vcmd_x2)
    y1_entry.configure(validatecommand=vcmd_y1)
    y2_entry.configure(validatecommand=vcmd_y2)
    sc_entry.configure(validatecommand=vcmd_sc)

    # Resample Button and info
    resample_button = ttk.Button(emode_frame, text="Resample", state='disabled',
                                 command=lambda: spawn_thread(q, re_sample))
    sample_info = ttk.Label(emode_frame, text=# "Right click to edit Tokens directly.\n"
                                              "Resampling will regenerate the level,\n"
                                              "so prior Token edits will be lost.")

    # TOAD-GAN resample function
    def re_sample():
        if not level_obj.scales:
            error_msg.set("Can't resample loaded level.")  # should not be reachable
        else:
            is_loaded.set(False)
            # Get scaled Bounding Box
            sc = level_obj.scales[edit_scale.get()].shape[-1] / level_obj.oh_level.shape[-1]
            scaled_bbox = (round(bbox_x1.get() * sc), round(bbox_x2.get() * sc),
                           round(bbox_y1.get() * sc), round(bbox_y2.get() * sc))

            new_states = [level_obj.scales, level_obj.noises]

            # Get x,y scales from height and length
            sc_h = level_h.get() / toadgan_obj.reals[-1].shape[-2]
            sc_l = level_l.get() / toadgan_obj.reals[-1].shape[-1]

            # Regenerate level from noise (this will reset prior edits)
            level, scales, noises = generate_sample(toadgan_obj.Gs, toadgan_obj.Zs, toadgan_obj.reals,
                                                    toadgan_obj.NoiseAmp, toadgan_obj.num_layers,
                                                    toadgan_obj.token_list, in_states=new_states,
                                                    gen_start_scale=edit_scale.get(), is_bboxed=True,
                                                    bbox=scaled_bbox, scale_v=sc_h, scale_h=sc_l)
            level_obj.oh_level = level.cpu()
            level_obj.scales = scales
            level_obj.noises = noises

            level_obj.ascii_level = one_hot_to_ascii_level(level, toadgan_obj.token_list)
            redraw_image(scale=edit_scale.get())

            is_loaded.set(True)

    # Grid/Remove Edit mode widgets
    def toggle_editmode(t1, t2, t3):
        if editmode.get():
            # Grid widgets
            controls_frame.grid_configure(column=1, row=1)  # move frame to make room

            # On settings:
            emode_frame.grid(column=0, row=0, rowspan=2, sticky=(E, W), padx=10)

            # On emode_frame:
            bbox_frame.grid(column=0, row=0, columnspan=1, sticky=(E, W), padx=5, pady=5)
            resample_button.grid(column=0, row=5, columnspan=3, sticky=(N, S, E, W), padx=5, pady=5)
            sample_info.grid(column=0, row=4, columnspan=3, sticky=(N, S), padx=5, pady=5)
            sc_frame.grid(column=1, row=0, columnspan=5, sticky=(N, S, E, W), padx=5, pady=5)
            sc_label.grid(column=0, row=0, columnspan=1, sticky=(N, S, E), padx=1, pady=5)
            sc_entry.grid(column=1, row=0, columnspan=1, sticky=(N, S, W), padx=1, pady=5)
            sc_info_label.grid(column=0, row=1, columnspan=2, sticky=(N, S, E, W), padx=1, pady=5)
            sc_noise_image.grid(column=0, row=2, columnspan=2, sticky=(N, S), padx=1, pady=5)

            # On bbox_frame:
            x1_label.grid(column=0, row=0, sticky=(N, S, E), padx=1, pady=1)
            x1_entry.grid(column=1, row=0, sticky=(N, S, W), padx=5, pady=1)
            x2_label.grid(column=0, row=1, sticky=(N, S, E), padx=1, pady=1)
            x2_entry.grid(column=1, row=1, sticky=(N, S, W), padx=5, pady=1)
            y1_label.grid(column=2, row=0, sticky=(N, S, E), padx=1, pady=1)
            y1_entry.grid(column=3, row=0, sticky=(N, S, W), padx=5, pady=1)
            y2_label.grid(column=2, row=1, sticky=(N, S, E), padx=1, pady=1)
            y2_entry.grid(column=3, row=1, sticky=(N, S, W), padx=5, pady=1)

            # Column/Rowconfigure
            emode_frame.columnconfigure(0, weight=0)
            emode_frame.columnconfigure(1, weight=1)
            emode_frame.rowconfigure(0, weight=1)
            emode_frame.rowconfigure(1, weight=1)
            emode_frame.rowconfigure(2, weight=1)
            emode_frame.rowconfigure(3, weight=1)
            emode_frame.rowconfigure(4, weight=1)
            emode_frame.rowconfigure(5, weight=1)

            bbox_frame.columnconfigure(0, weight=1)
            bbox_frame.columnconfigure(1, weight=1)
            bbox_frame.columnconfigure(2, weight=1)
            bbox_frame.columnconfigure(3, weight=1)
            bbox_frame.rowconfigure(0, weight=1)
            bbox_frame.rowconfigure(1, weight=1)

            sc_frame.columnconfigure(0, weight=1)
            sc_frame.columnconfigure(1, weight=1)
            sc_frame.rowconfigure(0, weight=1)
            sc_frame.rowconfigure(1, weight=1)
            sc_frame.rowconfigure(2, weight=1)

            redraw_image(True, rectangle=[(bbox_y1.get()*16, bbox_x1.get()*16),
                                          (bbox_y2.get()*16, bbox_x2.get()*16)], scale=edit_scale.get())

            update_scale_info(t1, t2, t3)

        else:
            # Hide widgets
            controls_frame.grid_configure(column=2, row=0)  # move frame back
            emode_frame.grid_forget()
            redraw_image(False)

    editmode.trace("w", callback=toggle_editmode)

    # Update scale info label, noise image and resample button availability
    def update_scale_info(t1, t2, t3):
        try:
            # Correct bbox values, TODO: BBox entries are not user friendly - lower value can't be set first
            if bbox_y1.get() < 0:
                bbox_y1.set(0)
            if bbox_x1.get() < 0:
                bbox_x1.set(0)
            if bbox_y2.get() >= len(level_obj.ascii_level[-1]):
                bbox_y2.set(len(level_obj.ascii_level[-1]))
            if bbox_x2.get() >= len(level_obj.ascii_level):
                bbox_x2.set(len(level_obj.ascii_level))
            if bbox_y1.get() >= bbox_y2.get():
                bbox_y1.set(bbox_y2.get()-1)
            if bbox_x1.get() >= bbox_x2.get():
                bbox_x1.set(bbox_x2.get()-1)

            redraw_image(True, rectangle=[(bbox_y1.get() * 16, bbox_x1.get() * 16),
                                          (bbox_y2.get() * 16, bbox_x2.get() * 16)], scale=edit_scale.get())

            # Show Noise Amplitude, which indicates how much influence this noise change will have
            scale_info.set("Noise influence: %.4f\n"
                           % (toadgan_obj.NoiseAmp[edit_scale.get()]))
            sc_tooltip.enabled = True

            # Calculate scaled bounding box
            sc = level_obj.scales[edit_scale.get()].shape[-1] / level_obj.oh_level.shape[-1]
            scaled_bbox = [(round(bbox_y1.get() * sc), round(bbox_x1.get() * sc)),
                           (round(bbox_y2.get() * sc), round(bbox_x2.get() * sc))]

            # Get first tokens noise map on current scale as representation
            noise_holder = Image.fromarray(level_obj.noises[edit_scale.get()][0, 0, 3:-3, 3:-3].cpu().numpy()*255)
            noise_holder = noise_holder.convert('RGB')

            # Draw adjusted bounding box on noise map
            if not (round(bbox_y1.get() * sc) == round(bbox_y2.get() * sc) or
                    round(bbox_x1.get() * sc) == round(bbox_x2.get() * sc)):
                n_draw = ImageDraw.Draw(noise_holder, 'RGBA')
                rectanglebox = scaled_bbox
                rectanglebox[1] = (max(round(bbox_y1.get() * sc), round(bbox_y2.get() * sc) - 1),
                                   max(round(bbox_x1.get() * sc), round(bbox_x2.get() * sc) - 1))
                n_draw.rectangle(rectanglebox, fill=(255, 0, 0, 128))

            # Make image bigger, so you can see it better
            noise_holder = noise_holder.resize((noise_holder.size[0] * 2, noise_holder.size[1] * 2), Image.NEAREST)

            # Set noise image
            noiseimage = ImageTk.PhotoImage(noise_holder)
            sc_noise_image.change_image(noiseimage)

            resample_button.state(['!disabled'])  # Allow resampling
            noise_tooltip.enabled = True
            x1_tooltip.enabled = True
            x2_tooltip.enabled = True
            y1_tooltip.enabled = True
            y2_tooltip.enabled = True

        except TclError:
            scale_info.set("No scale")
            resample_button.state(['disabled'])
            sc_tooltip.enabled = False
            noise_tooltip.enabled = True
            x1_tooltip.enabled = True
            x2_tooltip.enabled = True
            y1_tooltip.enabled = True
            y2_tooltip.enabled = True

        except IndexError:
            scale_info.set("Scale out of range")
            resample_button.state(['disabled'])
            sc_tooltip.enabled = False
            noise_tooltip.enabled = True
            x1_tooltip.enabled = True
            x2_tooltip.enabled = True
            y1_tooltip.enabled = True
            y2_tooltip.enabled = True

        except TypeError:
            scale_info.set("No editable level loaded")
            noise_holder = Image.new('RGB', (8, 8), (255, 255, 255))
            noiseimage = ImageTk.PhotoImage(noise_holder)
            sc_noise_image.change_image(noiseimage)
            resample_button.state(['disabled'])
            sc_tooltip.enabled = False
            noise_tooltip.enabled = False
            x1_tooltip.enabled = False
            x2_tooltip.enabled = False
            y1_tooltip.enabled = False
            y2_tooltip.enabled = False

    edit_scale.trace("w", callback=update_scale_info)
    bbox_x1.trace("w", callback=update_scale_info)
    bbox_x2.trace("w", callback=update_scale_info)
    bbox_y1.trace("w", callback=update_scale_info)
    bbox_y2.trace("w", callback=update_scale_info)

    # Move scrollbar to middle (to have message on the test image appear centered)
    root.update()
    root.after(1, image_label.move_scrollbar_to_middle)

    # Run Window
    root.mainloop()
