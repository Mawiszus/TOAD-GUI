# based on https://stackoverflow.com/questions/56043767/show-large-image-using-scrollbar-in-python/56043976
from tkinter import *
from tkinter import ttk
import platform


class ScrollableImage(Canvas):
    def __init__(self, master=None, **kw):
        self.image = kw.pop('image', None)
        super(ScrollableImage, self).__init__(master=master, **kw)
        self.is_first_level = False
        self['highlightthickness'] = 0
        self.propagate(0)  # wont let the scrollbars rule the size of Canvas
        self.create_image(0, 0, anchor='nw', image=self.image, tag='image')

        # Vertical and Horizontal scrollbars
        self.v_scroll = ttk.Scrollbar(self, orient='vertical')
        self.h_scroll = ttk.Scrollbar(self, orient='horizontal')
        self.v_scroll.pack(side='right', fill='y')
        self.h_scroll.pack(side='bottom', fill='x')
        # Set the scrollbars to the canvas
        self.config(xscrollcommand=self.h_scroll.set,
                    yscrollcommand=self.v_scroll.set)
        # Set canvas view to the scrollbars
        self.v_scroll.config(command=self.yview)
        self.h_scroll.config(command=self.xview)
        # Assign the region to be scrolled
        self.config(scrollregion=self.bbox('all'))

        self.focus_set()

        # Bind Mousewheel
        if platform.system() == 'Linux':
            self.bind_class(self, "<Button-4>", self.mouse_scroll)
            self.bind_class(self, "<Button-5>", self.mouse_scroll)
        else:
            self.bind_class(self, "<MouseWheel>", self.mouse_scroll)

    def mouse_scroll(self, evt):
        if evt.state == 0:
            if platform.system() == 'Windows':
                self.xview_scroll(int(-1*(evt.delta/120)), 'units')  # For windows
            elif platform.system() == 'Linux':
                delta = 1 if evt.num == 4 else -1
                self.xview_scroll(-1 * delta, 'units')  # For Linux
            else:
                self.xview_scroll(-1*evt.delta, 'units')  # For MacOS
        if evt.state == 1:
            if platform.system() == 'Windows':
                self.yview_scroll(int(-1*(evt.delta/120)), 'units')  # For windows
            elif platform.system() == 'Linux':
                delta = 1 if evt.num == 4 else -1
                self.xview_scroll(-1 * delta, 'units')  # For Linux
            else:
                self.yview_scroll(-1*evt.delta, 'units')  # For MacOS

    def change_image(self, im):
        # Set new image
        self.image = im
        self.delete('image')
        self.create_image(0, 0, anchor='nw', image=self.image, tag='image')
        # Assign the region to be scrolled
        scroll_bbox = self.bbox('image')
        self.config(scrollregion=(scroll_bbox[0], scroll_bbox[1], scroll_bbox[2]+17, scroll_bbox[3]+17))

        # If it's the first loaded level scroll to the beginning (placeholder can move scrollbar)
        if not self.is_first_level:
            self.xview_moveto(0)
            self.is_first_level = True

    def move_scrollbar_to_middle(self):
        x1, x2 = self.xview()
        self.xview_moveto(0.5 - (x2-x1)/2)
