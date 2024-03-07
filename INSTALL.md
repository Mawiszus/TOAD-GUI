
```sh
conda env create -f environment.yml
conda activate toad-gui
python main.py
```

If the program does fail to start, ensure that `torch` is NOT installed globally. If it is, remove it and retry running.
