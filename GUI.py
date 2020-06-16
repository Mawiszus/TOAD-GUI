from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import ImageTk, Image, ImageFont, ImageDraw
from py4j.java_gateway import JavaGateway
import os
import platform
import time
import threading
import queue

from utils.scrollable_image import ScrollableImage
from utils.level_utils import read_level_from_file, one_hot_to_ascii_level, place_a_mario_token
from utils.level_image_gen import LevelImageGen
from utils.toad_gan_utils import load_trained_pyramid, generate_sample, TOADGAN_obj


MARIO_AI_PATH = os.path.abspath(os.path.join(os.path.curdir, "Mario-AI-Framework/mario-1.0-SNAPSHOT.jar"))

# Cheasck if windows user to make sure taskbar icon is correct
if platform.system() == "Windows":
    import ctypes
    my_appid = u'toad-gui.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)


class LevelObject:
    def __init__(self, ascii_level, oh_level, image, tokens):
        self.ascii_level = ascii_level
        self.oh_level = oh_level
        self.image = image
        self.tokens = tokens


def TOAD_GUI():
    # Init Window
    root = Tk(className=" TOAD-GUI")

    # Functions to keep GUI alive when playing/loading/generating
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

    # Define Variables
    ImgGen = LevelImageGen(os.path.join(os.path.join(os.curdir, "utils"), "sprites"))
    current_level, current_tokens = read_level_from_file(os.path.join(os.curdir, "levels/originals"), "lvl_1-1.txt")

    placeholder = Image.new('RGB', (690, 256), (255, 255, 255))
    draw = ImageDraw.Draw(placeholder)
    draw.text((256, 128), "Level Preview will appear here.", (0, 0, 0))
    levelimage = ImageTk.PhotoImage(placeholder)

    level_obj = LevelObject(one_hot_to_ascii_level(current_level, current_tokens),
                            current_level, levelimage, current_tokens)
    toadgan_obj = TOADGAN_obj(None, None, None, None, None, None)

    load_string_gen = StringVar()
    load_string_txt = StringVar()
    error_msg = StringVar()
    use_gen = BooleanVar()
    is_loaded = BooleanVar()
    q = queue.Queue()

    load_string_gen.set("Click the buttons to open a level or generator.")
    load_string_txt.set(os.path.join(os.curdir, "levels"))
    error_msg.set("No Errors")
    use_gen.set(False)
    is_loaded.set(False)

    # Define Callbacks
    def load_level():
        fname = fd.askopenfilename(title='Load Level', initialdir=os.path.join(os.curdir, 'levels'),
                                   filetypes=[("level .txt files", "*.txt")])
        try:
            error_msg.set("Loading level...")
            if fname[-3:] == "txt":
                load_string_gen.set('Path: ' + fname)
                folder, lname = os.path.split(fname)

                lev, tok = read_level_from_file(folder, lname)

                level_obj.oh_level = lev
                level_obj.ascii_level = one_hot_to_ascii_level(lev, tok)
                m_exists = False
                for line in level_obj.ascii_level:
                    if 'M' in line:
                        m_exists = True
                if not m_exists:
                    level_obj.ascii_level = place_a_mario_token(level_obj.ascii_level)
                level_obj.tokens = tok

                img = ImageTk.PhotoImage(ImgGen.render(level_obj.ascii_level))
                level_obj.image = img

                use_gen.set(False)
                is_loaded.set(True)
                error_msg.set("Level loaded")
            else:
                error_msg.set("No level file selected.")
        except Exception:
            error_msg.set("No level file selected.")

        return

    def load_generator():
        fname = fd.askdirectory(title='Load Generator Directory', initialdir=os.path.join(os.curdir, 'generators'))

        try:
            error_msg.set("Loading generator...")
            load_string_gen.set('Path: ' + fname)
            folder = fname

            loadgan, msg = load_trained_pyramid(folder)
            toadgan_obj.Gs = loadgan.Gs
            toadgan_obj.Zs = loadgan.Zs
            toadgan_obj.reals = loadgan.reals
            toadgan_obj.NoiseAmp = loadgan.NoiseAmp
            toadgan_obj.token_list = loadgan.token_list
            toadgan_obj.num_layers = loadgan.num_layers

            error_msg.set(msg)

            use_gen.set(True)
            is_loaded.set(False)

        except Exception:
            error_msg.set("Could not load generator. Is the filepath correct?")

        return

    def save_txt():
        save_name = fd.asksaveasfile(title='Save level (.txt/.png)', initialdir=os.path.join(os.curdir, "levels"), mode='w',
                                     defaultextension=".txt", filetypes=[("txt files", ".txt"), ("png files", ".png")])
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
            level = generate_sample(toadgan_obj.Gs, toadgan_obj.Zs, toadgan_obj.reals, toadgan_obj.NoiseAmp,
                                    toadgan_obj.num_layers, toadgan_obj.token_list).cpu()
            level_obj.oh_level = level
            level_obj.ascii_level = one_hot_to_ascii_level(level, toadgan_obj.token_list)
            m_exists = False
            for line in level_obj.ascii_level:
                if 'M' in line:
                    m_exists = True
            if not m_exists:
                level_obj.ascii_level = place_a_mario_token(level_obj.ascii_level)
            level_obj.tokens = toadgan_obj.token_list

            img = ImageTk.PhotoImage(ImgGen.render(level_obj.ascii_level))

            level_obj.image = img

            is_loaded.set(True)
            print("Level generated!")
            error_msg.set("Level generated!")
        return

    def play_level():
        error_msg.set("Playing level...")
        gateway = JavaGateway.launch_gateway(classpath=MARIO_AI_PATH, die_on_exit=True)
        game = gateway.jvm.engine.core.MarioGame()
        result = game.playGame(''.join(level_obj.ascii_level), 200)
        game.getWindow().dispose()
        perc = int(result.getCompletionPercentage() * 100)
        gateway.java_process.kill()
        gateway.close()
        error_msg.set("Level Played. Completion Percentage: %d%%" % perc)
        return

    # Make layout
    settings = ttk.Frame(root, padding=(15, 15, 15, 15), width=1000, height=1000)

    banner = ttk.Label(settings, image=banner_icon)
    welcome_message = ttk.Label(settings, text="Welcome to TOAD-GUI, a Framework to view and playtest Mario levels "
                                               "generated by TOAD-GAN.", width=95)

    fpath_label = ttk.Label(settings, textvariable=load_string_gen, width=100)
    load_lev_button = ttk.Button(settings, compound='top', image=load_level_icon, width=35,
                                 text='Open Level', command=lambda: spawn_thread(q, load_level))
    load_gen_button = ttk.Button(settings, compound='top', image=load_generator_icon, width=35,
                                 text='Open Generator', command=lambda: spawn_thread(q, load_generator))

    gen_button = ttk.Button(settings, compound='top', image=generate_level_icon,
                            text='Generate level', state='disabled', command=lambda: spawn_thread(q, generate))
    save_button = ttk.Button(settings, compound='top', image=save_level_icon,
                             text='Save Level/Image', state='disabled', command=lambda: spawn_thread(q, save_txt))

    def set_button_state(t1, t2, t3):
        if use_gen.get():
            gen_button.state(['!disabled'])
            save_button.state(['!disabled'])
        else:
            gen_button.state(['disabled'])
            save_button.state(['disabled'])
        return

    use_gen.trace("w", callback=set_button_state)

    p_c_frame = ttk.Frame(settings)
    play_button = ttk.Button(p_c_frame, compound='top', image=play_level_icon,
                             text='Play level', state='disabled', command=lambda: spawn_thread(q, play_level))

    prev_label = ttk.Label(settings, text='Preview:')
    image_label = ScrollableImage(settings, image=levelimage, height=271)

    def set_play_state(t1, t2, t3):
        if is_loaded.get():
            play_button.state(['!disabled'])
            image_label.change_image(level_obj.image)
        else:
            play_button.state(['disabled'])
        return

    is_loaded.trace("w", callback=set_play_state)

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

    # Pack layout to grid
    settings.grid(column=0, row=0, sticky=(N, S, E, W))
    banner.grid(column=1, row=0, columnspan=2, sticky=(N, S), padx=5, pady=5)
    welcome_message.grid(column=1, row=1, columnspan=2, sticky=(N, S), padx=5, pady=10)
    load_lev_button.grid(column=2, row=3, sticky=(N, S, E, W), padx=5, pady=5)
    load_gen_button.grid(column=1, row=3, sticky=(N, S, E, W), padx=5, pady=5)
    gen_button.grid(column=1, row=4, sticky=(N, S, E, W), padx=5, pady=5)
    save_button.grid(column=2, row=4, sticky=(N, S, E, W), padx=5, pady=5)
    prev_label.grid(column=0, row=5, columnspan=4, sticky=(S, W), padx=5, pady=5)
    image_label.grid(column=0, row=6, columnspan=4, sticky=(N, E, W), padx=5, pady=5)
    p_c_frame.grid(column=1, row=7, columnspan=2, sticky=(N, S, E, W), padx=5, pady=5)
    fpath_label.grid(column=0, row=9, columnspan=4, sticky=(S, E, W), padx=5, pady=10)
    error_label.grid(column=0, row=10, columnspan=4, sticky=(S, E, W), padx=5, pady=1)

    play_button.grid(column=0, row=0, sticky=(N, S, E, W), padx=5, pady=5)
    controls_frame.grid(column=1, row=0, sticky=(N, S, E, W), padx=5, pady=5)

    contr_a.grid(column=0, row=0, sticky=(N, S, E), padx=1, pady=1)
    contr_s.grid(column=0, row=1, sticky=(N, S, E), padx=1, pady=1)
    contr_l.grid(column=0, row=2, sticky=(N, S, E), padx=1, pady=1)
    contr_r.grid(column=0, row=3, sticky=(N, S, E), padx=1, pady=1)
    descr_a.grid(column=1, row=0, sticky=(N, S, W), padx=1, pady=1)
    descr_s.grid(column=1, row=1, sticky=(N, S, W), padx=1, pady=1)
    descr_l.grid(column=1, row=2, sticky=(N, S, W), padx=1, pady=1)
    descr_r.grid(column=1, row=3, sticky=(N, S, W), padx=1, pady=1)

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
    settings.rowconfigure(6, weight=1)
    settings.rowconfigure(10, weight=1)

    p_c_frame.columnconfigure(0, weight=2)
    p_c_frame.columnconfigure(0, weight=1)
    p_c_frame.rowconfigure(0, weight=1)

    controls_frame.columnconfigure(0, weight=1)
    controls_frame.columnconfigure(1, weight=1)
    controls_frame.rowconfigure(0, weight=1)
    controls_frame.rowconfigure(1, weight=1)
    controls_frame.rowconfigure(2, weight=1)
    controls_frame.rowconfigure(3, weight=1)

    # Move scrollbar to middle (to have message on the test image appear centered)
    root.after(1, image_label.move_scrollbar_to_middle)

    # Run Window
    root.mainloop()
