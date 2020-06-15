# source https://stackoverflow.com/questions/56043767/show-large-image-using-scrollbar-in-python/56043976
from tkinter import *
from tkinter import ttk


class ScrollableImage(Canvas):
    def __init__(self, master=None, **kw):
        self.image = kw.pop('image', None)
        super(ScrollableImage, self).__init__(master=master, **kw)
        self['highlightthickness'] = 0
        self.propagate(0)  # wont let the scrollbars rule the size of Canvas
        self.create_image(0, 0, anchor='nw', image=self.image)
        # Vertical and Horizontal scrollbars
        self.v_scroll = ttk.Scrollbar(self, orient='vertical')  # , width=6)
        self.h_scroll = ttk.Scrollbar(self, orient='horizontal')  # , width=6)
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
        self.bind_class(self, "<MouseWheel>", self.mouse_scroll)

    def mouse_scroll(self, evt):
        if evt.state == 0:
            # self.yview_scroll(-1*(evt.delta), 'units') # For MacOS
            self.xview_scroll(int(-1*(evt.delta/120)), 'units')  # For windows
        if evt.state == 1:
            # self.xview_scroll(-1*(evt.delta), 'units') # For MacOS
            self.yview_scroll(int(-1*(evt.delta/120)), 'units')  # For windows

    def change_image(self, im):
        self.image = im
        self.create_image(0, 0, anchor='nw', image=self.image)
        # Assign the region to be scrolled
        self.config(scrollregion=self.bbox('all'))
        self.xview_moveto(0)

        # Known Bug: When loading a smaller image after loading a larger one, the scrollbar will not shrink to that
        # image again.

    def move_scrollbar_to_middle(self):
        x1, x2 = self.xview()
        self.xview_moveto(0.5 - (x2-x1)/2)

