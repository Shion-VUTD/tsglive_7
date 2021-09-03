# -*- coding: utf-8 -*-
"""TSG_LIVE7_demo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B1U529dF_FzQeltGS0JgtVmxyi_4ypNC

#1-1 学習済みデータセットを用いた推論
"""

import os
import urllib.request
import zipfile

# フォルダ「data」が存在しない場合は作成する
data_dir = "./data/"
if not os.path.exists(data_dir):
    os.mkdir(data_dir)


# ImageNetのclass_indexをダウンロードする
# Kerasで用意されているものです
# https://github.com/fchollet/deep-learning-models/blob/master/imagenet_utils.py

url = "https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json"
save_path = os.path.join(data_dir, "imagenet_class_index.json")

if not os.path.exists(save_path):
    urllib.request.urlretrieve(url, save_path)


# 1.3節で使用するアリとハチの画像データをダウンロードし解凍します
# PyTorchのチュートリアルで用意されているものです
# https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html

url = "https://download.pytorch.org/tutorial/hymenoptera_data.zip"
save_path = os.path.join(data_dir, "hymenoptera_data.zip")

if not os.path.exists(save_path):
    urllib.request.urlretrieve(url, save_path)

    # ZIPファイルを読み込み
    zip = zipfile.ZipFile(save_path)
    zip.extractall(data_dir)  # ZIPを解凍
    zip.close()  # ZIPファイルをクローズ

    # ZIPファイルを消去
    os.remove(save_path)

!git clone https://github.com/YutaroOgawa/pytorch_advanced.git

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import json
from PIL import Image
import matplotlib.pyplot as plt
# %matplotlib inline
import torch
import torchvision
from torchvision import models,transforms

#学習済みモデルロード

#VGG-16モデルのインスタンス生成
use_pretrained = True
net = models.vgg16(pretrained=use_pretrained)
net.eval()

print(net)

class BaseTransform():
  """
  画像をリサイズし、色を標準化

  Attributes
  ----------
  resize : int（リサイズ先の画像の大きさ）
  mean : (R,G,B) 各色チャンネルの平均値
  std : (R,G,B) 各色チャンネルの標準偏差
  """
  def __init__(self,resize,mean,std):
    self.base_transform = transforms.Compose([
      transforms.Resize(resize),
      transforms.CenterCrop(resize),
      transforms.ToTensor(),
      transforms.Normalize(mean,std) #色情報の標準化                            
    ])

  def __call__(self,img):
    return self.base_transform(img)

#画像変形の動作を確認
image_path = "/content/pytorch_advanced/1_image_classification/data/goldenretriever-3724972_640.jpg"
img = Image.open(image_path)

resize = 224
mean = (0.485,0.456,0.406)
std = (0.229,0.224,0.225)
transform = BaseTransform(resize,mean,std)
image_tramsformed = transform(img)

img_transformed = image_tramsformed.numpy().transpose(1,2,0)
img_transformed = np.clip(img_transformed,0,1) #0から1に制限
plt.imshow(img_transformed)

ILSVRC_class_index = json.load(open('/content/data/imagenet_class_index.json','r'))
ILSVRC_class_index

#出力結果からラベルを予測する
class ILSVRCPredictor():
  """
  ILSVRCデータにに対するモデルの出力からラベルを求める

  Attributes
  ----------
  class_index:dictionary
  """
  def __init__(self,class_index):
    self.class_index = class_index

  def predict_max(self,out):
    """
    確率最大のラベルを出力
    """
    maxid = np.argmax(out.detach().numpy())
    predicted_label_name = self.class_index[str(maxid)][1]
    return predicted_label_name

predictor = ILSVRCPredictor(ILSVRC_class_index)
transform = BaseTransform(resize,mean,std)
img_transformed = transform(img)
inputs = img_transformed.unsqueeze_(0)

out = net(inputs)
result = predictor.predict_max(out)

print(result)

"""#1-2 Pytorchによるディープラーニング実装の流れ

Datasetの作成
"""

import glob
import os.path as osp
import random
from tqdm import tqdm

import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data

