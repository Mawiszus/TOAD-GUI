# TOAD-GUI

TOAD-GUI is a Framework with which Super Mario Bros. levels can be randomly generated, loaded and saved.
Generation is done with pre-trained TOAD-GAN. 
For more information on TOAD-GAN, please refer to the paper (link to be added) and the github (link to added).

<br/>
<p align="center">
<img alt="TOAD-GUI linux example" src="https://tntgit:3000/awiszus/TOAD-GUI/media/branch/master/icons/TOAD_GUI_example.gif">
</p>
<br/>

This project uses the [Mario-AI-Framework](http://marioai.org/) by [Ahmed Khalifa](https://scholar.google.com/citations?user=DRcyg5kAAAAJ&hl=en) and includes graphics from the game _Super Mario Bros._ **It is not affiliated with or endorsed by Nintendo.
The project was built for research purposes only.**

## Getting Started

This section includes the necessary steps to get TOAD-GUI running on your system.

### Python

You will need [Python 3](https://www.python.org/downloads) and the packages specified in requirements.txt.
We recommend setting up a [virtual environment with pip](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
and installing the packages there.

As TOAD-GAN uses **Pytorch** for its networks, we will need to install that, too.
The Pytorch package needed can be very different depending on your system, so `pip3 install torch` will not work directly.
Use the "Quick Start Locally" guide on [Pytorch.org](https://pytorch.org) to determine the correct package to install for your System.
Afterwards, you can install all other requirements with:
```
$ pip3 install -r requirements.txt
```
Make sure you use the `pip3` that belongs to your previously defined virtual environment.

### Java

TOAD-GUI uses the [Mario-AI-Framework](http://marioai.org/) to play the generated levels.
For the Framework to run, [Java](https://www.java.com/de/download/) needs to be installed.

## Running TOAD-GUI

Once all prerequisites are installed, TOAD-GUI can be started by running main.py.
```
$ python main.py
```
Make sure you are using the python installation you installed the prerequisites into.

### TOAD-GUI

When running TOAD-GUI you can:
* ![toad folder](icons/folder_toad.png) Open a Generator (TOAD-GAN)
* ![level folder](icons/folder_level.png) Open a (previously saved) level `.txt` to view and/or play
* ![gear toad](icons/gear_toad.png) Generate a level of the size defined in the entries below
* ![save button](icons/save_button.png) Save the currently loaded level level to a `.txt` or `.png` image file
* ![play button](icons/play_button.png) Play the currently loaded level

When a level is loaded, **right clicking** a point in the preview will allow you to change the token at that specific spot.
If you resample the level, any changes made will be lost.

The labels at the bottom will display the currently loaded path and information. 
This program was made mostly by one researcher and is not optimized.
Impatiently clicking buttons might crash the program.

#### Edit Mode
In this mode, parts of a generated level can be resampled with TOAD-GAN. 
The red bounding box shows the area to be changed, while the yellow bounding box shows which blocks can still be affected by that change.
The area of effect depends on the scale which is to be resampled and is a result of the Field of View produced by the convolutional layers.
Changes in a lower scale will result in larger changes in the final level.

![BBox example](icons/TOAD-GUI_crop.gif) ![Resample Scale 3](icons/TOAD-GUI_resample_sc3.gif) ![Resample Scale 0](icons/TOAD-GUI_resample_sc0.gif) ![Rightclick Edit](icons/TOAD-GUI_rightclick.gif)

### TOAD-GAN

If you are interested in training your own Generator, refer to the TOAD-GAN github and copy the folder of your trained generator into the `generators/` folder.
You should now be able to open it just like the provided generators.

## Known Bugs

* If the level play is quit using the window ('x' button in the corner), an error message regarding py4j will occur.
In spite of that, the program should continue running normally.

## Built With

* Tkinter - Python package for building GUIs
* py4j - Python to Java interface
* Pillow - Python Image Library for displaying images
* Pytorch - Deep Learning Framework
* Maven - Used for building the Mario-AI-Framework

## Authors

* **Maren Awiszus** - Institut für Informationsverarbeitung, Leibniz University Hanover
* **Frederik Schubert** - Institut für Informationsverarbeitung, Leibniz University Hanover

## Copyright

This program is not endorsed by Nintendo and is only intended for research purposes. 
Mario is a Nintendo character which the authors don’t own any rights to. 
Nintendo is also the sole owner of all the graphical assets in the game. 
Any use of this program is expected to be on a non-commercial basis. 

