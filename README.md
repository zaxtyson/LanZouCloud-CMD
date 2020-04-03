<p align="center">
<img src="https://pc.woozooo.com/img/logo2.gif" width="200">
</p>

<h3 align="center">- 蓝奏云CMD -</h3>

<p align="center">
<img src="https://img.shields.io/github/v/release/zaxtyson/LanZouCloud-CMD.svg?logo=iCloud">
<img src="https://img.shields.io/badge/support-Windows-blue?logo=Windows">
<img src="https://img.shields.io/badge/support-Linux-yellow?logo=Linux">
</p>

# 界面

![cmd.png](https://upload.cc/i1/2020/04/03/TGkgNI.png)

# 说明
- 请使用 Python 3.8+ 运行
- 解除官方上传限制，支持批量上传下载
- 为了方便管理，API 独立为一个项目[LanZouCloud-API](https://github.com/zaxtyson/LanZouCloud-API)
- 如果 Windows 平台缺少 `readline`，请执行 `pip install pyreadline`
- 默认下载路径为 `./Download`，请使用 `setpath` 命令修改
- 默认分卷大小为 100 MB, 会员用户请使用 `setsize` 命令修改
- 未登录时可使用 `down URL` 的方式下载文件(夹)~
- 关注本页面以获取更新，如果有问题或者建议，请提 issue
- 如果喜欢本项目，请给一个 star (^▽^)/
- 详细介绍请移步 [Wiki](https://github.com/zaxtyson/LanZouCloud-CMD/wiki) 页面

# 下载
- 感谢 [rachpt](https://github.com/rachpt/lanzou-gui) 开发的 GUI 版本，[点我](https://github.com/rachpt/lanzou-gui/wiki)查看详情

- 在蓝奏云网盘下载 [Windows版](https://www.lanzous.com/b0f14h1od) 

- 或者在本项目的 [`releases`](https://github.com/zaxtyson/LanZouCloud-CMD/releases) 板块下载

# 更新日志

## `v2.4.3`
- 上传/下载支持断点续传，大文件续传使用 `filename.record` 文件保存进度，请不要手动修改和删除
- 新增 `jobs` 命令查看后台任务, 支持提交多个上传/下载任务，使用 `jobs PID` 查看任务详情
- 新增 `xghost` 命令用于清理网盘中的"幽灵文件夹"(不在网盘和回收站显示的文件夹,移动文件时可以看见,文件移进去就丢失)
- 遇到下载验证码时自动打开图片，要求用户输入验证码
- 修复了其它的细节问题

## `2.4.2`
- 紧急修复了蓝奏云网页端变化导致无法显示文件夹的 Bug

## `v2.4.1`
- 修复使用 URL 下载大文件失败的问题
- 修复上传小文件时没有去除非法字符的问题
- 新增 `rmode` 命令，以适宜屏幕阅读器阅读的方式显示

## `v2.4.0`
- 放弃分段压缩，使用更复杂的方式上传大文件。分段数据文件名、文件大小、文件后缀随机，下载时自动处理。
- 放弃使用修改文件名的方式绕过上传格式限制。上传的文件末尾被添加了 512 字节的信息，储存真实文件名，
下载时自动检测并截断，不会影响文件 hash。一般情况下，不截断此信息不影响文件的使用，但纯文本类文件会受影响(比如代码文件)，
建议压缩后上传。
- 现在可以在网盘不同路径下创建同名文件夹，不再添加 `_` 区分，移动文件时支持绝对路径补全。
- 上传/下载失败会立即提醒并显示原因，不需要等待全部任务完成。
- 回收站稍微好看了点~

## `v2.3.5` 更新说明
- 修复回收站文件夹中文件名过长，导致后缀丢失，程序闪退的问题 [#14](https://github.com/zaxtyson/LanZouCloud-CMD/issues/14)
- 修复官方启用滑动验证导致无法登录的问题 [#15](https://github.com/zaxtyson/LanZouCloud-CMD/issues/15)
- 新增 `clogin` 命令支持使用 `cookie` 登录(防止某天 `login` 完全失效)
    - Cookie 内容见浏览器地址栏前的🔒 (Chrome):
    - `woozooo.com -> Cookie -> ylogin`
    - `pc.woozooo.com -> Cookie -> phpdisk_info`
- 因为使用 `Python3.8.1 X64` 打包，导致程序大了一圈😭,您可以使用 `Pyinstaller` 自行打包

## `v2.3.4` 更新说明
- 新增 `update` 命令检查更新(每次启动会检查一次)
- 解除了官方对上传分卷文件的限制 [#11](https://github.com/zaxtyson/LanZouCloud-CMD/issues/11) [#12](https://github.com/zaxtyson/LanZouCloud-CMD/issues/12)
- `rename` 命令支持会员用户修改文件名 [#9](https://github.com/zaxtyson/LanZouCloud-CMD/issues/9)
- 新增 `setsize` 命令支持会员用户修改分卷大小 [#9](https://github.com/zaxtyson/LanZouCloud-CMD/issues/9)
- `mv` 命令支持移动文件夹(不含子文件夹)
- 支持 `cd /` 返回根目录, `cd -` 返回上一次工作目录 [#8](https://github.com/zaxtyson/LanZouCloud-CMD/issues/8)
- 修复了某些特殊情况下回收站崩溃的问题
- `ls` 命令在文件描述为中英文混合时能够正确对齐 [#8](https://github.com/zaxtyson/LanZouCloud-CMD/issues/8)
- 下载时可以使用 `Ctrl + C` 强行中断
- 修复文件上传时间的错误


## `v2.3.3` 更新说明
- 修复上传超过 1GB 的文件时，前 10 个分卷丢失的 Bug [#7](https://github.com/zaxtyson/LanZouCloud-CMD/issues/7)

## `v2.3.2` 更新说明
- 修复了无法上传的 Bug
- 解除了官方对文件名包含多个后缀的限制
- 使用 cookie 登录，配置文件不再保存明文

## `v2.3.1` 更新说明
- 界面焕然一新
- 修复了一堆 BUG
- 新增设置描述信息功能
- 完善了回收站功能
- 完善了移动文件功能

## `v2.2.1` 更新说明
- 修复了文件(夹)无法下载的问题 [#4](https://github.com/zaxtyson/LanZouCloud-CMD/issues/4)
- 修复了上传 rar 分卷文件被 ban 的问题
- 修复了无后缀文件上传出错的问题
- 修复了文件中空白字符导致上传和解压失败的问题

## `v2.1` 更新说明
- 修复了蓝奏云分享链接格式变化导致无法获取直链的问题

## `v2.0`更新说明
- 修复了登录 `formhash` 的错误
- 增加了上传/下载的进度条 [#1](https://github.com/zaxtyson/LanZouCloud-CMD/issues/1)
- 使用 RAR 分卷压缩代替文件分段 [#2](https://github.com/zaxtyson/LanZouCloud-CMD/issues/2)
- 修复了连续上传大文件被ban的问题 [#3](https://github.com/zaxtyson/LanZouCloud-CMD/issues/3)
- 增加了回收站功能
- 取消了`种子文件`下载方式，自动识别分卷数据并解压
- 增加了通过分享链接下载的功能