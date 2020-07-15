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
import torch

from utils.scrollable_image import ScrollableImage
from utils.level_utils import read_level_from_file, one_hot_to_ascii_level, place_a_mario_token, ascii_to_one_hot_level
from utils.level_image_gen import LevelImageGen
from utils.toad_gan_utils import load_trained_pyramid, generate_sample, TOADGAN_obj
from utils.sampling_tools import get_samples


MARIO_AI_PATH = os.path.abspath(os.path.join(os.path.curdir, "Mario-AI-Framework/mario-1.0-SNAPSHOT.jar"))

# Cheasck if windows user to make sure taskbar icon is correct
if platform.system() == "Windows":
    import ctypes
    my_appid = u'toad-gui.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)


class LevelObject:
    def __init__(self, ascii_level, oh_level, image, tokens, scales, noises):
        self.ascii_level = ascii_level
        self.oh_level = oh_level
        self.image = image
        self.tokens = tokens
        self.scales = scales
        self.noises = noises


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
                            current_level, levelimage, current_tokens, None, None)
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
            is_loaded.set(False)
            use_gen.set(False)
            if fname[-3:] == "txt":
                load_string_gen.set('Path: ' + fname)
                folder, lname = os.path.split(fname)

                lev, tok = read_level_from_file(folder, lname)

                level_obj.oh_level = torch.Tensor(lev)  # casting to Tensor to keep consistency
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

                level_obj.scales = None
                level_obj.noises = None

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
            use_gen.set(False)
            is_loaded.set(False)
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
            level, scales, noises = generate_sample(toadgan_obj.Gs, toadgan_obj.Zs, toadgan_obj.reals,
                                                    toadgan_obj.NoiseAmp, toadgan_obj.num_layers,
                                                    toadgan_obj.token_list)
            level_obj.oh_level = level.cpu()
            level_obj.scales = scales
            level_obj.noises = noises

            level_obj.ascii_level = one_hot_to_ascii_level(level, toadgan_obj.token_list)
            redraw_image()

            # for testing:
            # new_level, new_scales, new_noises = generate_sample(toadgan_obj.Gs, toadgan_obj.Zs, toadgan_obj.reals,
            #                                                     toadgan_obj.NoiseAmp, toadgan_obj.num_layers,
            #                                                     toadgan_obj.token_list, in_states=[scales, noises],
            #                                                     gen_start_scale=3)

            is_loaded.set(True)
            print("Level generated!")
            error_msg.set("Level generated!")
        return

    def redraw_image(edit_mode=False, rectangle=[(0, 0), (16, 16)], stat_mode=False, seed=(8*16, 8*16)):
        if is_loaded.get():
            m_exists = False
            for line in level_obj.ascii_level:
                if 'M' in line:
                    m_exists = True
            if not m_exists:
                level_obj.ascii_level = place_a_mario_token(level_obj.ascii_level)
            level_obj.tokens = toadgan_obj.token_list

            pil_img = ImgGen.render(level_obj.ascii_level)

            if edit_mode:
                # Add Visualizations for rows and bounding box
                l_draw = ImageDraw.Draw(pil_img)
                for y in range(level_obj.oh_level.shape[-2]):
                    l_draw.multiline_text((1, 4+y*16), str(y), (255, 255, 255),
                                          stroke_width=-1, stroke_fill=(0, 0, 0))
                for x in range(level_obj.oh_level.shape[-1]):
                    l_draw.multiline_text((6+x*16, 0), "".join(["%s\n" % c for c in str(x)]), (255, 255, 255),
                                          stroke_width=-1, stroke_fill=(0, 0, 0), direction='ttb', spacing=0, align='right')
                l_draw.rectangle(rectangle, outline=(255, 0, 0), width=2)
                if stat_mode:
                    ellipse = [(rectangle[0][0] + seed[0], rectangle[0][1] + seed[1]),
                               (rectangle[0][0] + seed[0] + 16, rectangle[0][1] + seed[1] + 16)]
                    l_draw.ellipse(ellipse, outline=(0, 255, 0), width=2)

            img = ImageTk.PhotoImage(pil_img)

            level_obj.image = img
            image_label.change_image(level_obj.image)

    def play_level():
        error_msg.set("Playing level...")
        use_gen.set(False)
        is_loaded.set(False)
        try:
            gateway = JavaGateway.launch_gateway(classpath=MARIO_AI_PATH, die_on_exit=True)
            game = gateway.jvm.engine.core.MarioGame()
            result = game.playGame(''.join(level_obj.ascii_level), 200)
            game.getWindow().dispose()
            perc = int(result.getCompletionPercentage() * 100)
            gateway.java_process.kill()
            gateway.close()
            error_msg.set("Level Played. Completion Percentage: %d%%" % perc)
        except Exception:
            error_msg.set("Level Play was interrupted unexpectedly.")
        use_gen.set(True)
        is_loaded.set(True)
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
        toggle_editmode(t1, t2, t3)
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
    fpath_label.grid(column=0, row=99, columnspan=4, sticky=(S, E, W), padx=5, pady=10)
    error_label.grid(column=0, row=100, columnspan=4, sticky=(S, E, W), padx=5, pady=1)

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
    settings.rowconfigure(6, weight=2)
    settings.rowconfigure(99, weight=1)
    settings.rowconfigure(100, weight=1)

    p_c_frame.columnconfigure(0, weight=2)
    p_c_frame.columnconfigure(0, weight=1)
    p_c_frame.rowconfigure(0, weight=1)

    controls_frame.columnconfigure(0, weight=1)
    controls_frame.columnconfigure(1, weight=1)
    controls_frame.rowconfigure(0, weight=1)
    controls_frame.rowconfigure(1, weight=1)
    controls_frame.rowconfigure(2, weight=1)
    controls_frame.rowconfigure(3, weight=1)

    # -------------------- Handling Editmode -----------------------------

    # Variables
    editmode = BooleanVar()
    bbox_x1 = IntVar()
    bbox_x2 = IntVar()
    bbox_y1 = IntVar()
    bbox_y2 = IntVar()
    temp = DoubleVar()
    edit_type = StringVar()
    seed_x = IntVar()
    seed_y = IntVar()
    seed_token = IntVar()
    edit_scale = IntVar()
    scale_info = StringVar()

    editmode.set(False)
    bbox_x1.set(0)
    bbox_x2.set(16)
    bbox_y1.set(0)
    bbox_y2.set(16)
    temp.set(6)
    edit_type.set("tokenwise")
    seed_x.set(8)
    seed_y.set(8)
    seed_token.set(0)
    edit_scale.set(0)
    scale_info.set("Scale 0 window: 8x8")

    noise_holder = Image.new('RGB', (8, 8), (255, 255, 255))
    noiseimage = ImageTk.PhotoImage(noise_holder)

    # Widgets
    emode_box = ttk.Checkbutton(settings, text="Edit mode", variable=editmode)
    emode_box.grid(column=1, row=8, columnspan=2, sticky=(N, S, E, W), padx=5, pady=5)
    settings.rowconfigure(8, weight=1)

    emode_frame = ttk.LabelFrame(root, text="Edit mode controls", padding=(5, 5, 5, 5))
    type_switch_frame = ttk.Frame(emode_frame, padding=(0, 5, 0, 5))
    type_switch_label = ttk.Label(type_switch_frame, text="Edit Type:")
    type_switch_0 = ttk.Radiobutton(type_switch_frame, text="Tokenwise", variable=edit_type, value="tokenwise")
    type_switch_1 = ttk.Radiobutton(type_switch_frame, text="Statistics enhanced", variable=edit_type, value="stats")
    type_switch_2 = ttk.Radiobutton(type_switch_frame, text="TOAD-GAN resample", variable=edit_type, value="toadgan")

    bbox_frame = ttk.LabelFrame(emode_frame, text="Bounding Box", padding=(5, 5, 5, 5))

    def on_validate(inStr, act_type):
        if act_type == '1':  # insertion
            if not inStr.isdigit():
                return False
        return True

    x1_label = ttk.Label(bbox_frame, text="x1:", width=5, anchor="e")
    x1_entry = ttk.Entry(bbox_frame, textvariable=bbox_y1, validate="key", width=3, justify='right')
    x2_label = ttk.Label(bbox_frame, text="x2:")
    x2_entry = ttk.Entry(bbox_frame, textvariable=bbox_y2, validate="key", width=3, justify='right')
    y1_label = ttk.Label(bbox_frame, text=" y1:", width=5, anchor="e")
    y1_entry = ttk.Entry(bbox_frame, textvariable=bbox_x1, validate="key", width=3, justify='right')
    y2_label = ttk.Label(bbox_frame, text=" y2:")
    y2_entry = ttk.Entry(bbox_frame, textvariable=bbox_x2, validate="key", width=3, justify='right')
    t_label = ttk.Label(emode_frame, text="Determinism:")
    t_entry = ttk.Entry(emode_frame, textvariable=temp, validate="key", width=3, justify='right')

    stat_frame = ttk.Frame(emode_frame, padding=(0, 5, 0, 5))
    sx_label = ttk.Label(stat_frame, text="Seed x:")
    sx_entry = ttk.Entry(stat_frame, textvariable=seed_x, validate="key", width=3, justify='right')
    sy_label = ttk.Label(stat_frame, text="Seed y:")
    sy_entry = ttk.Entry(stat_frame, textvariable=seed_y, validate="key", width=3, justify='right')
    st_label = ttk.Label(stat_frame, text="Seed token:")
    st_entry = ttk.Entry(stat_frame, textvariable=seed_token, validate="key", width=3, justify='right')

    sc_frame = ttk.Frame(emode_frame, padding=(0, 5, 0, 5))
    sc_label = ttk.Label(sc_frame, text="Scale:")
    sc_entry = ttk.Entry(sc_frame, textvariable=edit_scale, validate="key", width=3, justify='right')
    sc_noise_image = ttk.Label(sc_frame, image=noiseimage)

    sc_info_label = ttk.Label(sc_frame, textvariable=scale_info)

    vcmd_x1 = (x1_entry.register(on_validate), '%P', '%d')
    vcmd_x2 = (x2_entry.register(on_validate), '%P', '%d')
    vcmd_y1 = (y1_entry.register(on_validate), '%P', '%d')
    vcmd_y2 = (y2_entry.register(on_validate), '%P', '%d')
    vcmd_t = (t_entry.register(on_validate), '%P', '%d')
    vcmd_sx = (sx_entry.register(on_validate), '%P', '%d')
    vcmd_sy = (sy_entry.register(on_validate), '%P', '%d')
    vcmd_st = (st_entry.register(on_validate), '%P', '%d')
    vcmd_sc = (sc_entry.register(on_validate), '%P', '%d')

    x1_entry.configure(validatecommand=vcmd_x1)
    x2_entry.configure(validatecommand=vcmd_x2)
    y1_entry.configure(validatecommand=vcmd_y1)
    y2_entry.configure(validatecommand=vcmd_y2)
    t_entry.configure(validatecommand=vcmd_t)
    sx_entry.configure(validatecommand=vcmd_sx)
    sy_entry.configure(validatecommand=vcmd_sy)
    st_entry.configure(validatecommand=vcmd_st)
    sc_entry.configure(validatecommand=vcmd_sc)

    resample_button = ttk.Button(emode_frame, text="Resample", state='disabled',
                                 command=lambda: spawn_thread(q, re_sample))
    confirm_sample_button = ttk.Button(emode_frame, text="Confirm", state='disabled',
                                       command=lambda: spawn_thread(q, confirm_sample))

    def re_sample():
        if not level_obj.scales:
            error_msg.set("Can't resample loaded level.")
        else:
            if edit_type.get() == "tokenwise":
                is_loaded.set(False)
                bbox = (bbox_x1.get(), bbox_x2.get(), bbox_y1.get(), bbox_y2.get())
                samples = get_samples(1, level_obj.oh_level, bbox, temp.get())
                tmp_lvl = level_obj.oh_level.clone()
                tmp_lvl[0, :, bbox[0]:bbox[1], bbox[2]:bbox[3]] = samples[0]
                level_obj.ascii_level = one_hot_to_ascii_level(tmp_lvl, toadgan_obj.token_list)
                redraw_image(True, rectangle=[(bbox_y1.get()*16, bbox_x1.get()*16), (bbox_y2.get()*16, bbox_x2.get()*16)])

                is_loaded.set(True)
            elif edit_type.get() == "stats":
                is_loaded.set(False)
                bbox = (bbox_x1.get(), bbox_x2.get(), bbox_y1.get(), bbox_y2.get())
                samples = get_samples(1, level_obj.oh_level, bbox, temp.get(),
                                      use_stats=True, stat_seed=(seed_y.get(), seed_x.get()),
                                      stat_tok_ind=seed_token.get(), curr_token_list=toadgan_obj.token_list)
                tmp_lvl = level_obj.oh_level.clone()
                tmp_lvl[0, :, bbox[0]:bbox[1], bbox[2]:bbox[3]] = samples[0]
                level_obj.ascii_level = one_hot_to_ascii_level(tmp_lvl, toadgan_obj.token_list)
                redraw_image(True, rectangle=[(bbox_y1.get()*16, bbox_x1.get()*16), (bbox_y2.get()*16, bbox_x2.get()*16)],
                             stat_mode=True, seed=(seed_y.get()*16, seed_x.get()*16))
                is_loaded.set(True)
            elif edit_type.get() == "toadgan":
                is_loaded.set(False)
                sc = level_obj.scales[edit_scale.get()].shape[-1] / level_obj.oh_level.shape[-1]
                scaled_bbox = (round(bbox_x1.get() * sc), round(bbox_x2.get() * sc),
                               round(bbox_y1.get() * sc), round(bbox_y2.get() * sc))

                new_states = [level_obj.scales, level_obj.noises]
                level, scales, noises = generate_sample(toadgan_obj.Gs, toadgan_obj.Zs, toadgan_obj.reals,
                                                        toadgan_obj.NoiseAmp, toadgan_obj.num_layers,
                                                        toadgan_obj.token_list, in_states=new_states,
                                                        gen_start_scale=edit_scale.get(), is_bboxed=True,
                                                        bbox=scaled_bbox)
                level_obj.oh_level = level.cpu()
                level_obj.scales = scales
                level_obj.noises = noises

                level_obj.ascii_level = one_hot_to_ascii_level(level, toadgan_obj.token_list)
                redraw_image()

                is_loaded.set(True)
            else:
                error_msg.set("Unknown resample mode. Check Radiobuttons.")

    def confirm_sample():
        bbox = (bbox_x1.get(), bbox_x2.get(), bbox_y1.get(), bbox_y2.get())
        tmp_ascii = torch.Tensor(ascii_to_one_hot_level(level_obj.ascii_level, toadgan_obj.token_list))
        level_obj.oh_level[0, :, bbox[0]:bbox[1], bbox[2]:bbox[3]] = tmp_ascii[:, bbox[0]:bbox[1], bbox[2]:bbox[3]]

    def toggle_editmode(t1, t2, t3):
        if editmode.get():
            # Grid all the things
            emode_frame.grid(column=1, row=0, columnspan=2, sticky=(E, W), padx=10)
            type_switch_frame.grid(column=0, row=0, columnspan=6, sticky=(N, S, E, W))
            type_switch_label.grid(column=0, row=0, rowspan=2, sticky=(N, S, E), padx=5)
            type_switch_0.grid(column=1, row=0, sticky=(N, S, E, W), padx=5)
            type_switch_1.grid(column=2, row=0, sticky=(N, S, E, W), padx=5)
            type_switch_2.grid(column=1, row=1, sticky=(N, S, E, W), padx=5)
            bbox_frame.grid(column=0, row=1, columnspan=3, sticky=(E, W), padx=5, pady=5)
            x1_label.grid(column=0, row=0, sticky=(N, S, E), padx=1, pady=1)
            x1_entry.grid(column=1, row=0, sticky=(N, S, W), padx=5, pady=1)
            x2_label.grid(column=0, row=1, sticky=(N, S, E), padx=1, pady=1)
            x2_entry.grid(column=1, row=1, sticky=(N, S, W), padx=5, pady=1)
            y1_label.grid(column=2, row=0, sticky=(N, S, E), padx=1, pady=1)
            y1_entry.grid(column=3, row=0, sticky=(N, S, W), padx=5, pady=1)
            y2_label.grid(column=2, row=1, sticky=(N, S, E), padx=1, pady=1)
            y2_entry.grid(column=3, row=1, sticky=(N, S, W), padx=5, pady=1)
            t_label.grid(column=3, row=1, sticky=(E), padx=1, pady=5)
            t_entry.grid(column=4, row=1, sticky=(W), padx=1, pady=5)
            resample_button.grid(column=0, row=5, columnspan=3, sticky=(N, S, E, W), padx=5, pady=5)
            confirm_sample_button.grid(column=3, row=5, columnspan=3, sticky=(N, S, E, W), padx=5, pady=5)

            emode_frame.columnconfigure(0, weight=1)
            emode_frame.columnconfigure(1, weight=1)
            emode_frame.columnconfigure(2, weight=1)
            emode_frame.columnconfigure(3, weight=1)
            emode_frame.columnconfigure(4, weight=1)
            emode_frame.columnconfigure(5, weight=1)
            emode_frame.rowconfigure(0, weight=1)
            emode_frame.rowconfigure(1, weight=1)
            emode_frame.rowconfigure(2, weight=1)
            emode_frame.rowconfigure(3, weight=1)
            emode_frame.rowconfigure(4, weight=1)
            emode_frame.rowconfigure(5, weight=1)

            type_switch_frame.columnconfigure(0, weight=1)
            type_switch_frame.columnconfigure(1, weight=1)
            type_switch_frame.columnconfigure(2, weight=1)
            type_switch_frame.rowconfigure(0, weight=1)

            bbox_frame.columnconfigure(0, weight=1)
            bbox_frame.columnconfigure(1, weight=1)
            bbox_frame.columnconfigure(2, weight=1)
            bbox_frame.columnconfigure(3, weight=1)
            bbox_frame.rowconfigure(0, weight=1)
            bbox_frame.rowconfigure(1, weight=1)
            redraw_image(True, rectangle=[(bbox_y1.get()*16, bbox_x1.get()*16), (bbox_y2.get()*16, bbox_x2.get()*16)])
            update_scale_info(t1, t2, t3)

        else:
            # Hide all the things
            emode_frame.grid_forget()
            redraw_image(False)

    editmode.trace("w", callback=toggle_editmode)

    def switch_edit_type(t1, t2, t3):
        if edit_type.get() == "tokenwise":
            sc_frame.grid_forget()
            stat_frame.grid_forget()
        elif edit_type.get() == "stats":
            sc_frame.grid_forget()
            stat_frame.grid(column=0, row=3, columnspan=5, sticky=(N, S, E, W), padx=5, pady=5)
            sx_label.grid(column=0, row=0, sticky=(N, S, E), padx=1, pady=5)
            sx_entry.grid(column=1, row=0, sticky=(N, S, W), padx=1, pady=5)
            sy_label.grid(column=2, row=0, sticky=(N, S, E), padx=1, pady=5)
            sy_entry.grid(column=3, row=0, sticky=(N, S, W), padx=1, pady=5)
            st_label.grid(column=4, row=0, sticky=(N, S, E), padx=1, pady=5)
            st_entry.grid(column=5, row=0, sticky=(N, S, W), padx=1, pady=5)

            stat_frame.columnconfigure(0, weight=1)
            stat_frame.columnconfigure(1, weight=1)
            stat_frame.columnconfigure(2, weight=1)
            stat_frame.columnconfigure(3, weight=1)
            stat_frame.columnconfigure(4, weight=1)
            stat_frame.columnconfigure(5, weight=1)
        elif edit_type.get() == "toadgan":
            stat_frame.grid_forget()
            sc_frame.grid(column=0, row=3, columnspan=5, sticky=(N, S, E, W), padx=5, pady=5)
            sc_label.grid(column=0, row=0, columnspan=1, sticky=(N, S, E), padx=1, pady=5)
            sc_entry.grid(column=1, row=0, columnspan=1, sticky=(N, S, W), padx=1, pady=5)
            sc_info_label.grid(column=0, row=1, columnspan=2, sticky=(N, S, E, W), padx=1, pady=5)
            sc_noise_image.grid(column=0, row=2, columnspan=2, sticky=(N, S), padx=1, pady=5)

            sc_frame.columnconfigure(0, weight=1)
            sc_frame.columnconfigure(1, weight=1)
            sc_frame.rowconfigure(0, weight=1)
            sc_frame.rowconfigure(1, weight=1)
            sc_frame.rowconfigure(2, weight=1)
            edit_scale.set(0)

    edit_type.trace("w", callback=switch_edit_type)

    def update_scale_info(t1, t2, t3):
        try:
            # Correct bbox values
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
                                          (bbox_y2.get() * 16, bbox_x2.get() * 16)])
            scale_info.set(" Scale %d\n Noise amp: %.4f\n The bbox will be fitted to the noisemap.\n "
                           "This may result in changes outside of the bbox."
                           % (edit_scale.get(), toadgan_obj.NoiseAmp[edit_scale.get()]))
            sc = level_obj.scales[edit_scale.get()].shape[-1] / level_obj.oh_level.shape[-1]

            scaled_bbox = [(round(bbox_y1.get() * sc), round(bbox_x1.get() * sc)),
                           (round(bbox_y2.get() * sc), round(bbox_x2.get() * sc))]

            noise_holder = Image.fromarray(level_obj.noises[edit_scale.get()][0, 0, 3:-3, 3:-3].cpu().numpy()*255)
            noise_holder = noise_holder.convert('RGB')
            n_draw = ImageDraw.Draw(noise_holder, 'RGBA')
            n_draw.rectangle(scaled_bbox, fill=(255, 0, 0, 128))
            noise_holder = noise_holder.resize((noise_holder.size[0] * 2, noise_holder.size[1] * 2), Image.NEAREST)
            noiseimage = ImageTk.PhotoImage(noise_holder)
            sc_noise_image.configure(image=noiseimage)
            sc_noise_image.image = noiseimage

            resample_button.state(['!disabled'])
            confirm_sample_button.state(['!disabled'])
        except TclError:
            scale_info.set("No scale")
            resample_button.state(['disabled'])
            confirm_sample_button.state(['disabled'])
        except IndexError:
            scale_info.set("Scale out of range")
            resample_button.state(['disabled'])
            confirm_sample_button.state(['disabled'])
        except TypeError:
            scale_info.set("No editable level loaded")
            noise_holder = Image.new('RGB', (8, 8), (255, 255, 255))
            noiseimage = ImageTk.PhotoImage(noise_holder)
            sc_noise_image.configure(image=noiseimage)
            sc_noise_image.image = noiseimage
            resample_button.state(['disabled'])
            confirm_sample_button.state(['disabled'])

    edit_scale.trace("w", callback=update_scale_info)
    bbox_x1.trace("w", callback=update_scale_info)
    bbox_x2.trace("w", callback=update_scale_info)
    bbox_y1.trace("w", callback=update_scale_info)
    bbox_y2.trace("w", callback=update_scale_info)

    root.update()
    # Move scrollbar to middle (to have message on the test image appear centered)
    root.after(1, image_label.move_scrollbar_to_middle)

    # Run Window
    root.mainloop()
