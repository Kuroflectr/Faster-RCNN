import numpy as np 
import os
from glob import glob
import torch
import argparse
import time
from util import *

def __create_exp_folder(path, model_filename): 
    """ examine the current existing folders 
        and create a new one for storing the model
        input: 
            path: parent path, which is specified by the user

        output: 
            exp_number: expXX 
            file_name: {path}/exp{:0>2}/{weight_name(data set)}.{device}.pt
    """
    # experiment number
    exp_folder_list = glob('{}/exp*'.format(path))
    exp_number_list = np.array([x[-2:] for x in exp_folder_list]).astype(np.int32)

    # create a folder for saving the model
    if exp_number_list.size >= 1: 
        exp_number_list.sort()
        exp_number = exp_number_list[-1]+1
        os.mkdir('{}/exp{:0>2}/'.format(path,exp_number))
        os.mkdir('{}/exp{:0>2}/checkpoint/'.format(path,exp_number))
    else: 
        exp_number = 1
        os.mkdir('{}/exp{:0>2}/'.format(path,exp_number))
        os.mkdir('{}/exp{:0>2}/checkpoint/'.format(path,exp_number))

    # output model filename
    file_name = '{}/exp{:0>2}/{}.{}.pt'.format(path, exp_number, model_filename, device)
    print('The generated model will be saved to {}'.format(file_name))


    return exp_number, file_name


def __find_checkpoint_file(checkpoint_path): 
    """ fetch the newest checkpoint file under the specified .model/exp{exp_num} folder
    input: 
        checkpoint_path: path for the checkpoint files (e.g., ./model/exp01/checkpoint)

    output: 
        checkpoint_filename: the checkpoint generated 
    
    """
    if checkpoint_path != '/':
        checkpoint_path = checkpoint_path + '/'
        
    checkpoint_folder_list = glob(checkpoint_path+'*.pt',)
    checkpoint_number_list = np.sort(np.array([x[-6:-3] for x in checkpoint_folder_list]).astype(np.int32)) 
    checkpoint_number = checkpoint_number_list[-1]

    checkpoint_filename_found = checkpoint_path+'{:0>3}.pt'.format(checkpoint_number)
        
    return checkpoint_number, checkpoint_filename_found


