# Faster-R-CNN


This code is written based on the Faster R-CNN tutorial provided by pytorch (https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html). 



## Environment  

```
# clone the repository 
$ git clone https://github.com/Kuroflectr/Faster-RCNN 
$ cd Faster-RCNN_lin 


# build a venv  
$ python3 -m venv venv 
$ source venv/bin/activate

# install all the necessary packages 
$ pip3 install --pre torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/nightly/cpu
$ pip install -r requirements.txt

```



## Dataset preparation

1. Download the training, validation, test data and VOCdevkit

```
$ wget http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtrainval_06-Nov-2007.tar
$ wget http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtest_06-Nov-2007.tar       # optional 
$ wget http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCdevkit_08-Jun-2007.tar

```

2. Extract all of these tars into one directory named `VOCdevkit`

```
$ tar xvf VOCtrainval_06-Nov-2007.tar
$ tar xvf VOCtest_06-Nov-2007.tar           # optional
$ tar xvf VOCdevkit_08-Jun-2007.tar
```

3. It should have this basic structure

```
$ VOCdevkit/                           # development kit
$ VOCdevkit/VOCcode/                   # VOC utility code
$ VOCdevkit/VOC2007                    # image sets, annotations, etc.
# ... and several other directories ...

```

4. `mv` the `VOCdevkit` folder under `dataset`
```
$ mkdir dataset
$ mv -r VOCdevkit  ./dataset/

```


## Create the folders for placing the outputs 


```
% mkdir model/              # trained models
% mkdir eval/               # evaluation results (metics ... etc.)
% mkdir detect/             # detection results (images)

```


## Training


training a faster R-CNN model (training with PASCAL VOC 2007 data by default) via: 

```
$ python trainer.py  --batchsize 5  --epochs 20
```

if you'd like to accerlate the training, using `--device cuda` flag

```
$ python trainer.py  --batchsize 5  --epochs 20 --device cuda
```

the output (trained model, log ...etc.) will bw placed under `./model/exp{$experiment_number}`: 
```
$ ls -l exp30 
drwxr-xr-x  12 hayashi  staff        384 Aug 23 19:00 checkpoint
-rw-r--r--   1 hayashi  staff       3094 Aug 23 19:00 losses.npz
-rw-r--r--   1 hayashi  staff  166143917 Aug 23 19:00 train_ALL_VOC2007.cpu.pt
-rw-r--r--   1 hayashi  staff        216 Aug 23 19:00 var.dat
```

- `checkpoint` checkpoint files are placed under this folder.
- `losses.npz` records the losses of every iteration.
- `train_ALL_VOC2007.{$device}.pt` is the trained model.
-  `var.dat` records the information of the training. It should be like: 


```
$ cat var.dat 
output model filename: train_ALL_VOC2007
data sample number: 351
batch_size_train: 1
num_epochs: 20
learning rate: 0.005
weight_decay: 0.0005
momentum: 0.9
dataset is sampled at: 1/10
time_elapsed: 37987 sec (~10hr33min)

```

Training from the supended session with `--load_checkpoint` flag 
(e.g., make use the checkpoint under `./model/exp06/checkpoint`) : 

```
$ python trainer.py  --epoch 1  --load_checkpoint 6 
```





Use `python trainer.py --help` for more information about the arguments: 

```
$ python trainer.py --help 
usage: FRCNN training and evaluation script [-h] [--lr LR] [--epochs EPOCHS]
                                            [--weight_decay WEIGHT_DECAY] [--momentum MOMENTUM]
                                            [--batchsize BATCHSIZE] [--sample SAMPLE]
                                            [--test TEST] [--device DEVICE]
                                            [--backbone BACKBONE] [--model MODEL]
                                            [--dataset_name DATASET_NAME] [--path PATH] [--w W]
                                            [--label LABEL] [--data DATA]
...
```

## Evaluation

Evaluating the training result (which is under the `./model/exp{$experiment_number}/` folder) via: 

```
$ experiment_number=1           # for example, the trained model is under ./model/exp01
$ python evaluater.py --exp $experiment_number
```
The evaluation result will be output to `./eval/`: 

```
$ ls -l
total 24
-rw-r--r--  1 hayashi  staff   342 Jul 19 18:41 result_metric.dat
-rw-r--r--  1 hayashi  staff  5157 Jul 19 16:02 result_metric.npz
```


- `result_metric.npz` records the metrics for evaluating the training result. 
- `result_metric.dat` shows the values of the metrics, which is like: 

```
$ cat result_metric.dat 
map: 17.16
map_50: 32.66
map_75: 17.46
map_small: 8.79
map_medium: 17.43
map_large: 24.76
map_per_class: -100.00
output model filename:  train_ALL_VOC2007
data sample number:  351
batch_size_train:  1
num_epochs:  10
learning rate:  0.005
weight_decay:  0.0005
momentum:  0.9
dataset is sampled at:  1/10
time_elapsed:  16807 sec (~4hr40min)
```

(meanings of the metrics can be found at https://jonathan-hui.medium.com/map-mean-average-precision-for-object-detection-45c121a31173 )



If you want to see the detetction result (images), set the `--plot_result` flag to True: 

```
$ experiment_number=1           # for example, the trained model is under ./model/exp01
$ python evaluater.py --exp $experiment_number --plot_result True
```

The resulting images would be under `./detect/exp{$experiment_number}/` folder, like: 

```
$ ls -l
total 182728
-rw-r--r--  1 hayashi  staff  297590 Jul 19 16:01 detection_id000005.png
-rw-r--r--  1 hayashi  staff  297429 Jul 19 16:01 detection_id000005_gt.png
-rw-r--r--  1 hayashi  staff  332888 Jul 19 16:00 detection_id000024.png
-rw-r--r--  1 hayashi  staff  328015 Jul 19 16:00 detection_id000024_gt.png
....
```


See more information of the arguments via `--help` flag: 


```
$ python evaluater.py --help 
usage: FRCNN detect and validation process  [-h] [--weights WEIGHTS] [--path PATH] --exp EXP
                                            [--device DEVICE] [--plot_result PLOT_RESULT]
                                            [--dataset_name DATASET_NAME] [--label LABEL]
                                            [--data DATA] [--sample SAMPLE]
                                            [--eval_output EVAL_OUTPUT]
                                            [--detect_output DETECT_OUTPUT]



```