#データ前処理クラスを作成
class ImageTransform():
  """
  データを前処理するクラス

  Attribute(__init__の引数になるやつ)
  ---------
  resize: 短辺のサイズ
  mean:(R,G,B)
  std:(R,G,B)
  """

  def __init__(self,resize,mean,std):
    self.data_transform = {
      "train" : transforms.Compose([                               
        transforms.RandomResizedCrop(
            resize,scale=(0.5,1.0)
        ),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean,std)                                   
      ]),
      "val": transforms.Compose([
        transforms.Resize(resize),
        transforms.CenterCrop(resize),
        transforms.ToTensor(),
        transforms.Normalize(mean,std)                         
      ])
    }  

  def __call__(self,img,phase='train'):
    return self.data_transform[phase](img)

#画像前処理の動作を確認
image_path = '/content/pytorch_advanced/1_image_classification/data/goldenretriever-3724972_640.jpg'
img = Image.open(image_path)

resize = 224
mean = mean = (0.485,0.456,0.406)
std = (0.229,0.224,0.225)
transform = ImageTransform(resize,mean,std)
img_transformed = transform(img,phase = 'train')
img_transformed = img_transformed.numpy().transpose((1,2,0))
img_transformed = np.clip(img_transformed,0,1)
plt.imshow(img_transformed)

#画像のパスを作るリストを作成
def make_datapath_list(phase='train'):
  """
  引数：phase(train/val)
  ---------------------
  return : path_list

  """
  rootpath = '/content/data/hymenoptera_data/'
  target_path = osp.join(rootpath+phase+'/**/*.jpg')
  

  path_list = []
  for path in glob.glob(target_path):
     path_list.append(path)

  return path_list

make_datapath_list(phase='val')[0][35:39]

#いよいよデータセットを作っていくよ！
#今まで整備してきたのは…
#データ前処理クラス
#画像パスを取り出す関数

class HymenopteraDataset(data.Dataset): #別のクラスのインスタンス・メソッドをを継承したいなら、ここの引数として渡す！
  """
  アリとハチの画像のDatasetクラス。PythonのDatasetクラスを継承
  Attributes
  ----------
  file_list:画像のパスを格納するリスト
  transform:object 前処理クラスのインスタンス
  phase:'train'/'val' 学習か検証か設定

  """
  def __init__(self,file_list,transform,phase='train'):
    self.file_list = file_list
    self.transform = transform
    self.phase = phase

  def __len__(self):
    return len(self.file_list)

  def __getitem__(self,index):
    #画像取得、前処理
    img_path = self.file_list[index]   
    img = Image.open(img_path) 
    img_transformed = self.transform(img,self.phase)

    #正解ラベルデータ取得・数値に変換
    if self.phase == 'train':
      label = img_path[37:41]
    elif self.phase =='val':
      label = img_path[35:39]

    if label == 'ants':
      label = 0

    elif label == 'bees':
      label = 1

    return img_transformed,label

#実際にデータを取り出してみよう！
train_list = make_datapath_list(phase='train')
val_list = make_datapath_list(phase='val')
train_dataset = HymenopteraDataset(train_list,transform,phase='train')
val_dataset = HymenopteraDataset(val_list,transform,phase='val')

print(train_dataset.__getitem__(0)[0].size())
print(train_dataset.__getitem__(0)[1])

"""DataLoaderの作成"""

batch_size = 32
train_dataloader = torch.utils.data.DataLoader(train_dataset,batch_size=batch_size,shuffle=True)
val_dataloader = torch.utils.data.DataLoader(val_dataset,batch_size=batch_size,shuffle=False)

dataloaders_dict = {"train":train_dataloader, "val":val_dataloader}

#動作確認
batch_iterator = iter(dataloaders_dict['train'])
inputs,labels = next(batch_iterator)
print(inputs.size())
print(labels)

"""モデルの作成"""

#今回は学習済みVGG-16モデルを使用
#最終出力層だけ変更

use_pretrained = True
net = models.vgg16(pretrained=True)
net.classifier[6] = nn.Linear(in_features=4096,out_features=2)

#訓練モードに
net.train()

"""損失関数の定義"""

criterion = nn.CrossEntropyLoss()

"""最適化手法を定義"""

net.named_parameters()

