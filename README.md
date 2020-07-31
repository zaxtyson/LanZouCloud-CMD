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

![cmd.png](https://upload.cc/i1/2020/04/04/W8GKsr.png)

# 说明
- 请使用 Python 3.8+ 运行，否则会报语法错误
- 安装依赖 `pip install requests requests-toolbelt`, Windows 平台还需要 `pyreadline` [#14](https://github.com/zaxtyson/LanZouCloud-CMD/issues/14#issuecomment-590166417)
- 为了方便管理，API 独立为一个项目[LanZouCloud-API](https://github.com/zaxtyson/LanZouCloud-API)
- 由于某些原因不再支持突破官方限制，如果您需要上传大文件，请 fork 本项目并修改部分代码(见API文档)
- 关注本页面以获取更新，如果有问题或者建议，请提 issue
- 如果喜欢本项目，请给一个 star (^▽^)/
- 详细介绍请移步 [Wiki](https://github.com/zaxtyson/LanZouCloud-CMD/wiki) 页面

# 下载
- 感谢 [rachpt](https://github.com/rachpt/lanzou-gui) 开发的 GUI 版本，[点我](https://github.com/rachpt/lanzou-gui/wiki)查看详情

- 在蓝奏云网盘下载 [Windows版](https://www.lanzous.com/b0f14h1od) 

- 或者在本项目的 [`releases`](https://github.com/zaxtyson/LanZouCloud-CMD/releases) 板块下载

# 命令速览
> 路径和文件名支持 TAB 补全

|命令                                 |描述                    |
|-------------------------------------|-----------------------|
|help                                 |查看帮助文档             |
|update                               |检测更新               |
|login                                |使用 Cookie 登录[[1]](https://github.com/zaxtyson/LanZouCloud-API/issues/21#issuecomment-632964409) [[2]](https://github.com/zaxtyson/LanZouCloud-CMD#v235-%E6%9B%B4%E6%96%B0%E8%AF%B4%E6%98%8E)       |
|logout                               |注销当前账号               |
|refresh                              |刷新当前目录            |
|clear                                |清空屏幕                |
|ls                                   |列出文件与目录          |
|mkdir `文件夹`                       |创建文件夹(路径最大深度 4 级)               |
|rm `文件(夹)名`                      |将文件(夹)放入回收站            |
|cd `路径`                           |切换工作目录(..表示上级路径, -表示上一次路径)
|mv `文件(夹)名`                       |移动文件(夹)                |
|rename `文件(夹)名`                   |重命名(普通用户无法修改文件名)    |
|desc `文件(夹)名`                     |设置文件(夹)描述信息       |
|passwd `文件(夹)名`                    |设置文件(夹)提取码       |
|setpath                              |修改下载路径(默认 ./Download) |
|setsize                              |修改单文件大小限制        |
|setpasswd                              |设置文件(夹)默认提取码|
|setdelay                              |设置数据块上传延时，防止被封号(突破官方限制时使用)|
|upload `文件(夹)路径`                |上传文件(夹)            |
|down `文件(夹)名/分享链接`              |下载文件(夹)  |
|share `文件/文件夹`                    |查看文件(夹)分享信息    |
|export `文件夹名`                      |导出文件夹下的文件信息到CSV文件|
|xghost                                |清理"幽灵"文件夹(网盘中看不见,移动时会显示)|
|rmode                                 |方便视障用户使用屏幕阅读器阅读|
|jobs                                  |查看后台上传/下载任务      |
|jobs `任务ID`                          |查看任务详细信息(错误原因)      |
|cdrec                                |进入回收站              |
|[cdrec]  ls                          |显示回收站文件           |
|[cdrec]  rec `文件(夹)名`             |恢复文件(夹)           |
|[cdrec]  clean                       |清空回收站              |
|[cdrec]  cd ..                       |退出回收站              |
|bye                                  |退出程序                    |

# 更新日志
## `v2.5.5`
- 修复下载两个同名文件时断点续传功能异常的问题[#35](https://github.com/zaxtyson/LanZouCloud-API/issues/35#issue-668534695)
- 下载同名文件时自动添加序号以便区分
- 修复蓝奏云将文件名敏感词(如[小姐](https://zaxtyson.lanzous.com/ic59zpg))替换为`*`导致下载文件崩溃的问题
- 修复文件大小中出现 `,` 导致无法完整匹配文件大小的问题

## `v2.5.4`
- 修复下载某些文件时验证方式变化的问题
- 修复 export 导出时的编码问题(Excel乱码: 数据->从文本/CSV导入->UTF-8编码)

## `v2.5.3`
- 修复新出现的 URL 包含大写字符无法匹配的问题

## `v2.5.2`
- 修复子域名变化导致的异常
- `share` 命令不再显示文件夹下的文件信息
- 新增 `export` 命令, 支持批量导出文件夹内的文件信息(csv文件)

## `v2.5.0`
- 遵守官方限制, 不再支持大文件上传和文件名伪装功能(之前上传的文件仍可以正常下载)
- 登录接口被限制, 使用 Cookie 登录, 参见 `v2.3.5` 更新日志

## `v2.4.5`
- 修复无法处理蓝奏云自定义域名的问题
- 修复新用户执行与创建文件夹相关命令时崩溃的问题
- 新增 `setpasswd` 命令设置文件(夹)默认提取码
- 新增 `setdelay` 命令设置大文件数据块上传延时，减小被封的可能性
- 出于 PD 事件的影响，这将是本项目最后一次更新
- CMD 版本将去除大文件上传功能，仅保留蓝奏云的基本功能
- API 保留了相关功能，有能力者请自行开发，但是您需要承担由此带来的风险
- **本项目的代码会在一段时间后删除**，在此之前，请保存好您的网盘的大文件

## `v2.4.4`
- `ls` 命令显示文件下载次数
- 修复 VIP 用户分享链接无法处理的问题
- 修复下载时可能出现的 Read time out 异常
- 修复上传大文件自动创建文件夹名包含 `mkdir` 字符串后缀的问题(这不是feature，只是测试时无意中写到代码里了－_－)
- Windows 发行版使用 Inno Setup 封装，直接安装，方便更新

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
