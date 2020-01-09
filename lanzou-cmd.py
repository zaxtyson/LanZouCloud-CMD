#!python3
# coding=utf-8
import os
from configparser import ConfigParser
from getpass import getpass
from time import sleep
import readline
from lanzou.api import LanZouCloud      # pip install lanzou-api


class Commander(object):
    def __init__(self):
        self._prompt = '> '
        self._disk = LanZouCloud()
        self._folder_list = {}
        self._file_list = {}
        self._path_list = {}
        self._parent_id = -1
        self._parent_name = ''
        self._work_name = ''
        self._work_id = -1
        self._config = ConfigParser()
        self._config.read('config.ini', encoding='utf-8')

    def _show_progress(self, file_name, total_size, now_size):
        """显示进度条的回调函数"""
        percent = now_size / total_size
        bar_len = 40  # 进度条长总度
        bar_str = '>' * round(bar_len * percent) + '=' * round(bar_len * (1 - percent))
        print('\r{:.2f}%\t[{}] {:.1f}/{:.1f}MB | {} '.format(
            percent * 100, bar_str, now_size / 1048576, total_size / 1048576, file_name), end='')
        if total_size == now_size:
            print('')  # 下载完成换行

    def _refresh(self, dir_id=-1):
        """刷新当前文件夹和路径信息"""
        self._file_list = self._disk.get_file_list2(dir_id)  # {name-id}
        self._folder_list = self._disk.get_dir_list(dir_id)
        self._path_list = self._disk.get_full_path(dir_id)
        self._prompt = '/'.join(list(self._path_list.keys())) + ' > '
        self._work_name = list(self._path_list.keys())[-1]
        self._work_id = self._path_list.get(self._work_name, -1)
        if dir_id != -1:
            self._parent_name = list(self._path_list.keys())[-2]
            self._parent_id = self._path_list.get(self._parent_name, -1)

    def check_rar_tool(self):
        """设置RAR解压工具"""
        rar_bin = self._config.get('path', 'rar_bin')
        if self._disk.set_rar_tool(rar_bin) == LanZouCloud.ZIP_ERROR:
            print('ERROR : 缺少解压工具，请修改配置文件!!!')
            sleep(2)
            exit(-1)

    def set_console_style(self):
        """设置命令行窗口样式"""
        if os.name != 'nt': return None
        os.system('mode con cols=110 lines=30')
        os.system('title LanZouCloud-CMD 2.0 by zaxtyson')

    def login(self):
        """登录网盘"""
        username = self._config.get('login', 'username') or input('输入用户名:')
        password = self._config.get('login', 'password') or getpass('输入密码:')
        if self._disk.login(username, password) != LanZouCloud.SUCCESS:
            print('登录失败 : 用户名或密码错误 :(')
            return None
        # 登录成功保存用户名和密码
        self._config.set('login', 'username', username)
        self._config.set('login', 'password', password)
        self._config.write(open('config.ini', 'w', encoding='utf-8'))
        # 刷新文件列表
        self._refresh(self._work_id)

    def ls(self):
        """列出文件"""
        for folder, f_id in self._folder_list.items():
            print('ID:{:<10d}\t{}/'.format(f_id, folder))
        for file_name, f_id in self._file_list.items():
            print('ID:{:<10d}\t{}'.format(f_id, file_name))

    def clear(self):
        """清空屏幕"""
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def cd(self, dir_name):
        """切换工作目录"""
        if self._work_name == 'Recovery' and dir_name not in ['.', '..']:
            print('ERROR : 回收站模式下仅支持 > cd ..')
            return None
        if dir_name == '..':  # 返回上级路径
            self._refresh(self._parent_id)
        elif dir_name == '.':
            pass
        elif dir_name in self._folder_list.keys():
            folder_id = self._folder_list[dir_name]
            self._refresh(folder_id)
        else:
            print('ERROR : 该文件夹不存在: {}'.format(dir_name))

    def mkdir(self, name, desc=''):
        """创建文件夹"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        if name in self._folder_list.keys():
            print('ERROR : 文件夹已存在:{}'.format(name))
        else:
            dir_id = self._disk.mkdir(self._work_id, name, desc)
            if dir_id == LanZouCloud.MKDIR_ERROR:
                print('ERROR : 创建文件夹失败:{}'.format(name))
            else:
                self._folder_list.update({name: dir_id})

    def rm(self, name):
        """删除文件"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        file_id = self._file_list.get(name, None)
        dir_id = self._folder_list.get(name, None)
        if file_id is None and dir_id is None:
            print('ERROR : 文件(夹)不存在:{}'.format(name))
            return None
        # 删除文件
        if file_id is not None and dir_id is None:
            if self._disk.delete(file_id, is_file=True) == LanZouCloud.SUCCESS:
                self._file_list.pop(name)
            else:
                print('ERROR : 删除文件失败:{}'.format(name))
        # 删除文件夹
        if dir_id is not None and file_id is None:
            if self._disk.delete(dir_id, is_file=False) == LanZouCloud.SUCCESS:
                self._folder_list.pop(name)
            else:
                print('ERROR : 删除失败,存在子文件夹?:{}'.format(name))

    def ls_recovery(self):
        """查看回收站"""
        rec = self._disk.list_recovery()
        self._file_list = rec['file_list']
        self._folder_list = rec['folder_list']
        self._parent_name = list(self._path_list.keys())[-1]
        self._parent_id = self._path_list.get(self._parent_name)
        self._prompt = 'LanZouCloud/Recovery > '
        self._work_name = 'Recovery'

    def clean(self):
        """清空回收站"""
        if input('INFO : 确认清空回收站?(y) ') == 'y':
            self._disk.clean_recycle()
        if self._work_name == 'Recovery':
            sleep(2)  # 等待刷新
            self.ls_recovery()

    def recovery(self, name):
        """恢复文件"""
        if self._work_name != 'Recovery':
            print('INFO : 该命令仅在回收站模式下使用 :)')
            return None
        file_id = self._file_list.get(name, None)
        dir_id = self._folder_list.get(name, None)
        if file_id is None and dir_id is None:
            print('ERROR : 文件(夹)不存在:{}'.format(name))
            return None
        # 恢复文件
        if file_id is not None and dir_id is None:
            if self._disk.recovery(file_id, is_file=True) == LanZouCloud.SUCCESS:
                self._file_list.pop(name)
            else:
                print('ERROR : 恢复文件失败:{}'.format(name))
        # 恢复文件夹
        if dir_id is not None and file_id is None:
            if self._disk.recovery(dir_id, is_file=False) == LanZouCloud.SUCCESS:
                self._folder_list.pop(name)
            else:
                print('ERROR : 恢复文件夹失败:{}'.format(name))

    def rename(self, name):
        """重命名"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        fid = self._folder_list.get(name, None)
        if fid is None:
            print('ERROR : 文件夹不存在:{}'.format(name))
        else:
            new_name = input('重命名 {} -> '.format(name)) or None
            if new_name is not None:
                self._disk.rename_dir(fid, str(new_name))
                self._refresh(self._work_id)

    def move(self, name):
        """移动文件"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        old_fid = self._file_list.get(name, None)
        if old_fid is None:
            print('ERROR : 源文件不存在:{}'.format(name))
            return None
        new_fid = input('移动到 -> ID:') or None
        if self._disk.move_file(old_fid, new_fid) == LanZouCloud.SUCCESS:
            self._refresh(self._work_id)
        else:
            print('ERROR : 该ID对应的文件夹不存在:{}'.format(new_fid))

    def _down_by_id(self, name):
        """通过id下载文件(夹)"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        save_path = self._config.get('path', 'save_path')
        if self._folder_list.get(name, None):
            self._disk.download_dir2(self._folder_list.get(name), save_path, self._show_progress)
        elif self._file_list.get(name, None):
            self._disk.download_file2(self._file_list.get(name), save_path, self._show_progress)
        else:
            print('ERROR : 文件(夹)不存在:{}'.format(name))

    def _print_error(self, code):
        if code == LanZouCloud.SUCCESS:
            return None
        elif code == LanZouCloud.LACK_PASSWORD:
            print('ERROR : 缺少提取码')
        elif code == LanZouCloud.PASSWORD_ERROR:
            print('ERROR : 提取码错误')
        elif code == LanZouCloud.FILE_CANCELLED:
            print('ERROR : 该链接已失效')
        elif code == LanZouCloud.ZIP_ERROR:
            print('ERROR : 解压过程异常')
        else:
            print('ERROR : 下载过程异常，请重试')

    def _down_by_url(self, url):
        """通过url下载"""
        save_path = self._config.get('path', 'save_path')
        if self._disk.is_file_url(url):
            code = self._disk.download_file(url, '', save_path, self._show_progress)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件的提取码 : ') or ''
                code2 = self._disk.download_file(url, str(pwd), save_path, self._show_progress)
                self._print_error(code2)
            else:
                self._print_error(code)
        elif self._disk.is_folder_url(url):
            code = self._disk.download_dir(url, '', save_path, self._show_progress)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件夹的提取码 : ') or ''
                code2 = self._disk.download_dir(url, str(pwd), save_path, self._show_progress)
                self._print_error(code2)
            else:
                self._print_error(code)
        else:
            print('ERROR : 该链接无效')

    def down(self, arg):
        """自动选择下载方式"""
        if arg.startswith('http'):
            self._down_by_url(arg)
        else:
            self._down_by_id(arg)

    def upload(self, path):
        """上传文件(夹)"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        path = path.strip('\"\' ')
        if not os.path.exists(path):
            print('ERROR : 文件不存在:{}'.format(path))
            return None
        if os.path.isdir(path):
            print('INFO : 文件夹批量上传:{}'.format(path))
            self._disk.upload_dir(path, self._work_id, self._show_progress)
            self._refresh(self._work_id)
        else:
            self._disk.upload_file(path, self._work_id, self._show_progress)
            self._refresh(self._work_id)

    def share(self, name):
        """显示分享信息"""
        if self._work_name == 'Recovery':
            print('ERROR : 回收站模式下无法使用此操作')
            return None
        if self._file_list.get(name, None):
            info_all = self._disk.get_file_list(self._work_id).get(name)
            share_info = self._disk.get_share_info(info_all['id'], is_file=True)
            d_url = self._disk.get_direct_url2(info_all['id'])
            print('-' * 50)
            print('文件名 : {}'.format(name))
            print('提取码 : {}'.format(share_info['passwd'] or '无'))
            print('文件大小 : {}'.format(info_all['size']))
            print('下载次数 : {}'.format(info_all['downs']))
            print('上传时间 : {}'.format(info_all['time']))
            print('分享链接 : {}'.format(share_info['share_url']))
            print('下载直链 : {}'.format(d_url['direct_url'] or '无'))
            print('-' * 50)
        elif self._folder_list.get(name, None):
            share_info = self._disk.get_share_info(self._folder_list.get(name), is_file=False)
            print('-' * 50)
            print('文件夹名 : {}'.format(name))
            print('提取码 : {}'.format(share_info['passwd'] or '无'))
            print('分享链接 : {}'.format(share_info['share_url']))
            print('-' * 50)
        else:
            print('ERROR : 文件(夹)不存在:{}'.format(name))

    def passwd(self, name):
        """设置文件(夹)提取码"""
        file_flag = True       # 默认 fid 为文件 id
        fid = self._file_list.get(name, None)
        if not fid:
            fid = self._folder_list.get(name, None)
            file_flag = False      # fid 为文件夹 id
        if not fid:
            print('ERROR : 文件(夹)不存在:{}'.format(name))
            return None
        info = self._disk.get_share_info(fid, is_file=file_flag)
        new_pass = input('修改提取码 "{}" -> '.format(info['passwd'] or '无'))
        if 2 <= len(new_pass) <= 6:
            if new_pass == 'off': new_pass = ''
            self._disk.set_share_passwd(fid, new_pass, is_file=file_flag)
        else:
            print('ERROR : 提取码为2-6位字符,关闭请输入off')

    def setpath(self):
        print('当前保存路径 : {}'.format(self._config.get('path', 'save_path')))
        path = input('修改为 -> ').strip("\"\' ")
        if os.path.isdir(path):
            self._config.set('path', 'save_path', path)
            self._config.write(open('config.ini', 'w', encoding='utf-8'))
        else:
            print('ERROR : 路径非法,取消修改')

    def logout(self):
        """注销"""
        self._disk.logout()
        self._config.set('login', 'username', '')
        self._config.set('login', 'password', '')
        self._config.write(open('config.ini', 'w', encoding='utf-8'))
        self._file_list = {}
        self._folder_list = {'LanZouCloud': -1}
        self._parent_id = -1
        self._parent_name = ''
        self._work_id = -1
        self._work_name = ''

    def help(self):
        help_text = """
    LanZouCloud-Cmd v2.2.1   by zaxtyson
        
    • CMD版蓝奏云控制台，支持路径自动补全
    • 支持大文件上传，解除格式限制
    • 支持提取直链，批量下载上传
    
    命令帮助：
    help    显示本信息
    login   登录网盘/切换账号
    logout  注销当前账号
    ls      列出文件(夹)
    cd      切换工作目录
    cdrec   进入回收站
    rm      删除网盘文件(夹)
    mkdir   创建新文件夹
    share   显示分享信息
    clear   清空屏幕
    clean   清空回收站
    upload  上传文件(夹)
    down    下载文件(夹)
    passwd  设置文件(夹)提取码
    setpath 设置默认下载路径
    rename  重命名文件夹
    mv      移动文件到某个文件夹
    bye     退出本程序
    
    更详细的介绍请参考本项目的Github主页:
    https://github.com/zaxtyson/LanZouCloud-CMD   
    如有Bug反馈或建议请在 GitHub 提 Issue 或者
    发送邮件至 : zaxtyson@foxmail.com
    感谢您的使用 :)
        """
        print(help_text)

    def process_a_cmd(self):
        """处理一条用户命令"""
        def completer(text, rank):
            """自动补全"""
            tab_list = []
            all_list = list(self._folder_list.keys()) + list(self._file_list.keys())
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
            print('INFO : 退出本程序请输入bye')
            return -1
        if len(args) == 0: return None
        cmd = args[0]
        first_arg = ' '.join(args[1:])

        if cmd == 'rm':
            self.rm(first_arg)
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
            self.ls_recovery()
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
            self.move(first_arg)
        elif cmd == 'help':
            self.help()
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
