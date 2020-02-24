# coding=utf-8
import os
from getpass import getpass
from time import sleep
import readline
from lanzou.api import LanZouCloud  # pip install lanzou-api
from pickle import load, dump
import requests


def check_rec_mode(func):
    """装饰不能在回收站下运行的函数"""

    def wrapper(self, *args, **kw):
        if self._mode == Commander.REC_MODE:
            print('ERROR : 回收站模式下无法使用此命令哦')
            return None
        func(self, *args, **kw)

    return wrapper


class Commander(object):
    REC_MODE = 0  # 回收站模式
    NORMAL_MODE = 1  # 正常模式

    def __init__(self):
        self._version = '2.3.5'
        self._prompt = '> '
        self._mode = Commander.NORMAL_MODE
        self._disk = LanZouCloud()
        self._dir_list = []
        self._file_list = []
        self._dir_id_list = {}
        self._file_id_list = {}
        self._path_list = {}
        self._rec_root_file = {}
        self._parent_id = -1
        self._parent_name = ''
        self._work_name = ''
        self._work_id = -1
        self._last_work_id = -1
        self._config_file = 'config.dat'
        self._config = None
        self._default_down_path = './Download'

        with open(self._config_file, 'rb') as config:
            self._config = load(config)

    @staticmethod
    def _show_progress(file_name, total_size, now_size):
        """显示进度条的回调函数"""
        percent = now_size / total_size
        bar_len = 40  # 进度条长总度
        bar_str = '>' * round(bar_len * percent) + '=' * round(bar_len * (1 - percent))
        print('\r{:.2f}%\t[{}] {:.1f}/{:.1f}MB\t| {} '.format(
            percent * 100, bar_str, now_size / 1048576, total_size / 1048576, file_name), end='')
        if total_size == now_size:
            print('')  # 下载完成换行

    @staticmethod
    def set_console_style():
        """设置命令行窗口样式"""
        if os.name != 'nt':
            return None
        os.system('mode con cols=125 lines=40')
        os.system('title 蓝奏云CMD控制台')

    def _print_logo(self):
        """输出logo"""
        logo_str = f"""
        _                  ______            _____ _                 _ 
       | |                |___  /           /  __ \ |               | |
       | |     __ _ _ __     / /  ___  _   _| /  \/ | ___  _   _  __| |
       | |    / _  |  _ \   / /  / _ \| | | | |   | |/ _ \| | | |/ _  |
       | |___| (_| | | | | / /__| (_) | |_| | \__/\ | (_) | |_| | (_| |
       \_____/\____|_| |_|\_____/\___/ \____|\____/_|\___/ \____|\____|
      --------------------------------------------------------------------
      Github: https://github.com/zaxtyson/LanZouCloud-CMD (Version: {self._version})
      --------------------------------------------------------------------
            """
        print(logo_str)

    def update_config(self):
        """更新配置文件"""
        with open(self._config_file, 'wb') as f:
            dump(self._config, f)

    def refresh(self, dir_id=-1):
        """刷新当前文件夹和路径信息"""
        self._file_list = self._disk.get_file_list(dir_id)
        self._file_id_list = self._disk.get_file_id_list(dir_id)
        self._dir_list = self._disk.get_dir_list(dir_id)
        self._dir_id_list = self._disk.get_dir_id_list(dir_id)
        self._path_list = self._disk.get_full_path(dir_id)
        self._prompt = '/'.join(list(self._path_list.keys())) + ' > '
        self._work_name = list(self._path_list.keys())[-1]
        self._last_work_id = self._work_id
        self._work_id = self._path_list.get(self._work_name, -1)
        if dir_id != -1:
            self._parent_name = list(self._path_list.keys())[-2]
            self._parent_id = self._path_list.get(self._parent_name, -1)

    def _local_delete(self, name, is_file=True):
        """本地删除文件(夹)信息，减少向服务器的请求"""
        if is_file:
            pop_id = self._file_id_list.pop(name)  # 删除本地文件 name-id 索引
            for f in self._file_list:  # 删除本地文件信息
                if f['name'] == name:
                    self._file_list.remove(f)
            if self._mode == Commander.REC_MODE:  # 回收站模式需要删除更多信息
                if f in self._rec_root_file.items():
                    if f['name'] == name:
                        self._rec_root_file.pop(name)
                for folder in self._dir_list:
                    for file in folder['files']:
                        if file['id'] == pop_id:  # 防止不同文件夹文件重名
                            folder['files'].remove(file)

        else:
            self._dir_id_list.pop(name)
            for d in self._dir_list:
                if d['name'] == name:
                    self._dir_list.remove(d)

    def check_rar_tool(self):
        """设置RAR解压工具"""
        if os.name == 'nt':
            rar_bin = './rar.exe'
        else:
            rar_bin = '/usr/bin/rar'
        if self._disk.set_rar_tool(rar_bin) == LanZouCloud.ZIP_ERROR:
            print('ERROR : 缺少解压工具! \n'
                  'Windows 用户请检查 rar.exe 文件是否存在\n'
                  'Linux 用户请执行: sudo apt install rar')
            sleep(3)
            exit(-1)

    def init_max_size(self):
        """初始化文件分卷大小"""
        max_size = self._config.get('max_size')
        self._disk.set_max_size(max_size)

    def update(self):
        """检查更新"""
        print("正在检测更新...")
        api = "https://api.github.com/repos/zaxtyson/LanZouCloud-CMD/releases/latest"
        try:
            info = requests.get(api).json()
        except (requests.RequestException, AttributeError):
            input("ERROR: 检查更新时发生异常")
            return None
        tag_name, msg = info['tag_name'], info['body']
        update_url = info['assets'][0]['browser_download_url']
        version = tag_name.replace('v', '').split('.')     # x.x.x
        version2 = self._version.split('.')
        remote_version = int(version[0]) * 100 + int(version[1]) * 10 + int(version[2])
        local_version = int(version2[0]) * 100 + int(version2[1]) * 10 + int(version2[2])
        if remote_version > local_version:
            print(f"程序可以更新 v{self._version} -> {tag_name}")
            print(f"\n@更新说明:\n{msg}")
            print(f"\n@Windows 更新:")
            print(f"蓝奏云: https://www.lanzous.com/b0f14h1od")
            print(f"Github: {update_url}")
            print("\n@Linux 更新:")
            print("pip install -U lanzou-api")
            print("git clone https://github.com/zaxtyson/LanZouCloud-CMD.git")
            input()
        else:
            print("(*/ω＼*)暂无更新~ 如有 Bug 或建议,请提 Issue 或发邮件反馈")
            print("Email: zaxtyson@foxmail.com")
            print("Github: https://github.com/zaxtyson/LanZouCloud-CMD")

    def _check_down_path(self):
        """检查下载路径"""
        if not self._config.get('path'):
            print('请设置文件下载路径')
            self.setpath()

    def clogin(self):
        """使用 cookie 登录"""
        print("请在浏览器端登录: https://pc.woozooo.com/")
        print("设置 Cookie 内容:")
        ylogin = input("ylogin=")
        disk_info = input("phpdisk_info=")
        if not ylogin or not disk_info:
            print("ERROR: 请输入正确的 Cookie 信息")
            return None
        cookie = {"ylogin": str(ylogin), "phpdisk_info": disk_info}
        if self._disk.login_by_cookie(cookie) == LanZouCloud.SUCCESS:
            self._config['cookie'] = cookie
            self.update_config()
            self.refresh(self._work_id)
        else:
            print("ERROR : 登录失败,请检查 Cookie 是否正确")

    def login(self):
        """登录网盘"""
        self.clear()
        self._print_logo()
        cookie = self._config.get('cookie')
        if not cookie or self._disk.login_by_cookie(cookie) != LanZouCloud.SUCCESS:
            username = input('输入用户名:')
            password = getpass('输入密码:')
            code = self._disk.login(username, password)
            if code == LanZouCloud.NETWORK_ERROR:
                print("登录失败 : 网络连接异常")
                return None
            elif code == LanZouCloud.FAILED:
                print('登录失败 : 用户名或密码错误 :(')
                return None
            # 登录成功保存用户 cookie
            self._config['cookie'] = self._disk.get_cookie()
            self.update_config()
        # 刷新文件列表
        self.refresh(self._work_id)

    def ls(self):
        """列出文件(夹)"""

        def _text_align(text, length) -> str:
            """中英混合字符串对齐"""
            text_len = len(text)
            for char in text:
                if u'\u4e00' <= char <= u'\u9fff':
                    text_len += 1
            space = length - text_len
            return text + ' ' * space

        if self._mode == Commander.REC_MODE:  # 回收站模式
            for file in self._file_list:
                print("#{0:<12}{1:<14}{2}".format(file['id'], file['time'], file['name']))
            for folder in self._dir_list:
                print("#{0:<12}{1:<14}{2}/".format(folder['id'], folder['time'], folder['name']))
                files = folder['files']
                for file in files:
                    print("{0:<27} - [{1}] {2}".format('', file['size'], file['name']))
        else:  # 正常模式
            for folder in self._dir_list:
                pwd_str = '✦' if folder['has_pwd'] else '✧'
                print("#{0:<12}{1:<4}{2}{3}/".format(
                    folder['id'], pwd_str, _text_align(folder['desc'], 24), folder['name']
                ))
            for file in self._file_list:
                pwd_str = '✦' if file['has_pwd'] else '✧'
                print("#{0:<12}{1:<4}{2:<14}{3:<10}{4}".format(
                    file['id'], pwd_str, file['time'], file['size'], file['name']
                ))

    @staticmethod
    def clear():
        """清空屏幕"""
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def cd(self, dir_name):
        """切换工作目录"""
        if self._mode == Commander.REC_MODE:
            if dir_name == '..':
                self._mode = Commander.NORMAL_MODE
                self.refresh(self._parent_id)
                return None
            print('INFO : 退出回收站请输入 "cd .."')
            return None
        # 正常工作模式
        if dir_name == '..':  # 返回上级路径
            self.refresh(self._parent_id)
        elif dir_name == '/':
            self.refresh()
        elif dir_name == '-':
            self.refresh(self._last_work_id)
        elif dir_name == '.':
            pass
        elif dir_name in self._dir_id_list.keys():
            folder_id = self._dir_id_list.get(dir_name)
            self.refresh(folder_id)
        else:
            print(f'ERROR : 该文件夹不存在: {dir_name}')

    @check_rec_mode
    def mkdir(self, name, desc=''):
        """创建文件夹"""
        if name in self._dir_id_list.values():
            print(f'ERROR : 文件夹已存在:{name}')
            return None
        dir_id = self._disk.mkdir(self._work_id, name, desc)
        if dir_id == LanZouCloud.MKDIR_ERROR:
            print(f'ERROR : 创建文件夹失败:{name}')
        else:  # 创建成功，添加到文件夹列表，减少向服务器请求次数
            self._dir_list.append({'name': name, 'id': dir_id, 'has_pwd': False, 'desc': desc})
            self._dir_id_list.setdefault(name, dir_id)

    def rm(self, name):
        """删除文件"""
        if self._file_id_list.get(name, None):  # 文件
            fid = self._file_id_list.get(name)
            if self._mode == Commander.REC_MODE:  # 回收站模式,彻底删除文件
                if name not in self._rec_root_file.keys():
                    print('ERROR : 无法直接删除回收站文件夹中的文件')
                    return None
                if self._disk.delete_rec(fid, True) == LanZouCloud.SUCCESS:
                    self._local_delete(name, True)
                else:
                    print(f'ERROR : 彻底删除文件失败: {name}')
            else:  # 正常模式，移动文件至回收站
                if self._disk.delete(fid, True) == LanZouCloud.SUCCESS:
                    self._local_delete(name, True)
                else:
                    print(f'ERROR : 删除文件失败: {name}')
        elif self._dir_id_list.get(name, None):  # 文件夹
            fid = self._dir_id_list.get(name)
            if self._mode == Commander.REC_MODE:
                if self._disk.delete_rec(fid, False) == LanZouCloud.SUCCESS:
                    self._local_delete(name, False)
                else:
                    print(f'ERROR : 彻底删除文件夹失败: {name}')
            else:
                if self._disk.delete(fid, False) == LanZouCloud.SUCCESS:
                    self._local_delete(name, False)
                else:
                    print(f'ERROR : 删除文件夹失败(存在子文件夹?): {name}')
        else:  # 不存在
            print(f'ERROR : 文件(夹)不存在: {name}')

    def cdrec(self):
        """查看回收站"""
        self._mode = Commander.REC_MODE
        files, folders = self._disk.get_rec_all()
        self._dir_list = folders
        self._dir_id_list = {f['name']: f['id'] for f in folders}
        self._file_list = files
        self._rec_root_file = {f['name']: f['id'] for f in files}  # 真根目录下的文件
        self._file_id_list = {f['name']: f['id'] for f in self._disk.get_rec_file_list()}  # 全部文件
        self._parent_name = list(self._path_list.keys())[-1]
        self._parent_id = self._path_list.get(self._parent_name)
        self._prompt = 'LanZouCloud/Recovery > '

    def clean(self):
        """清空回收站"""
        if self._mode != Commander.REC_MODE:
            print(f'INFO : 该命令仅在回收站模式下使用哦')
            return None
        if input('INFO : 确认清空回收站?(y) ') == 'y':
            if self._disk.clean_rec() == LanZouCloud.SUCCESS:
                self._rec_root_file = {}
                self._file_list = []
                self._file_id_list = {}
                self._dir_list = []
                self._dir_id_list = {}
                print('INFO : 回收站清空成功!')
            else:
                print('ERROR : 回收站清空失败!')

    def rec(self, name):
        """恢复文件"""
        if self._mode != Commander.REC_MODE:
            print('ERROR : 该命令仅在回收站模式下可用 :)')
            return None
        if self._file_id_list.get(name, None):
            fid = self._file_id_list.get(name)
            if self._disk.recovery(fid, True) == LanZouCloud.SUCCESS:
                self._local_delete(name, True)
            else:
                print(f'ERROR : 彻底删除文件失败: {name}')
        elif self._dir_id_list.get(name, None):
            fid = self._dir_id_list.get(name)
            if self._disk.recovery(fid, False) == LanZouCloud.SUCCESS:
                self._local_delete(name, False)
            else:
                print(f'ERROR : 彻底删除文件夹失败: {name}')
        else:
            print('ERROR : (#`O′) 没有这个文件啊喂')

    @check_rec_mode
    def rename(self, name):
        """重命名文件或文件夹(需要会员)"""
        is_file = True
        if self._dir_id_list.get(name, None):
            fid = self._dir_id_list.get(name)
            is_file = False
        elif self._file_id_list.get(name, None):
            fid = self._file_id_list.get(name)
        else:
            print(f'ERROR : 没有这个文件(夹)的啦: {name}')
            return None

        new_name = input(f'重命名 "{name}" 为 ') or None
        if not new_name:
            print(f'INFO : 重命名操作取消')
            return None

        if is_file:
            if self._disk.rename_file(fid, new_name) != LanZouCloud.SUCCESS:
                print('ERROR : (＃°Д°) 文件重命名失败, 请开通会员，文件名不要带后缀')
                return None
            # 只更新本地索引的文件夹名(调用refresh()要等 1.5s 才能刷新信息)
            self._file_id_list[new_name] = self._file_id_list.pop(name)
            for file in self._file_list:
                if file['name'] == name:
                    file['name'] = new_name
        else:
            if self._disk.rename_dir(fid, new_name) != LanZouCloud.SUCCESS:
                print('ERROR : 文件夹重命名失败')
                return None
            self._dir_id_list[new_name] = self._dir_id_list.pop(name)
            for folder in self._dir_list:
                if folder['name'] == name:
                    folder['name'] = new_name

    def mv(self, name):
        """移动文件或文件夹"""
        is_file = True
        if self._file_id_list.get(name, None):
            fid = self._file_id_list.get(name)
        elif self._dir_id_list.get(name, None):
            fid = self._dir_id_list.get(name)
            is_file = False
        else:
            print(f"ERROR : 文件(夹)不存在: {name}")
            return None

        # 备份当前目录下文件(夹) name-id 列表,TAB 只补全目标文件夹名
        backup_dir = self._dir_id_list
        backup_file = self._file_id_list
        self._file_id_list = {}
        self._dir_id_list = self._disk.get_folders_name_id()
        self._dir_id_list.pop(self._work_name)  # 不能移动到当前文件夹
        if not is_file:
            self._dir_id_list.pop(name)     # 文件夹不能移动到自身

        print('# 请选择目标文件夹(TAB键补全)')
        for n, folder in enumerate(self._dir_id_list.keys()):
            if n != 0 and n % 2 == 0:
                print('')   # 换行
            print(' -> {:<32}'.format(folder), end='\t')

        folder_name = input(f'\n移动 "{name}" 到 ') or ' '
        folder_id = self._dir_id_list.get(folder_name, None)
        if not folder_id:
            print(f'ERROR : 目标文件夹不存在的啦: {folder_name}')
            self._file_id_list = backup_file    # 还原当前目录的文件(夹) name-id 索引
            self._dir_id_list = backup_dir
            return None
        if is_file:
            code = self._disk.move_file(fid, folder_id)
        else:
            code = self._disk.move_folder(fid, folder_id)

        if code == LanZouCloud.SUCCESS:
            self.refresh(self._work_id)     # 移动成功，刷新当前目录信息
        else:
            print(f"ERROR : 移动 {name} 到 {folder_name} 失败")
            self._dir_id_list = backup_dir
            self._file_id_list = backup_file

    @check_rec_mode
    def _down_by_id(self, name):
        """通过 id 下载文件(夹)"""
        save_path = self._config.get('path') or self._default_down_path
        if self._file_id_list.get(name, None):  # 如果是文件
            code = self._disk.down_file_by_id(self._file_id_list.get(name), save_path, self._show_progress)
            if code != LanZouCloud.SUCCESS:
                print(f"ERROR : 文件下载失败: {name}")
        elif self._dir_id_list.get(name, None):  # 如果是文件夹
            info = self._disk.down_dir_by_id(self._dir_id_list.get(name), save_path, self._show_progress, mkdir=True)
            if info['code'] != LanZouCloud.SUCCESS:  # 有文件下载失败
                if not info['failed']:
                    print('INFO : 该文件夹下没有文件的啦')
                else:
                    print('ERROR : 以下文件下载失败: ')
                    for f in info['failed']:
                        print(f"    -> #{f['id']}  错误码:{f['code']}  文件名:{f['name']}")
        else:
            print(f'ERROR : 文件(夹)不存在: {name}')

    @staticmethod
    def _print_error(code):
        if code == LanZouCloud.SUCCESS:
            return None
        elif code == LanZouCloud.URL_INVALID:
            print('ERROR : 分享链接无效')
        elif code == LanZouCloud.LACK_PASSWORD:
            print('ERROR : 缺少提取码')
        elif code == LanZouCloud.PASSWORD_ERROR:
            print('ERROR : 提取码错误')
        elif code == LanZouCloud.FILE_CANCELLED:
            print('ERROR : 该链接已失效')
        elif code == LanZouCloud.ZIP_ERROR:
            print('ERROR : 解压过程异常')
        elif code == LanZouCloud.NETWORK_ERROR:
            print('ERROR : 网络连接异常')
        else:
            print('ERROR : 下载失败，请重试')

    @check_rec_mode
    def _down_by_url(self, url):
        """通过 url 下载"""
        save_path = self._config.get('path') or self._default_down_path
        if self._disk.is_file_url(url):  # 如果是文件
            code = self._disk.down_file_by_url(url, '', save_path, self._show_progress)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件的提取码 : ') or ''
                code2 = self._disk.down_file_by_url(url, str(pwd), save_path, self._show_progress)
                self._print_error(code2)
            else:
                self._print_error(code)
        elif self._disk.is_folder_url(url):  # 如果是文件夹
            info = self._disk.down_dir_by_url(url, '', save_path, self._show_progress, mkdir=True)
            if info['code'] == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件夹的提取码 : ') or ''
                info2 = self._disk.down_dir_by_url(url, str(pwd), save_path, self._show_progress, mkdir=True)
                if info2['code'] == LanZouCloud.FAILED:  # 部分文件下载失败
                    print(f'ERROR : 以下文件下载失败:')
                    for file in info2['failed']:
                        print(f"    -> 错误码: {file['code']}  {file['name']}  ({file['url']})")
                    return None
                self._print_error(info2['code'])  # 其它错误
            else:
                self._print_error(info['code'])
        else:  # 链接无效
            print('ERROR : (。>︿<) 该分享链接无效哦')

    def down(self, arg):
        """自动选择下载方式"""
        try:
            if arg.startswith('http'):
                self._down_by_url(arg)
            else:
                self._down_by_id(arg)
        except KeyboardInterrupt:
            print('\nINFO : 当前下载任务已取消')

    @check_rec_mode
    def upload(self, path):
        """上传文件(夹)"""
        path = path.strip('\"\' ')  # 去除直接拖文件到窗口产生的引号
        if not os.path.exists(path):
            print(f'ERROR : 该路径不存在哦: {path}')
            return None

        try:
            if os.path.isdir(path):
                print(f'INFO : 批量上传文件夹: {path}')
                info = self._disk.upload_dir(path, self._work_id, self._show_progress)
                if info['code'] != LanZouCloud.SUCCESS:
                    print(f"ERROR : 以下文件上传失败: {' '.join(info['failed'])}")
                self.refresh(self._work_id)
            else:
                info = self._disk.upload_file(path, self._work_id, self._show_progress)
                if info['code'] != LanZouCloud.SUCCESS:
                    print(f"ERROR : 文件上传失败: {' '.join(info['failed'])}")
                self.refresh(self._work_id)
        except KeyboardInterrupt:
            print("\nINFO : 上传已终止")

    @check_rec_mode
    def share(self, name):
        """显示分享信息"""
        if self._file_id_list.get(name, None):  # 文件
            info = self._disk.get_file_info_by_id(self._file_id_list.get(name))
            if info['code'] != LanZouCloud.SUCCESS:
                print('ERROR : 获取文件信息出错')
            print("-" * 50)
            print(f"文件名   : {name}")
            print(f"提取码   : {info['pwd'] or '无'}")
            print(f"文件大小 : {info['size']}")
            print(f"上传时间 : {info['time']}")
            print(f"分享链接 : {info['url']}")
            print(f"描述信息 : {info['desc'] or '无'}")
            print(f"下载直链 : {info['durl'] or '无'}")
            print("-" * 50)
        elif self._dir_id_list.get(name, None):  # 文件夹
            info = self._disk.get_folder_info_by_id(self._dir_id_list.get(name))
            if info['code'] != LanZouCloud.SUCCESS:
                print('ERROR : 获取文件夹信息出错')
            print("-" * 80)
            print(f"文件夹名 : {name}")
            print(f"提取码   : {info['folder']['pwd'] or '无'}")
            print(f"分享链接 : {info['folder']['url']}")
            print(f"描述信息 : {info['folder']['desc'] or '无'}")
            print("-" * 80)
            for file in info['files']:
                print("+ {0:<12}{1:<9}{2}\t{3}".format(file['time'], file['size'], file['url'], file['name']))
            if len(info['files']) != 0:
                print("-" * 80)
        else:
            print(f"ERROR : 文件(夹)不存在: {name}")

    @check_rec_mode
    def passwd(self, name):
        """设置文件(夹)提取码"""
        if self._file_id_list.get(name, None):  # 文件
            fid = self._file_id_list.get(name)
            info = self._disk.get_share_info(fid, True)
            new_pass = input(f'修改提取码 "{info["pwd"] or "无"}" -> ')
            if 2 <= len(new_pass) <= 6:
                if new_pass == 'off': new_pass = ''
                if self._disk.set_passwd(fid, str(new_pass), True) != LanZouCloud.SUCCESS:
                    print('ERROR : 设置文件提取码失败')
                self.refresh(self._work_id)
            else:
                print('ERROR : 提取码为2-6位字符,关闭请输入off')
        elif self._dir_id_list.get(name, None):  # 文件夹
            fid = self._dir_id_list.get(name)
            info = self._disk.get_share_info(fid, False)
            new_pass = input(f'修改提取码 "{info["pwd"] or "无"}" -> ')
            if 2 <= len(new_pass) <= 12:
                if new_pass == 'off': new_pass = ''
                if self._disk.set_passwd(fid, str(new_pass), False) != LanZouCloud.SUCCESS:
                    print('ERROR : 设置文件夹提取码失败')
                self.refresh(self._work_id)
            else:
                print('ERROR : 提取码为2-12位字符,关闭请输入off')
        else:
            print(f'ERROR : 文件(夹)不存在: {name}')

    @check_rec_mode
    def desc(self, name):
        """设置文件描述"""
        if self._file_id_list.get(name, None):  # 文件
            fid = self._file_id_list.get(name)
            info = self._disk.get_share_info(fid, True)
            print(f"当前描述: {info['desc'] or '无'}")
            desc = input(f'修改为 -> ')
            if not desc:
                print(f'ERROR : 文件描述不允许为空')
                return None
            if self._disk.set_desc(fid, str(desc), True) != LanZouCloud.SUCCESS:
                print(f'ERROR : 文件描述修改失败')
            self.refresh(self._work_id)
        elif self._dir_id_list.get(name, None):  # 文件夹
            fid = self._dir_id_list.get(name)
            info = self._disk.get_share_info(fid, False)
            print(f"当前描述: {info['desc']}")
            desc = input(f'修改为 -> ') or ''
            if self._disk.set_desc(fid, str(desc), False) == LanZouCloud.SUCCESS:
                if len(desc) == 0:
                    print('INFO : 文件夹描述已关闭')
            else:
                print(f'ERROR : 文件夹描述修改失败')
            self.refresh(self._work_id)
        else:
            print(f'ERROR : 文件(夹)不存在: {name}')

    def setpath(self):
        """设置下载路径"""
        print(f"当前下载路径 : {self._config.get('path')}")
        path = input('修改为 -> ').strip("\"\' ")
        if os.path.isdir(path):
            self._config['path'] = path
            self.update_config()
        else:
            print('ERROR : 路径非法,取消修改')

    def setsize(self):
        """设置分卷大小"""
        print(f"当前分卷大小(MB): {self._config.get('max_size')}")
        max_size = input('修改为 -> ')
        if not max_size.isnumeric():
            print("ERROR: 请输入大于 100 的数字")
            return None
        if self._disk.set_max_size(int(max_size)) != LanZouCloud.SUCCESS:
            print("ERROR: 自定义分卷大小应该大于 100 MB")
            return None

        self._config['max_size'] = int(max_size)
        self.update_config()

    def logout(self):
        """注销"""
        self.clear()
        self._disk.logout()
        self._file_list = []
        self._dir_list = []
        self._path_list = {'LanZouCloud': -1}
        self._parent_id = -1
        self._parent_name = ''
        self._work_id = -1
        self._last_work_id = -1
        self._work_name = ''
        self._config['cookie'] = None
        self.update_config()

    @staticmethod
    def help():
        help_text = """
    • CMD版蓝奏云控制台，按 TAB 自动补全路径
    • 支持大文件上传，解除文件格式限制
    • 支持提取直链，批量下载上传
    
    命令帮助 :
    help        显示本信息
    update      检查更新
    refresh     强制刷新文件列表信息
    login       使用账号密码登录网盘
    clogin      使用 Cookie 登录网盘
    logout      注销当前账号
    ls          列出文件(夹)
    cd          切换工作目录
    cdrec       进入回收站
    rm          删除网盘文件(夹)
    mkdir       创建新文件夹
    share       显示分享信息
    clear       清空屏幕
    clean       清空回收站
    upload      上传文件(夹)
    down        下载文件(夹)
    passwd      设置文件(夹)提取码
    setpath     设置默认下载路径
    setsize     设置文件分卷大小
    rename      重命名文件(夹)
    desc        修改文件(夹)描述
    mv          移动文件(夹)
    bye         退出本程序
    
    更详细的介绍请参考本项目的 Github 主页:
    https://github.com/zaxtyson/LanZouCloud-CMD   
    如有 Bug 反馈或建议请在 GitHub 提 Issue 或者
    发送邮件至 : zaxtyson@foxmail.com
    感谢您的使用 (●'◡'●)
        """
        print(help_text)

    def process_a_cmd(self):
        """处理一条用户命令"""

        def completer(text, rank):
            """自动补全"""
            tab_list = []
            all_list = list(self._dir_id_list.keys()) + list(self._file_id_list.keys())
            for folder_name in all_list:
                if folder_name.startswith(text):
                    tab_list.append(folder_name)
            return tab_list[rank]

        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer)

        # 处理用户命令
        try:
            args = input(self._prompt).split()
        except KeyboardInterrupt:
            print('INFO : 退出本程序请输入 bye')
            return -1
        if len(args) == 0: return None
        cmd = args[0]   # 命令
        arg = ' '.join(args[1:])    # 参数(可带有空格)

        no_arg_cmd = ['ls', 'login', 'clogin', 'clean', 'cdrec', 'clear', 'setpath', 'setsize', 'help', 'update']
        cmd_with_arg = ['rm', 'cd', 'mkdir', 'rec', 'upload', 'down', 'share', 'passwd', 'rename', 'mv', 'desc']

        if cmd in no_arg_cmd:
            exec(f"self.{cmd}()")
        elif cmd in cmd_with_arg:
            exec(f"self.{cmd}(r'{arg}')")
        elif cmd == 'refresh':
            self.refresh(self._work_id)
        elif cmd == 'logout':
            self.logout()
            self.login()
        elif cmd == 'bye':
            exit(0)
        else:
            print('ERROR : 命令不存在哦，输入 help 查看帮助')


if __name__ == '__main__':
    lanzou_cmd = Commander()
    lanzou_cmd.set_console_style()
    lanzou_cmd.check_rar_tool()
    lanzou_cmd.init_max_size()
    lanzou_cmd.update()
    lanzou_cmd.login()
    while True:
        lanzou_cmd.process_a_cmd()