#今回は転移学習をするので、最終層のパラメータだけ勾配計算に加える
params_to_update=[]
update_param_names = ["classifier.6.weight","classifier.6.bias"]

for name,param in net.named_parameters():
  if name in update_param_names:
    param.requires_grad = True
    print(name)
    params_to_update.append(param)
  else:
    param.requires_grad = False

optimizer = optim.SGD(params=params_to_update,lr=0.001,momentum=0.9)

"""学習・検証"""

#訓練用の関数

def train_model(net,dataloaders_dict,criterion,optimizer,num_epochs):
  for epoch in range(num_epochs):
    print("Epoch:{}/{}".format(epoch+1,num_epochs))
    print("======================================")

    for phase in ["train","val"]:
      if phase == "train":
        net.train() #訓練モードに
      else:
        net.eval() #検証モードに

      epoch_loss = 0.0 #epochの損失和
      epoch_corrects = 0 #epochの正解数

      #未学習時の検証性能を確かめるため、epoch=0の訓練は省略
      if (epoch == 0) and (phase == 'train'): 
        continue
      #データローダからミニバッチを取り出すループ
      for inputs,labels in tqdm(dataloaders_dict[phase]):
        #勾配初期化
        optimizer.zero_grad()

        #順伝播(forward)計算
        with torch.set_grad_enabled(phase=='train'):
          outputs = net(inputs) #model(入力)で順伝播してくれるやつ
          loss = criterion(outputs,labels) #nn.criterion(出力、正解ラベル)
          _,preds = torch.max(outputs,1) #なんだこれ（出力(,2)からラベル返すやつ）

          #訓練時のみ逆伝播
          if phase == 'train':
            loss.backward()
            optimizer.step() #optimizer.stepでパラメータを更新する


          #iteration結果の計算
          #loss合計を更新（なんでepoch全体で足してるんだ？？）
          epoch_loss += loss.item()*inputs.size(0)
          """
          ここでなにしてるのかと言いますと
          モチベーションとしては
          "epochごとのlossの総和を取りたい！！"
          そのために、各iterationごとに
          "バッチごとのlossの平均"* "バッチ数"をたしあわせている
          """
          #正解数の合計を更新
          epoch_corrects += torch.sum(preds==labels.data)

      #epochごとのlossと正解率を表示
      epoch_loss = epoch_loss / len(dataloaders_dict[phase].dataset) #損失平均
      #1epochは、バッチ抽出を繰り返してのべdataset全体と同じ枚数を抽出した時の回数だから
      epoch_acc = epoch_corrects.double()/len(dataloaders_dict[phase].dataset)

      print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase,epoch_loss,epoch_acc))

#実行！！！
num_epochs = 2
train_model(net,dataloaders_dict,criterion,optimizer,num_epochs)

"""##GPUを使った学習の実装

休憩おわり
ねー1から学習するのってどーやるんだろーね
ってことでやってみようー
"""

models.resnet34()

#とりあえずmodelとoptimizerは変える必要 is ありそう
#ランタイプをGPUにするの忘れない
net2 = models.resnet34(pretrained = False)
net2.fc = nn.Linear(in_features=512,out_features=2)

optimizer = optim.Adam(net2.parameters())

#訓練なう
num_epochs = 10
train_model(net2,dataloaders_dict,criterion,optimizer,num_epochs)

"""回してる間暇だからちゃんとしたやつ実装する"""

import torch.nn.functional as F

resize = 28
mean = (0.485)
std = (0.225)
transform_mnist = BaseTransform(resize,mean,std)

#なんもわからん
#とりまデータセットいるよな
#なんにしよう
# Mnist? （なにも思いつかない…）ImageNetのやつでもいいか…
#Mnist ならこんな大きいモデルいらんのよな

#結局ResNetでMnistやってみることにする（大袈裟）
#valデータめんどくさかったのでtestで代用（だめ）
train_size = 48000
val_size = 12000

trainval_set = torchvision.datasets.MNIST(root='./data', 
                                        train=True,
                                        download=True,
                                        transform=transform_mnist)

trainset, valset = torch.utils.data.random_split(trainval_set, [train_size, val_size])

