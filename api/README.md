# 蓝奏云网盘API `2.0`
> 基于Python3实现,最强的蓝奏云API~ 

![](https://pc.woozooo.com/img/logo2.gif)  

### [蓝奏云注册](https://pc.woozooo.com/account.php?action=register)

# 更新说明
- 修复了登录时 `formhash` 错误的问题
- 修复了因蓝奏云官网变化导致的功能异常
- 细化 API 接口的功能，某些接口被取消、更名
- 上传文件、创建文件夹时会进行存在性检查
- 不再向上抛异常，而是返回错误码
- 用脚写代码，用心写文档

# 简介

- 本库封装了对蓝奏云的基本操作: 登录、列出文件、下载文件、上传文件、删除文件(夹)、
清空回收站、恢复文件、创建文件夹、设置文件(夹)访问密码
- 此外，通过伪装后缀名，解决了蓝奏云的上传格式限制。
通过分卷上传，解决了单文件最大 100MB 的限制

- 如果有任何问题或建议，欢迎提 issue。最后，求一个 star (≧∇≦)ﾉ

# 安装依赖库
```
pip install requests requests_toolbelt
```

# API 文档

### `.login(username, passwd)`  
> 登录蓝奏云  

|参数|类型|说明|必填|
|:---:|:---:|:---:|:---:|
|username|str|用户名|Y|
|passwd|str|登录密码|Y|

示例 : 
```python
from api.lanzou import LanZouCloud

lzy = LanZouCloud()
status = lzy.login('username', 'passwd')
print(status)
```

返回值 : 登录成功返回 `True`,失败返回 `False`

---

### `.get_dir_list(folder_id)`  
> 获取子文件夹名-id列表

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|folder_id|int|文件夹id|N|默认`-1`(根目录)|

示例 :
```python
# 列出 id 为 1037070 的文件夹的子文件夹
sub_dirs = lzy.get_dir_list(1037070)
print(sub_dirs)
```

返回值：
```python
{
    "娱乐": 1037080,
    "科幻": 1037083,
    "纪录片": 1037084,
    "游戏改": 1037085
}
```

---

### `.get_file_list(folder_id)`  
> 获取文件详细信息列表

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|folder_id|int|文件夹id|N|默认`-1`(根目录)|

示例 :
```python
file_list = lzy.get_file_list(1037070)
print(file_list)
```

返回值 : 
```python
[
    {
        "id": 12741016,     # 文件 id
        "name": "Valentin - A Little Story.mp3",    # 文件名
        "time": "昨天15:27",      # 上传时间
        "size": "8.0 M",    # 文件大小
        "downs": 6,         # 下载次数
        "has_pwd": False, # 是否设置提取码
        "has_des": True   # 是否设置描述
    },
    {
        "id": 12740874,
        "name": "小清水亜美 - 玻璃の空.mp3",
        "time": "昨天15:24",
        "size": "10.7 M",
        "downs": 0,
        "has_pwd": False,
        "has_des": False
    }
]
```

---

### `.get_file_list2(folder_id)`  
> 获取子文件名-id列表

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|folder_id|int|文件夹id|N|默认`-1`(根目录)|

示例 :
```python
file_list = lzy.get_file_list2(1037070)
print(file_list)
```

返回值 : 
```python
{
    "Valentin - A Little Story.mp3": 12741016,
    "小清水亜美 - 玻璃の空.mp3": 12740874
}
```

---

### `.get_full_path(folder_id)`  
> 获取文件夹绝对路径

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|folder_id|int|文件夹id|N|默认`-1`(根目录)|

示例 : 
```python
# 路径: /视频/电影/娱乐     "娱乐"文件夹 id 为 1037080
full_path = lzy.get_full_path(1037080)
print(full_path)
```

返回值 : 
```python
{
    "LanZouCloud": -1,
    "视频": 1033205,
    "电影": 1037070,
    "娱乐": 1037080
}
```

---

### `.delete(fid)`  
> 把网盘的文件(夹)放到回收站

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|fid|int|文件(夹)id|Y|-|

示例 : 
```python
status = lzy.delete(12741016)
print(status)
```
返回值 : 删除成功返回`True`,失败返回`False`  

注 : 

- 无法删除**含有子文件夹的文件夹**,但含有文件的可以删除。
- 重复删除同一个 id 仍返回 `True`
- 删除不存在的 id 也返回 `True`
- 这都是蓝奏云的锅，与我无关 :(

---

### `.move_file(file_id, folder_id)`
> 移动文件到指定文件夹

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|file_id|int|文件id|Y|-|
|folder_id|int|文件夹id|N|默认`-1`(根目录)|

示例 : 
```python
# 把 id=12741016 的文件移动到 id=1037083 的文件夹
status = lzy.move_file(12741016, 1037083)
print(status)
```
返回值 : 移动成功返回 `True`,失败返回 `False`  

---

### `.upload(file_path, folder_id, call_back)`  
> 上传文件到网盘的指定文件夹  

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|file_path|str|本地文件路径|Y|使用绝对路径|
|folder_id|int|网盘文件夹id|N|默认`-1`(根目录)|
|call_back|func|回调函数|N|默认`None`|

返回值 : 上传成功返回 `True`,失败返回 `False`

注意 : 上传一个网盘中已经存在的文件，默认执行覆盖操作

回调函数 : 该函数用于跟踪上传进度  

|参数|类型|说明|
|:---:|:---:|:---:|
|file_name|str|上传文件名|
|total_size|int|文件总字节数|
|now_size|int|已上传字节数|
  

示例:
```python
# 编写显示上传进度条的回调函数
def show_progress(file_name, total_size, now_size):
    percent = now_size / total_size
    bar_len = 40            # 进度条长总度
    now_size /= 1048576     # Bytes to MB
    total_size /= 1048576
    bar_str = '>' * int(bar_len * percent) + '=' * int(bar_len * (1 - percent))
    sys.stdout.write('{} [{}] {:.2f}% ({:.1f}/{:.1f}MB) \r'.format(
        file_name, bar_str, percent * 100, now_size, total_size))

# 上传 D:\test\123.zip 到网盘中 id 为 233333 的文件夹
if lzy.upload(r"D:\test\123.zip", 233333, show_progress):
    print('上传成功')
else:
    print('上传失败')
```

结果 : 
```
123.zip [>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>====] 87.72% (39.9/45.5MB)

```

---

### `.upload2(file_path, folder_id, call_back)`  
> 强化版 upload，解除单文件 100MB 大小限制

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|file_path|str|本地文件路径|Y|使用绝对路径|
|folder_id|int|网盘文件夹id|N|默认`-1`(根目录)|
|call_back|func|回调函数|N|默认`None`|

返回值 : 
- 上传成功返回 `LanZouCloud.SUCCESS` 
- 上传失败返回 `LanZouCloud.FAILED`
- 压缩过程异常返回 `LanZouCloud.ZIP_ERROR`  

注意 : 
- 连续多文件上传的极限是 80 MB/个,所以分卷大小为 80 MB
- 上传大文件会自动在网盘创建文件夹以保存分卷
- 重复上传默认执行覆盖操作

回调函数 : 同 `.upload()`

---

### `.download_file(share_url, pwd, save_path, call_back):`  
> 通过分享链接下载文件
  
|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|share_url|str|文件分享链接|Y|-|
|pwd|str|提取码|N|默认空|
|save_path|str|文件保存路径|N|默认当前路径|
|call_back|func|回调函数|N|默认`None`|

返回值 : 下载成功返回 `True`,下载失败返回 `False`

示例 : 
```python
# 编写显示上传进度条的回调函数
def show_progress(file_name, total_size, now_size):
    percent = now_size / total_size
    bar_len = 40            # 进度条长总度
    now_size /= 1048576     # Bytes to MB
    total_size /= 1048576
    bar_str = '>' * int(bar_len * percent) + '=' * int(bar_len * (1 - percent))
    sys.stdout.write('{} [{}] {:.2f}% ({:.1f}/{:.1f}MB) \r'.format(
        file_name, bar_str, percent * 100, now_size, total_size))

# 下载文件到默认路径
lzy.download_file('https://www.lanzous.com/i6q0fli', '6666', call_back=show_progress)
```

结果 :
```
Git-2.23.0-64-bit.exe [>>>>>>>>>>>>>>>>>>>>>>>>>>>>===========] 71.63% (32.6/45.5MB)
```
---
### `.download_file2(fid, save_path, call_back):`  
> 登录用户通过id下载文件
  
|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|fid|int|文件id|Y|-|
|save_path|str|文件保存路径|N|默认当前路径|
|call_back|func|回调函数|N|默认`None`|

返回值 : 下载成功返回 `True`,下载失败返回 `False`

回调函数 : 同 `.download_file()`

---
### `.mkdir(parent_id, folder_name, description)`  
> 在网盘创建文件夹  

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|parent_id|int|父文件夹id|Y|`-1` 表根目录|
|folder_name|str|文件夹名|Y|自动删除非法字符|
|description|str|文件夹描述|N|默认无|

示例 : 
```python
code = lzy.mkdir(-1, 'my_music', '音乐分享')
if code != LanZouCloud.MKDIR_ERROR:
    print('文件夹id:' + str(code))
```

返回值 : 
- 创建成功返回文件夹 `id`
- 目标已存在返回文件夹 `id`
- 创建失败返回 `LanZouCloud.MKDIR_ERROR`

注意 : 蓝奏云支持创建 **同名文件夹** ，但本方法会阻止这种操作，以防出现混淆

---

### `.rename_dir(folder_id, folder_name, description)`  
> 重命名文件夹(和描述)  

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|folder_id|int|文件夹id|N|默认`-1`(根目录)|
|folder_name|str|文件夹名|Y|非法字符自动删除|
|description|str|文件夹描述|N|默认无|

示例 : 
```python
status = lzy.rename_dir(1037070, 'soft-music', '轻音乐分享')
print(code)
```

返回值 : 重命名成功返回 `True` ,失败或异常返回 `False`

---

### `.list_recovery()`  
> 列出回收站文件(夹)

示例 :
```python
deleted_files = lzy.list_recovery()
print(deleted_files)
```

返回值 :
```python
{
    "folder_list": {
        "杂物": "1037324",
        "相册": "1037324"
    },
    "file_list": {
        "java模拟器.zip": "1037324",
        "Valentin - A Little Story.mp3": "12741016",
        "小清水亜美 - 玻璃の空.mp3": "12740874"
    }
}
```

---

### `.recovery(fid)`  
> 从回收站恢复文件（夹）

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|fid|int|文件(夹)id|Y|-|

示例 : 
```python
status = lzy.recovery(12741016)
print(status)
```

返回值 : 恢复成功返回 `True` ,失败或异常返回 `False`

---

### `.clean_recycle()`  
> 清空回收站

示例 :
```python
status = lzy.clean_recycle()
print(status)
```

返回值 : 清空成功返回 `True` ,失败或异常返回 `False`

---

### `.get_share_info(fid)`  
> 获取文件(夹)分享信息

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|fid|int|文件(夹)id|Y|-|

返回值 : 
```python
{
    "code": 0,      # 状态码
    "share_url": "https://www.lanzous.com/i6q0fli",    # 分享链接
    "passwd": "6666"          # 提取码
}
```

状态码 code:  
- 获取成功 : `LanZouCloud.SUCCESS`
- 获取失败 : `LanZouCloud.FAILED`
- fid参数错误 : `LanZouCloud.ID_ERROR`

示例 :
```python
info = lzy.get_share_info(1033203)

if info['code'] == LanZouCloud.SUCCESS:
    print('分享链接:' + info['share_url'])
```

---

### `.set_share_passwd(fid, passwd)`  
> 设置文件(夹)分享密码

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|fid|int|文件(夹)id|Y|-|
|passwd|str|分享密码|N|2-6个字符,默认空(无密码)|

示例 :
```python
status = lzy.set_share_info(1033203, 'fuck')
print(status)
```

返回值 : 设置成功返回 `True` ,失败返回 `False`  

---

### `.get_direct_url(share_url, pwd)`  
> 获取文件下载直链

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|share_url|str|文件分享链接|Y|-|
|pwd|str|提取码|N|默认空|

返回值 : 
```python
{
    "code": 0,
    "name": "Git-2.23.0-64-bit.exe",
    "direct_url": "https://development5.baidupan.com/100420bb/2019/10/03/41c4117570de8c0ce02d7e7ddc838135.mp3?st=o22S3uwv063cbklsDWh50w&e=1570193627&b=CAwBYFA8UzNXbAclADkAagN2WisNLAVCUSIBQFM9B3FTdQ5iUDVYfVVTVHYEOwF3VXkAcgFtA3VSMg_c_c&fi=12741016&up="
}
```
状态码 code :  
- 获取成功 : `LanZouCloud.SUCCESS`
- 分享链接非法 : `LanZouCloud.URL_INVALID`
- 缺少提取码 : `LanZouCloud.LACK_PASSWORD`
- 提取码错误 : `LanZouCloud.PASSWORD_ERROR`
- 文件已取消 : `LanZouCloud.FILE_CANCELLED`

示例 :
```python
info = lzy.get_direct_url('https://www.lanzous.com/i6k203g', '6666')

if info['code'] == LanZouCloud.SUCCESS:
    print('直链地址:' + info['direct_url'])
elif info['code'] == LanZouCloud.LACK_PASSWD:
    print('缺少提取码')
```

注意 : 
- 本方法会检查分享链接合法性
- 直链有效期约 30 分钟

---
### `.get_direct_url2(fid)`  
> 通过id获取文件下载直链

|参数|类型|说明|必填|备注|  
|:---:|:---:|:---:|:---:|:---:|
|fid|int|文件id|Y|-|

返回值 :  同 `.get_direct_url()`

注意 : 登录后才能通过 id 获取直链，此时无需提取码

