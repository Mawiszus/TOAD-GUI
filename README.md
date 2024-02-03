This project uses the mario implementation defined on the repository: https://github.com/Mawiszus/TOAD-GUI
the project uses the code made by Maren Awiszus, Frederik Schubert and Bodo Rosenhahn which is explained on the paper referenced here: https://ieeexplore.ieee.org/abstract/document/9390320/footnotes#footnotes

```
@inproceedings{awiszus2020toadgan,
  title={TOAD-GAN: Coherent Style Level Generation from a Single Example},
  author={Awiszus, Maren and Schubert, Frederik and Rosenhahn, Bodo},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment},
  year={2020}
}
```


<p align="center">
<img alt="TOAD-GUI_linux_example" src="/icons/TOAD-GUI_example.gif">
</p>

This project uses the [Mario-AI-Framework](https://github.com/amidos2006/Mario-AI-Framework) by [Ahmed Khalifa](https://scholar.google.com/citations?user=DRcyg5kAAAAJ&hl=en) and includes graphics from the game _Super Mario Bros._ **It is not affiliated with or endorsed by Nintendo.
The project was built for research purposes only.**

## Getting Started

This section includes the necessary steps to get TOAD-GUI running on your system.

### Python

You will need [Python 3](https://www.python.org/downloads) and the packages specified in requirements.txt.
We recommend setting up a [virtual environment with pip](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
and installing the packages there.

```
$ pip3 install -r requirements.txt -f "https://download.pytorch.org/whl/torch_stable.html"
```
Make sure you use the `pip3` that belongs to your previously defined virtual environment.

The GUI is made with [Tkinter](https://wiki.python.org/moin/TkInter), which from Python 3.7 onwards is installed by default.
If you don't have it installed because of an older version, follow the instructions [here](https://tkdocs.com/tutorial/install.html).

### Java

TOAD-GUI uses the [Mario-AI-Framework](https://github.com/amidos2006/Mario-AI-Framework) to play the generated levels.
For the Framework to run, [Java 11](https://adoptopenjdk.net/releases.html) (or higher) needs to be installed.

## Running TOAD-GUI

Once all prerequisites are installed, the project can be started by running main.py.
```
$ python main.py
```
Make sure you are using the python installation you installed the prerequisites into.


### TOAD-GAN

If you are interested in training your own Generator, refer to the [TOAD-GAN Github](https://github.com/Mawiszus/TOAD-GAN) and copy the folder of your trained generator into the `generators/` folder.
You should now be able to open it just like the provided generators.

The necessary files are:
```
generators.pth
noise_amplitudes.pth
noise_maps.pth
num_layer.pth
reals.pth
token_list.pth
```
Any other files can be deleted if you want to keep your folders tidy.

**NOTE:** When a generator is opened, it will not show these files in the dialog window. 
That is intended behavior for `askdirectory()` of tkinter. Just navigate to the correct path and click "Open" regardless.


## Known Bugs

* If the level play is quit using the window ('x' button in the corner), an **error message regarding py4j** will occur.
In spite of that, the program should continue running normally.


* If you have two monitors with different resolutions, the GUI and the Java window **might not be displayed in the correct resolution**.
Try moving the windows to the monitor with the other resolution if you encounter this problem.
You can also change the DPI awareness for the program in the beginning of GUI.py.

## Authors

* **[Francisco José Vargas Castro]** - Universidad de Sevilla

## Copyright

This program is not endorsed by Nintendo and is only intended for research purposes. 
Mario is a Nintendo character which the authors don’t own any rights to. 
Nintendo is also the sole owner of all the graphical assets in the game.