testset = torchvision.datasets.MNIST(root='./data', 
                                        train=False, 
                                        download=True, 
                                        transform=transform_mnist)

mnistdataloader_train = torch.utils.data.DataLoader(trainset,batch_size=32,shuffle=True)
mnistdataloader_val = torch.utils.data.DataLoader(valset,batch_size=32,shuffle=False)
mnist_dataloader_dict = {"train":mnistdataloader_train,"val":mnistdataloader_val}

net_formnist = models.resnet34(pretrained = False)
net_formnist.fc = nn.Linear(in_features=512,out_features=10)
optimizer = optim.Adam(net_formnist.parameters())

#訓練なう
num_epochs = 2
train_model(net2,dataloaders_dict,criterion,optimizer,num_epochs)

#なんかMnistでResNetやんのなんか微妙なので自分でNet組んだ（しょぼいやつ）
class Net(nn.Module):
  def __init__(self): #層をインスタンス化
    super(Net,self).__init__() #継承したnn.Modelの初期化関数を起動
    self.conv1 = nn.Conv2d(1,32,3) #チャネル数in_features=1（白黒なのでそれはそう),out_features=32,フィルター3×3
    self.conv2 = nn.Conv2d(32,64,3) 
    self.pool = nn.MaxPool2d(2,2)
    self.dropout1 = nn.Dropout2d()
    self.fc1 = nn.Linear(in_features=12*12*64,out_features=128)
    self.dropout2 = nn.Dropout2d()
    self.fc2 = nn.Linear(128,10)

  def forward(self,x):
    x = F.relu(self.conv1(x))
    x = self.pool(F.relu(self.conv2(x)))
    x = self.dropout1(x)
    x = x.view(-1,12*12*64)
    x = F.relu(self.fc1(x))
    x = self.dropout2(x)
    x = self.fc2(x)
    return x

net_mnist = Net()
net_mnist.parameters()

optimizer = optim.SGD(net_mnist.parameters(),lr=0.0001)

num_epochs = 30
train_model(net_mnist,mnist_dataloader_dict,criterion,optimizer,num_epochs=30)

"""この学習済みモデルを使って早押し機を作っていくっ

"""

def predict(input,net):
  out = net(input)
  #softmaxを入れる
  out = torch.exp(out)/torch.sum(torch.exp(out))
  pred = int(torch.argmax(out))
  if out[0][pred] >= 0.5:
    return pred
  else:
    return -1

testset[1][0].unsqueeze_(0).size()

question_1 = testset[1][0].unsqueeze_(0)
print(predict(question_1,net_mnist))

for i in range(10):
  print("======= question {} =======".format(i+1))
  question = testset[i][0].unsqueeze_(0)
  print("Answer is:",predict(question,net_mnist))
  print("The right answer is:",testset[i][1])

#テストデータの解像度下げれんかな
img_1 = testset[1][0]
img_1 = img_1.numpy().transpose((1,2,0)).reshape(28,28)
#print(img_1)
#こっから解像度下げるアルゴリズム…めんどくさい…
img_1dash = np.zeros((28,28))
for i in range(14):
  for j in range(14):
    img_1dash[2*i][2*j] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
    img_1dash[2*i+1][2*j] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
    img_1dash[2*i][2*j+1] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
    img_1dash[2*i+1][2*j+1] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
img_1dash = torch.from_numpy(img_1dash.astype(np.float32)).clone()
plt.imshow(img_1dash)

print(predict(img_1dash.unsqueeze_(0).unsqueeze_(0),net_mnist))

#テストデータの解像度下げれんかな
img_1 = testset[1][0]
img_1 = img_1.numpy().transpose((1,2,0)).reshape(28,28)
#print(img_1)
#こっから解像度下げるアルゴリズム…めんどくさい…
img_1dash = np.zeros((28,28))
for i in range(14):
  for j in range(14):
    img_1dash[2*i][2*j] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
    img_1dash[2*i+1][2*j] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
    img_1dash[2*i][2*j+1] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4    
    img_1dash[2*i+1][2*j+1] = (img_1[2*i][2*j]+img_1[2*i+1][2*j]+img_1[2*i][2*j+1]+img_1[2*i+1][2*j+1])/4 
    
       