def get_args_parser(known=False):
    
    parser = argparse.ArgumentParser('FRCNN training and evaluation script')

    # hyperparameter setting 
    parser.add_argument('--lr', default=0.005, type=float, help='learning rate')
    parser.add_argument('--epochs', default=10, type=int, help='epochs')
    parser.add_argument('--weight_decay', default=0.0005, type=float, )
    parser.add_argument('--momentum', default=0.9, type=float, )
    parser.add_argument('--batchsize', default=1, type=int, help='batch size of training data')
    parser.add_argument('--sample', default=10, type=int, help='sampling the dataset')
    
    parser.add_argument('--test', default=False, help='sampling the dataset')
    # load the checkpoint
    parser.add_argument('--load_checkpoint', 
        default=0, type=int, help='load the checkpoint file under ./model/expXX/checkpoint/. Specify the XX here')



    # model, backbone setting
    parser.add_argument('--device', default='cpu', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')  
    parser.add_argument('--backbone', default='mobilenet', help='backbone')
    parser.add_argument('--model', default='FRCNN', help='model')

    # path (input data, output.. etc.)
    parser.add_argument('--dataset_name', default='VOC2007', help='training data format. currently only')
    parser.add_argument('--path', default='./model', help='output folder of model')     
    parser.add_argument('--w', default='train_ALL_VOC2007', help='output model filename')
    parser.add_argument('--label', default='./dataset/VOCdevkit/VOC2007/Annotations/', help='data path')                  
    parser.add_argument('--data', default='./dataset/VOCdevkit/VOC2007/JPEGImages/', help='label path')  
    

    # others
    opt = parser.parse_known_args()[0] if known else parser.parse_args()
    # opt = parser.parse_known_args()[0]
    return opt

def train(train_dataloader, model, 
            path, model_filename, 
            lr=0.005, momentum=0.9, weight_decay=0.0005, num_epochs=10, device='cpu', 
            test_mode=False, load_checkpoint=None): 


    """ (3)モデルとパラメータ探索アルゴリズムの設定 """
    params      = [p for p in model.parameters() if p.requires_grad] 
    optimizer   = torch.optim.SGD(params, lr=lr, momentum=momentum, weight_decay=weight_decay) # パラメータ探索アルゴリズム
    print('Model training on {}'.format(device))


    """ (4)モデル学習 """

    # epoch number
    epoch0 = 0
    num_epochs = num_epochs

    # array for storing loss
    losses_array = np.array([])

    if load_checkpoint != None:
        # if loading the checkpoint file, applying the 1. epoch, 2. optimizer, 3. loss
        # and the output file would be placed at the same folder
        checkpoint_path = '{}/exp{:0>2}/checkpoint/'.format(path, load_checkpoint)
        print('load the checkpoint file under {}'.format(checkpoint_path))
        checkpoint_num, checkpoint_filename_found = __find_checkpoint_file(checkpoint_path)

        checkpoint = torch.load(checkpoint_filename_found)

        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        epoch0 = checkpoint['epoch']
        loss0 = checkpoint['loss']
        losses_array = np.append(loss0, losses_array)

        exp_number = load_checkpoint
        file_name = '{}/exp{:0>2}/{}.{}.pt'.format(path, exp_number, model_filename, device)
        

    else: 
        # derive the filename for saving the output model
        exp_number, file_name  = __create_exp_folder(path, model_filename)
        checkpoint_num = 0




    # turn into the training mode 
    model.train()

    
    iter = 0
    for epoch in range(epoch0, num_epochs):
        for i, batch in enumerate(train_dataloader):
            iter += 1

            images, targets, image_ids = batch 
            
            images = list(image.to(device) for image in images)
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            
            ##学習モードでは画像とターゲット（ground-truth）を入力する
            ##返り値はdict[tensor]でlossが入ってる。（RPNとRCNN両方のloss）
            try:
                loss_dict = model(images, targets)

            except ValueError:
                print(image_ids)

                pass
            else:
                losses = sum(loss for loss in loss_dict.values())
                loss_value = losses.item()
                losses_array = np.append(losses_array,loss_value )
            
                optimizer.zero_grad()
                losses.backward()
                optimizer.step()
        
                if (i+1) % 50== 0:
                    print(f"epoch #{epoch+1} batch #{i+1} iteration #{iter} loss: {loss_value}") 
                
                # save the general check point 
                if (iter) % 50 == 0: 
                    checkpoint_num += 1
                    checkpoint_name = '{}/exp{:0>2}/checkpoint/{:0>3}.pt'.format(path, exp_number, checkpoint_num)
                    torch.save({'epoch': epoch+1,  
                                'model_state_dict': model.state_dict(), 
                                'optimizer_state_dict': optimizer.state_dict(),
                                'loss': loss_value,  }, checkpoint_name)
                    print('save the checkpoint: {}'.format(checkpoint_name))

                
    

    # save the trained model
    torch.save(model, file_name)
    np.savez( '{}/exp{:0>2}/losses.npz'.format(path, exp_number), losses_array=losses_array)
    return  exp_number


def load_data_train(annotation_path, img_path, batch_size_train, sample=10):
    """ (1)データの準備  """
    # datasetの読み込み
    xml_dir     = annotation_path  #"dataset/VOCdevkit/VOC2007/Annotations/"
    image_dir   = img_path #"dataset/VOCdevkit/VOC2007/JPEGImages/"

    # debug 
    if len(glob(xml_dir)) == 0 or len(glob(image_dir)) == 0 : 
        print('cannot load the file from the specified folder. please confirm the data again. ')

    print('loading data from {}'.format(image_dir))

    # データをロード
    # batch_size_train = 5
    # batch_size_val = 1
    train_dataloader,_= dataloader(
        xml_dir,
        image_dir,
        batch_size_train=batch_size_train, 
        batch_size_val= 1, 
        sample=sample)
    # train_batches = train_dataloader.__len__()
    # val_batches = val_dataloader.__len__()
    return train_dataloader


def load_model_train(backbone='mobilenet', model_name='FRCNN', device='cpu'):

    if backbone == 'mobilenet' and model_name == 'FRCNN': 
        # create the model
        model  = model_1().to(device)  # create the defined model
    else: 
        print('not updated yet')

    return  model.train()


def output_log(args, elapse, exp_number, data_sample_number, test_mode=False): 

    batch_size_train    = args.batchsize
    path                = args.path 
    model_filename      = args.w
    lr                  = args.lr
    momentum            = args.momentum
    weight_decay        = args.weight_decay
    num_epochs          = args.epochs
    sample              = args.sample

    # calculate the sample number
    
    # calculate elapsed hours and minutes 
    elapse_min = int((elapse/3600-int(elapse/3600))*60)
    elapse_hr = int(elapse/3600)



    if test_mode: 
        path = './test'
    else: 
        # record the training information
        with open('{}/exp{:0>2}/var.dat'.format(path, exp_number), 'w') as f: 
            f.write('output model filename: {}\n'.format(model_filename))
            f.write('data sample number: {}\n'.format(data_sample_number))
            f.write('batch_size_train: {}\n'.format(batch_size_train))
            f.write('num_epochs: {}\n'.format(num_epochs))
            f.write('learning rate: {}\n'.format(lr))
            f.write('weight_decay: {}\n'.format(weight_decay))
            f.write('momentum: {}\n'.format(momentum))
            f.write('dataset is sampled at: 1/{}\n'.format(sample))
            f.write('time_elapsed: {} sec (~{}hr{}min)'.format(int(elapse),elapse_hr,elapse_min ))
        return 


if __name__ == "__main__": 

    
    """ fetch the arguments """
    args = get_args_parser()


    """ load training dataloader """
    # get args
    data_path   = args.data
    label_path  = args.label
    batchsize   = args.batchsize
    sample      = args.sample
    # load training data
    
    print('training size: {}'.format(batchsize))
    print(label_path)
    train_dataloader = load_data_train(label_path, data_path, batchsize, sample=sample)  

    # get args
    """ load the mask faster RCNN model """
    device      = args.device
    model_name  = args.model
    backbone    = args.backbone
    model = load_model_train(device=device)
    
    """ training process """
    # get args
    path            = args.path 
    model_filename  = args.w
    lr              = args.lr
    momentum        = args.momentum
    weight_decay    = args.weight_decay
    num_epochs      = args.epochs
    test_mode       = args.test


    print('num_epochs: {}'.format(num_epochs))

    print('start training')
    start_time = time.time()

    

    """ load the checkpoint if being specified """
    load_checkpoint = args.load_checkpoint
    if load_checkpoint != 0: 
        exp_number = train(train_dataloader, 
                model, 
                path, 
                model_filename, 
                lr=lr, momentum=momentum, weight_decay=weight_decay, num_epochs=num_epochs, 
                test_mode=test_mode, device=device,load_checkpoint=load_checkpoint )

    else: 
        exp_number = train(train_dataloader, 
        model, 
        path, 
        model_filename, 
        lr=lr, momentum=momentum, weight_decay=weight_decay, num_epochs=num_epochs, 
        test_mode=test_mode, device=device, )



    end_time = time.time()
    elapse = end_time-start_time    
    print('training end ')
    print('time elapse: {}'.format(elapse))


    """output the log"""
    data_sample_number = train_dataloader.dataset.__len__()
    output_log(args, elapse, exp_number, data_sample_number)


    

