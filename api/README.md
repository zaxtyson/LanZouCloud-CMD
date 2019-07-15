# 蓝奏云网盘API
> 基于Python3实现,目前最强的蓝奏云API 

![](https://pc.woozooo.com/img/logo2.gif)  


### [蓝奏云注册](https://pc.woozooo.com/account.php?action=register)

本API实现的功能:
- [x] 登录蓝奏云
- [x] 提取下载直链
- [x] 上传文件
- [x] 后缀名伪装
- [x] 删除文件(夹)
- [x] 设置分享密码
- [x] 恢复文件(夹)
- [x] 清空回收站
- [x] 大文件上传支持
- [x] 网盘文件浏览

# 说明

百度云账号被限速到20kb/s，pandownload也是勉强支撑着，没钱氪金，相当难受。。。
于是乎，我们的救世主蓝奏云闪亮登场，作为主打小文件储存市场的免费网盘，可以说相当良心，空间不限，最重要的是**不限速**！！
然而，蓝奏云的弱点很明显，单个文件不能超过100MB，对文件格式也有不少限制。而且官方也没有提供
可供调用的api，如何用代码操作蓝奏云也是一个问题。但好运的是，这些狗屁问题我已经解决了。
现在，你可以用几行简单的代码操控蓝奏云，上传、下载、删除、设置分享密码、清理回收站、恢复文件，
此外，我还给你提供了***下载直链提取***和***大文件分段上传***的功能，现在，你可以随意上传大文件，直链下载
不限速，无广告，无限空间！！！文件格式也没有任何限制，后缀自动伪装，下载自动删除。  

一切的细节已经为你封装，你只需要将本api导入你的项目，跟随下面的文档，便能进行二次开发。
打开你的脑洞，好好利用这个无限的空间~

当然，本项目也存在诸多不足，可能还有有些bug，你就当作彩蛋吧(滑稽)，后面会继续维护的，欢迎吐槽和star

# API食用文档

> 安装依赖库
```
pip install requests
```

> 导入本api模块
```
import lanzou.py
```

> 创建一个网盘对象
```
lzy = LanZouCloud()
```


接下来就可以通过一系列方法操作网盘了

### `.login(username, passwd)`  
> 登录到蓝奏云  

**参数说明**:`username`为用户名,`passwd`为登录密码  
**异常处理**:密码错误抛出`PasswdError`
```
import lanzou.py

lzy = LanZouCloud()
lzy.login("12345", "abc")
```


### `.list_dir(folder_id)`  
> 列出某个文件夹下的子文件夹、文件、该文件夹的绝对路径列表 
  
**参数说明**:`folder_id`为文件夹id,id为`-1`表示根目录(可选,默认-1)  
**返回值**:
```
{
    'folder_list': {'子文件夹1': 'id', ...}, 
    'file_list': {'文件1': 'id', ...},
    'path_list': {'根目录': '-1', '父文件夹': 'id', ...}
}
```

`folder_list`中包含了所有子文件夹的name-id键值对  
`file_list`中包含了所有文件的name-id键值对  
`path_list`是该文件夹的上级路径的name-id键值对,一直回溯到根目录  

```
result = lzy.list_dir(797038)
print("打印文件夹下的所有文件及其id")
for k,v in result["file_list"].items():
    print("文件名:{}   ID:{}".format(k,v))
``` 


### `.upload(file_path, folder_id)`  
> 上传文件到网盘的指定文件夹  

**参数说明**:`file_path`为本地文件的***完整路径***,`folder_id`为网盘中目标文件夹的id,
id为`-1`表示上传到网盘根目录(可选,默认-1)  
**返回值**:`{'file_name': 文件名(不含路径) , 'file_id': 该文件在网盘的id, 'share_url': 分享链接}`    
**异常处理**:发生异常时抛出`UploadError` 
```
# 上传D:\test\123.zip到网盘中id为23333的文件夹

result = lzy.upload(r"D:\test\123.zip", 23333)
print("分享链接" + result["share_url"])
```


### `upload2(file_path, folder_id)`  
> 强化版upload,大文件自动拆分上传,生成种子文件

**参数说明**:`file_path`为本地文件完整路径,`folder_id`为蓝奏云目标文件夹的id,id为`-1`表示根目录 (可选,默认-1)  
**返回值**:返回结果格式同upload,小于100MB的文件直接返回文件信息,大文件拆分上传后返回种子文件的信息  
**其它**:上传并没有使用多线程，因为在多次测试中发现多线程上传总有文件会出错，而且上传速度没有明显加快  
种子文件指的是，包含所有分段文件分享链接的txt文本。类似分卷压缩的原理，对于超过100MB的文件，会自动切段，然后
上传，最后把所有分段文件的信息保存到一个txt文本文件，我称之为“种子文件”。download方法拿到这个“种子文件”，会选择所有
分段文件，然后合并，借此解决大文件无法上传的问题。



### `.download(share_url, save_path, pwd):`  
> 下载文件/下载种子文件
  
**参数说明**:`share_url`为蓝奏云分享链接,`save_path`为本地保存路径(不存在自动创建，默认当前路径),
           `pwd`为访问密码(默认为空)  
**异常处理**:出错时抛出`DownloadError`  
**其它**:本方法无需登录即可调用  
  
  
  
### `.mkdir(parent_id, folder_name, folder_description)`  
> 在网盘创建文件夹

**参数说明**:`parent_id`为目标文件夹的父文件夹id,`folder_name`为文件夹名称,
`folder_description`为文件夹描述文本(可选,默认为空)  
**返回值**:创建成功返回文件夹`id`,失败返回`None`  
**其它**:即使蓝奏云支持创建同名文件夹，但是十分不建议你这么做，这会导致mkdir无法正确返回文件夹id

```
# 在id为233333的文件夹下创建名为“music”的文件夹，并设置描述为“音乐分享”

folder_id = lzy.mkdir(233333, "music", "音乐分享")
print("文件夹id为:" + folder_id)
```



### `.delete(id)`  
> 把网盘的文件(夹)放到回收站
1
**参数说明**:`id`为文件或者文件夹的id,目前文件夹id为6位,
文件id为7位,而且它们都快进位了,这个长度以后可能要修改（代码第37行）  
**返回值**:删除成功返回`True`,失败返回`False`  
**其它**:无法删除***含有子文件夹的文件夹***,含有文件也可以删除
```
# 删除id为233333的文件夹(6位数)

lzy.delete(233333)
```


### `.recovery(id):`  
> 从回收站恢复文件（夹）

**参数说明**:`id`为文件或者文件夹的id  
**返回值**:恢复成功返回`True`,失败返回`False`



### `.clean_recycle()`  
> 清空回收站

**返回值**:清空成功返回`True`,失败返回`False`



### `.parse(url, pwd)`  
> 解析蓝奏云分享链接

**参数说明**:`url`为蓝奏云分享链接,`pwd`为文件分享密码(可选,默认为空)  
**返回值**:
```
{
    'file_name': 文件名,
    'file_size': 文件大小,
    'upload_time': 文件上传时间,
    'file_id': 文件id,
    'share_url': 文件分享链接,
    'direct_url': 文件下载直链
}
```  
**异常处理**:解析异常时抛出`ParseError`错误,分享密码错误时抛出`PasswdError`错误,其它情况抛出`LanZouCloudError`,
异常中带有详细的错误信息
```
try:
    result = lzy.parse('https://www.lanzous.com/i4vdvla', '1234')
except (PasswdError,ParseError) as e:
    print(e)

print("直链:" + result["direct_url"])
```


### `.set_passwd(id, passwd)`  
> 设置文件(夹)访问密码
   
**参数说明**:`id`为文件或者文件夹的id,`passwd`表示访问密码,`-1`表示关闭密码(可选,默认关闭)  
**返回值**:设置成功返回`True`,失败返回`False`  

### `.get_share_url(id)`  
> 通过id返回文件(夹)分享链接
   
**参数说明**:`id`为文件的id(目前是8位数字) 或者文件夹的id(目前6位)  
**返回值**:成功返回链接字符串，失败返回空字符串