img_1dash = torch.from_numpy(img_1dash.astype(np.float32)).clone()
plt.imshow(img_1dash)

#テストデータの解像度下げれんかな
img_1 = testset[1][0]
print(img_1.size())
#こっから解像度下げるアルゴリズム…めんどくさい…

def down_resolution(img_tensor,filter_size):
  """
  img_tensor:(1,28,28)の画像テンソル
  filter_size:filter_size×filter_size ピクセルをひとまとまりにする
  """
  img_arr = img_tensor.numpy().transpose((1,2,0)).reshape(28,28)
  img_dash = np.zeros((28,28))
  for i in range(28//filter_size):
    for j in range(28//filter_size):
      filter_total = 0
      for k in range(filter_size):
        for l in range(filter_size):
          filter_total += img_arr[filter_size*i+k][filter_size*j+l]
      filter_average = filter_total/(filter_size*filter_size)
      for k_ in range(filter_size):
        for l_ in range(filter_size):
          img_dash[filter_size*i+k_][filter_size*j+l_] = filter_average
   
  img_dash = torch.from_numpy(img_dash.astype(np.float32)).clone().unsqueeze_(0)

  return img_dash

plt.imshow(down_resolution(img_1,filter_size=2).reshape(28,28))

for i in range(10):
  print("======= question {} =======".format(i+1))
  question = testset[i][0]
  question_ = down_resolution(question,filter_size=7).unsqueeze_(0)
  print("Answer is:",predict(question_,net_mnist))
  print("The right answer is:",testset[i][1])

"""##解像度が低いやつをデータに組み込む"""

#Transformを工夫して、学習データに解像度が低いやつを組み込めないか？
#画像前処理クラスを定義
#解像度ダウンのデータを追加
def down_resolution(img_tensor,filter_size):
  """
  img_tensor:(1,28,28)の画像テンソル
  filter_size:filter_size×filter_size ピクセルをひとまとまりにする
  """
  img_arr = img_tensor.numpy().transpose((1,2,0)).reshape(28,28)
  img_dash = np.zeros((28,28))
  for i in range(28//filter_size):
    for j in range(28//filter_size):
      filter_total = 0
      for k in range(filter_size):
        for l in range(filter_size):
          filter_total += img_arr[filter_size*i+k][filter_size*j+l]
      filter_average = filter_total/(filter_size*filter_size)
      for k_ in range(filter_size):
        for l_ in range(filter_size):
          img_dash[filter_size*i+k_][filter_size*j+l_] = filter_average
   
  img_dash = torch.from_numpy(img_dash.astype(np.float32)).clone().unsqueeze_(0)

  return img_dash

def random_down_resolution(img_tensor):
    filter_size = random.choice([1,2,4,7])
    return down_resolution(img_tensor,filter_size)

class MnistTransform():
    def __init__(self,phase='train'): 
        if phase =='train':
            self.transform = \
                torchvision.transforms.Compose([
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Lambda(random_down_resolution)
                ])
        elif phase == "val":
            self.transform = \
                torchvision.transforms.Compose([
                torchvision.transforms.ToTensor()
            ])
        

    def __call__(self,img):
        return self.transform(img)

#データを取得
dataset1 = torchvision.datasets.MNIST(root='./data',train=True,download=True,transform=MnistTransform("train"))
dataset2 = torchvision.datasets.MNIST(root='./data',train=True,download=True,transform=MnistTransform("val"))
train_dataset = data.Subset(dataset1,list(range(48000)))
val_dataset = data.Subset(dataset2,list(range(48000,60000)))
test_dataset = torchvision.datasets.MNIST(root='./data',train=False,download=True,transform=MnistTransform())

img_tensor = train_dataset[0][0]
img_transformed = img_tensor.numpy().transpose((1,2,0))
plt.imshow(img_transformed.reshape(28,28))

#dataloaderを作ったった
mnist_dataloader_dict = {
    "train":data.DataLoader(dataset=train_dataset,batch_size=32,shuffle=True),
    "val":data.DataLoader(dataset=val_dataset,batch_size=32,shuffle=False)
}

#model作ったった
class MnistNet(nn.Module):
  def __init__(self): #層をインスタンス化
    super().__init__() #継承したnn.Modelの初期化関数を起動
    self.conv1 = nn.Conv2d(1,32,3) #チャネル数in_features=1（白黒なのでそれはそう),out_features=32,フィルター3×3
    self.conv2 = nn.Conv2d(32,64,3) 
    self.pool = nn.MaxPool2d(2,2)
    self.dropout1 = nn.Dropout2d()
    self.fc1 = nn.Linear(in_features=12*12*64,out_features=128)
    self.dropout2 = nn.Dropout2d()
    self.fc2 = nn.Linear(128,10)

  def forward(self,x):
    x = F.relu(self.conv1(x))
    x = self.pool(F.relu(self.conv2(x)))
    x = self.dropout1(x)
    x = x.view(-1,12*12*64)
    x = F.relu(self.fc1(x))
    x = self.dropout2(x)
    x = self.fc2(x)
    return x

net = MnistNet()

#損失関数作ったった
criterion_mnist = nn.CrossEntropyLoss()

#最適化したった
optimizer = optim.SGD(params=net.parameters(),lr=0.0001)

#訓練なう
num_epochs = 40
train_model(net,mnist_dataloader_dict,criterion_mnist,optimizer,num_epochs)

for i in range(10):
  print("======= question {} =======".format(i+1))
  question = test_dataset[i][0]
  question_ = down_resolution(question,filter_size=1).unsqueeze_(0)
  print("Answer is:",predict(question_,net))
  print("The right answer is:",testset[i][1])

"""結果：data augmentation 失敗…泣

#問題・ルールなど

画像早押しクイズ

・データセット：ImageNet・ILSVRC2012
うち、サンプルが多いクラスを100クラス（動物系？）

・ルール

　7×7 -> 14×14 -> 28×28 -> 56×56 -> 112×112 -> 224×224

のように解像度を上げていく

このとき、答えを言うか、あるいは「パス」を選択することができる

各チャレンジごとに10秒のシンキングタイムをとる（つまり、1問あたり1分程度）

*   i回目に正解すると　(7-i)*10 pt 
*   パスと選ぶと 0pt
*   誤答すると -10pt かつ回答権剥奪





20問終了時点で最も得点の高い人（チーム？）が勝利

（関東 vs 関西 にするなら、合計得点を競うのもアリ）

・企画の進め方

予選リーグとしてこれを2試合行い（6-10チーム参加を想定）、それぞれ最も得点が高かった2チームが決勝へ（ここまでで50分想定）

決勝は10問構成で

*   予選と同じことをする
*   違うことをする（例えば、ImageNetにない画像を出題したり）

・時間配分

*   挨拶、ルール説明 5分
*   予選 (20+5)分×2 = 50分
*   決勝 15分
*   プログラム解説会 45分
*   締め、挨拶 5分

・入力

*   出題する問題の画像（1問分5枚、予選2試合・決勝1試合の合計13問分）を一括でフォルダにまとめる
*   画像は全て3×224×224
*   フォルダは形式(いわゆるREADME)のみ公開しておく。サンプルフォルダで事前練習も
*   企画開始10分前にフォルダを公開

・出力
*   シンキングタイムは10秒しかないので、事前10分以内に、予選から決勝までの合計65枚を同時に実行する必要がある
*   出力形式は

　　　1.   csvファイル

　　　2.   各行は、予選1試合目第3問4枚目なら「qualifying1-Q3-N4,"答え"」、決勝第2問3枚目なら「final-Q2-N4,"答え"」などと書く

　　　3. 2列目は"答え"または"パス"のいずれか


* csvファイルに出力された内容を、各問ごとに該当のページに記入することで回答とする
*   事前にサンプルフォルダでテストを行い、そのときに仮答案csvファイルを提出してもらう→提出期限翌日に運営でチェックを行う
*   試合直前に本番のcsvファイルを提出してもらう → ログと照らし合わせて不正がないか確認

・禁止事項


*   指定された出力形式以外の形式をとってはならない。
*   事前にパスワードを開けてはならない。
*   ILSVRC2012のテストデータを用いて学習・検証を行ってはならない。
*   事前に提出したcsvファイルと異なる記入をしてはいけない。
"""