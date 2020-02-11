# coding=utf-8
import os
from getpass import getpass
from time import sleep
import readline
from lanzou.api import LanZouCloud  # pip install lanzou-api
from pickle import load, dump


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
        print('\r{:.2f}%\t[{}] {:.1f}/{:.1f}MB | {} '.format(
            percent * 100, bar_str, now_size / 1048576, total_size / 1048576, file_name), end='')
        if total_size == now_size:
            print('')  # 下载完成换行

    @staticmethod
    def set_console_style():
        """设置命令行窗口样式"""
        if os.name != 'nt':
            return None
        os.system('mode con cols=110 lines=35')
        os.system('title 蓝奏云CMD控制台')

    @staticmethod
    def _print_logo():
        """输出logo"""
        logo_str = """
        _                  ______            _____ _                 _ 
       | |                |___  /           /  __ \ |               | |
       | |     __ _ _ __     / /  ___  _   _| /  \/ | ___  _   _  __| |
       | |    / _  |  _ \   / /  / _ \| | | | |   | |/ _ \| | | |/ _  |
       | |___| (_| | | | | / /__| (_) | |_| | \__/\ | (_) | |_| | (_| |
       \_____/\____|_| |_|\_____/\___/ \____|\____/_|\___/ \____|\____|
      --------------------------------------------------------------------
      Github: https://github.com/zaxtyson/LanZouCloud-CMD (Version: 2.3.3)
      --------------------------------------------------------------------
            """
        print(logo_str)

    def _refresh(self, dir_id=-1):
        """刷新当前文件夹和路径信息"""
        self._file_list = self._disk.get_file_list(dir_id)
        self._file_id_list = self._disk.get_file_id_list(dir_id)
        self._dir_list = self._disk.get_dir_list(dir_id)
        self._dir_id_list = self._disk.get_dir_id_list(dir_id)
        self._path_list = self._disk.get_full_path(dir_id)
        self._prompt = '/'.join(list(self._path_list.keys())) + ' > '
        self._work_name = list(self._path_list.keys())[-1]
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
            sleep(2)
            exit(-1)

    def _check_down_path(self):
        """检查下载路径"""
        if not self._config.get('path'):
            print('请设置文件下载路径')
            self.setpath()

    def login(self):
        """登录网盘"""
        self.clear()
        self._print_logo()
        cookie = self._config.get('cookie')
        if not cookie or self._disk.login_by_cookie(cookie) != LanZouCloud.SUCCESS:
            username = input('输入用户名:')
            password = getpass('输入密码:')
            if self._disk.login(username, password) != LanZouCloud.SUCCESS:
                print('登录失败 : 用户名或密码错误 :(')
                return None
            # 登录成功保存用户 cookie
            self._config['cookie'] = self._disk.get_cookie()
            with open(self._config_file, 'wb') as f:
                dump(self._config, f)
        # 刷新文件列表
        self._refresh(self._work_id)

    def ls(self):
        """列出文件(夹)"""
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
                print("#{0:<12}{1:<4}{2:{4}<10} \t {3}/".format(
                    folder['id'], pwd_str, folder['desc'], folder['name'], chr(12288)  # 中文空格填充，保持对齐
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
                self._refresh(self._parent_id)
                return None
            print('INFO : 退出回收站请输入 "cd .."')
            return None
        # 正常工作模式
        if dir_name == '..':  # 返回上级路径
            self._refresh(self._parent_id)
        elif dir_name == '.':
            pass
        elif dir_name in self._dir_id_list.keys():
            folder_id = self._dir_id_list.get(dir_name)
            self._refresh(folder_id)
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

    def delete(self, name):
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

    def cd_rec(self):
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

    def recovery(self, name):
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
        """重命名文件夹"""
        fid = self._dir_id_list.get(name)
        if not fid:
            print(f'ERROR : ╰（‵□′）╯ 没有这个文件夹的啦: {name}')
            return None
        new_name = input(f'重命名 "{name}" -> ') or None
        if not new_name:
            print(f'INFO : 重命名操作取消')
            return None
        if self._disk.rename_dir(fid, str(new_name)) == LanZouCloud.SUCCESS:
            pop_id = self._dir_id_list.pop(name)  # 只更新本地文件夹名(调用_refresh()要等 1.5s 才能刷新信息)
            self._dir_id_list.setdefault(new_name, pop_id)
            for folder in self._dir_list:
                if folder['name'] == name:
                    folder['name'] = new_name
        else:
            print('ERROR : (＃°Д°) 重命名...失败了')

    @check_rec_mode
    def move_file(self, filename):
        """移动文件"""
        file_id = self._file_id_list.get(filename, None)
        if not file_id:
            print(f'ERROR : >_< 文件不存在: {filename}')
            return None
        backup = self._dir_id_list  # 备份文件夹 name-id 列表
        self._dir_id_list = self._disk.get_folder_id_list()  # 方便自动补全
        self._dir_id_list.pop(self._work_name)  # 不能移动文件到当前文件夹
        files_per_line = 1
        print('# 请选择目标文件夹(TAB键补全)')
        for folder, fid in self._dir_id_list.items():
            print(' -> {:<32}'.format(folder), end='\t')
            if files_per_line == 2:  # 一行输出 x 个文件夹
                files_per_line = 1
                print('')
            else:
                files_per_line += 1
        folder_name = input(f'\n移动 "{filename}" -> ') or ' '
        folder_id = self._dir_id_list.get(folder_name, None)
        if not folder_id:
            print(f'ERROR : 文件夹不存在的啦: {folder_name}')
            self._dir_id_list = backup  # 还原文件夹 name-id 索引
            return None
        if self._disk.move_file(file_id, folder_id) == LanZouCloud.SUCCESS:
            self._refresh(self._work_id)
        else:
            print('ERROR : (⊙ˍ⊙) 移动文件失败了!')
        self._dir_id_list = backup  # 还原文件夹 name-id 索引

    @check_rec_mode
    def _down_by_id(self, name):
        """通过 id 下载文件(夹)"""
        save_path = self._config.get('path') or self._default_down_path
        if self._file_id_list.get(name, None):  # 如果是文件
            code = self._disk.down_file_by_id(self._file_id_list.get(name), save_path, self._show_progress)
            if code != LanZouCloud.SUCCESS:
                print(f"ERROR : 文件下载失败: {name}")
        elif self._dir_id_list.get(name, None):  # 如果是文件夹
            info = self._disk.down_dir_by_id(self._dir_id_list.get(name), save_path, self._show_progress)
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
            info = self._disk.down_dir_by_url(url, '', save_path, self._show_progress)
            if info['code'] == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件夹的提取码 : ') or ''
                info2 = self._disk.down_dir_by_url(url, str(pwd), save_path, self._show_progress)
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

        if os.path.isdir(path):
            print(f'INFO : 批量上传文件夹: {path}')
            info = self._disk.upload_dir(path, self._work_id, self._show_progress)
            if info['code'] != LanZouCloud.SUCCESS:
                print(f"ERROR : 以下文件上传失败: {' '.join(info['failed'])}")
            self._refresh(self._work_id)
        else:
            info = self._disk.upload_file(path, self._work_id, self._show_progress)
            if info['code'] != LanZouCloud.SUCCESS:
                print(f"ERROR : 文件上传失败: {' '.join(info['failed'])}")
            self._refresh(self._work_id)

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
                self._refresh(self._work_id)
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
                self._refresh(self._work_id)
            else:
                print('ERROR : 提取码为2-12位字符,关闭请输入off')
        else:
            print(f'ERROR : 文件(夹)不存在: {name}')

    @check_rec_mode
    def set_desc(self, name):
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
            self._refresh(self._work_id)
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
            self._refresh(self._work_id)
        else:
            print(f'ERROR : 文件(夹)不存在: {name}')

    def setpath(self):
        """设置下载路径"""
        print(f"当前下载路径 : {self._config.get('path')}")
        path = input('修改为 -> ').strip("\"\' ")
        if os.path.isdir(path):
            self._config['path'] = path
            with open(self._config_file, 'wb') as f:
                dump(self._config, f)
        else:
            print('ERROR : 路径非法,取消修改')

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
        self._work_name = ''
        self._config['cookie'] = None
        with open(self._config_file, 'wb') as f:
            dump(self._config, f)

    @staticmethod
    def print_help():
        help_text = """
    • CMD版蓝奏云控制台，按 TAB 自动补全路径
    • 支持大文件上传，解除文件格式限制
    • 支持提取直链，批量下载上传
    
    命令帮助 :
    help        显示本信息
    refresh     强制刷新文件列表信息
    login       登录网盘/切换账号
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
    rename      重命名文件夹
    desc        修改文件(夹)描述
    mv          移动文件到某个文件夹
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
        cmd = args[0]
        first_arg = ' '.join(args[1:])

        if cmd == 'rm':
            self.delete(first_arg)
        elif cmd == 'refresh':
            self._refresh(self._work_id)
        elif cmd == 'ls':
            self.ls()
        elif cmd == 'login':
            self.login()
        elif cmd == 'logout':
            self.logout()
            self.login()
        elif cmd == 'clean':
            self.clean()
        elif cmd == 'cdrec':
            self.cd_rec()
        elif cmd == 'rec':
            self.recovery(first_arg)
        elif cmd == 'clear':
            self.clear()
        elif cmd == 'cd':
            self.cd(first_arg)
        elif cmd == 'mkdir':
            self.mkdir(first_arg)
        elif cmd == 'upload':
            self.upload(first_arg)
        elif cmd == 'down':
            self.down(first_arg)
        elif cmd == 'share':
            self.share(first_arg)
        elif cmd == 'passwd':
            self.passwd(first_arg)
        elif cmd == 'setpath':
            self.setpath()
        elif cmd == 'rename':
            self.rename(first_arg)
        elif cmd == 'mv':
            self.move_file(first_arg)
        elif cmd == 'desc':
            self.set_desc(first_arg)
        elif cmd == 'help':
            self.print_help()
        elif cmd == 'bye':
            exit(0)
        else:
            print('ERROR : 命令不存在哦，输入help查看帮助')


if __name__ == '__main__':
    lanzou_cmd = Commander()
    lanzou_cmd.set_console_style()
    lanzou_cmd.check_rar_tool()
    lanzou_cmd.login()
    while True:
        lanzou_cmd.process_a_cmd()
