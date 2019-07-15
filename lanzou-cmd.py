# coding=utf-8
import os
import readline
from configparser import ConfigParser
from api import lanzou


class Commander():
    def __init__(self):
        self._prompt = 'Lanzou > '
        self._lanzou = lanzou.LanZouCloud()
        self._folder_list = {}
        self._file_list = {}
        self._path_list = {}  # 完整路径-id
        self._parent_name = '根目录'
        self._parent_id = '-1'
        self._work_name = ''
        self._work_id = ''
        self._config = ConfigParser()
        self._config.read('config.ini', encoding='utf-8')

    def _update_file_list(self, id):
        """更新当前文件夹数据"""
        all_list = self._lanzou.list_dir(id)
        self._folder_list = all_list["folder_list"]
        self._file_list = all_list["file_list"]
        self._path_list = all_list["path_list"]
        parent_folders = [x for x in self._path_list.keys()]
        self._work_name = parent_folders[-1]
        self._work_id = self._path_list[parent_folders[-1]]
        if len(parent_folders) >= 2:
            self._parent_name = parent_folders[-2]
            self._parent_id = self._path_list[parent_folders[-2]]

    def login(self):
        def do_login(username, passwd):
            try:
                self._lanzou.login(username, passwd)
                self._update_file_list(-1)
                self._config.set('login', 'username', username)
                self._config.set('login', 'password', passwd)
                self._config.write(open('config.ini', 'w', encoding='utf-8'))
            except lanzou.PasswdError:
                print('用户名或密码错误')

        name = self._config.get('login', 'username')
        if not name:
            username = input('输入用户名:')
            passwd = input('输入用户密码:')
            do_login(username, passwd)
        else:
            yn = input('您已经登录{}，要切换账号吗(y/n): '.format(name))
            if yn == 'y':
                username = input('输入用户名:')
                passwd = input('输入用户密码:')
                do_login(username, passwd)
            else:
                username = self._config.get('login', 'username')
                passwd = self._config.get('login', 'password')
                do_login(username, passwd)

    def ls(self):
        self._update_file_list(self._work_id)
        for folder, id in self._folder_list.items():
            print('[文件夹]\t{:<10s}\t{:<}'.format(id, folder))
        for file, id in self._file_list.items():
            if file.endswith('.seed.txt'):
                print('$种子$\t\t{:<10s}\t{:<}'.format(id, file))
            else:
                print('=文件=\t\t{:<10s}\t{:<}'.format(id, file))

    def clear(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def cd(self, path):
        if path == '..':  # 返回上级路径
            self._update_file_list(self._parent_id)
        elif path == '.':
            pass
        elif path in self._folder_list.keys():
            folder_id = self._folder_list[path]
            self._update_file_list(folder_id)
        else:
            print('✘ 该目录不存在: {}'.format(path))
        prompt = ''
        for path in self._path_list.keys():
            prompt = prompt + path + '/'
        self._prompt = prompt.strip('/') + ' > '

    def mkdir(self, name, desc=''):
        if name in self._folder_list.keys():
            print('✘ 网盘中存在同名文件夹:{}'.format(name))
        else:
            try:
                folder_id = self._lanzou.mkdir(self._work_id, name, desc)
                self._lanzou.set_passwd(folder_id, -1)
                return folder_id
            except Exception:
                print('✘ 无法创建该文件夹:{}'.format(name))

    def rm(self, name):
        def do_rm(fid):
            if not self._lanzou.delete(fid):
                print('✘ 无法删除该文件夹(可能存在子文件夹):{}'.format(name))

        if name in self._folder_list.keys():
            do_rm(self._folder_list[name])
        elif name in self._file_list.keys():
            do_rm(self._file_list[name])
            if name.endswith('.seed.txt'):  # 如果删除种子，自动删除数据目录
                data_folder = name.replace('.seed.txt', '')
                do_rm(self._folder_list[data_folder])
        else:
            print('✘ 该文件(夹)或id不存在:{}'.format(name))

    def down(self, name):
        def do_down():
            try:
                print('正在下载: {} 到 {}'.format(name, self._config.get('path', 'save_path')))
                self._lanzou.download(share_url, save_path)
            except (lanzou.PasswdError, lanzou.LanZouCloudError):
                pwd = input('输入分享密码:')
                print('正在下载: {}'.format(name))
                self._lanzou.download(share_url, save_path, pwd)

        if name not in self._file_list.keys():
            print('✘ 该文件不存在:{}'.format(name))
        else:
            file_id = self._file_list[name]
            share_url = self._lanzou.get_share_url(file_id)
            save_path = self._config.get('path', 'save_path') or '.'
            real_name = name.replace('.seed.txt', '').replace('.dll', '')
            full_path = save_path + os.sep + real_name
            if os.path.exists(full_path):
                yn = input('该文件已存在，是否覆盖(y/n) :')
                if yn == 'y':
                    os.remove(full_path)
                    do_down()
                else:
                    print('已取消下载任务')
            else:  # 文件不存在
                do_down()

    def upload(self, path):
        def do_upload(file, folder_id):
            print('正在上传:{}'.format(file))
            try:
                self._lanzou.upload2(file, folder_id)
            except Exception:
                print('✘ 上传过程中发生错误，请重试')

        if os.path.isfile(path):
            if os.path.basename(path) in self._file_list.keys():
                print('✘ 网盘中存在同名文件')
            else:
                do_upload(path, self._work_id)
        elif os.path.isdir(path):
            folder_id = self.mkdir(os.path.basename(path), '批量上传')
            for file in os.listdir(path):
                do_upload(path + os.sep + file, folder_id)

    def share(self, name):
        if name in self._file_list.keys():
            fid = self._file_list[name]
            try:
                share_url = self._lanzou.get_share_url(fid)
                info = self._lanzou.parse(share_url)
                print('\n文件名: {}\n文件大小: {}\n分享链接: {}\n下载直链: {}\n'.format(
                    info['file_name'], info['file_size'], info['share_url'], info['direct_url'])
                )
            except Exception as e:
                print('✘ 分享时发生错误:{}'.format(e))
        elif name in self._folder_list.keys():
            fid = self._folder_list[name]
            print('\n分享链接:{}\n'.format(self._lanzou.get_share_url(fid)))
        else:
            print('✘ 该文件(夹)不存在:{}'.format(name))

    def passwd(self, name):
        def do_passwd(fid):
            passwd = input('设置访问密码(4-6位):')
            if not passwd:
                print('该文件访问密码已关闭')
                passwd = -1
            if not self._lanzou.set_passwd(fid, passwd):
                print('✘ 设置访问密码时错误:{}'.format(name))

        if name in self._file_list.keys():
            do_passwd(self._file_list[name])
        elif name in self._folder_list.keys():
            do_passwd(self._folder_list[name])
        else:
            print('✘ 该文件(夹)不存在:{}'.format(name))

    def setpath(self):
        path = input('输入保存路径(默认当前路径): ')
        if path:
            self._config.set('path', 'save_path', path)
            self._config.write(open('config.ini', 'w', encoding='utf-8'))
        else:
            print('没有修改，默认当前文件夹')

    def help(self):
        help_text = """     LanZouCloud-Cmd v1.0   by zaxtyson
        
    CMD版蓝奏云控制台，无限空间，不限速，无广告，无上传限制的船新版本。
    如果你熟悉linux系统，那么下面的操作将对你来说应该十分友好~
    顺带一提，已经实现按Tab键自动补全功能，快来试试吧
    
    命令帮助：
    help    显示本信息
    login   登录网盘/切换账号
    ls      列出网盘文件
    cd      切换工作目录
    rm      删除网盘文件(夹)
    mkdir   创建新文件夹
    share   显示文件分享信息
    clear   清空屏幕
    upload  上传文件(夹)
    down    下载文件/种子
    passwd  设置文件(夹)访问密码
    setpath 设置默认下载保存路径
    
    更详细的介绍请参考本项目的Github主页:
    https://github.com/zaxtyson/LanZouCloud   
    如有Bug反馈或建议请在GitHub提Issue或者发送邮件至：
    zaxtyson@qq.com
        """
        print(help_text)

    def run(self):
        def completer(text, rank):
            tab_list = []
            all_list = list(self._folder_list.keys()) + list(self._file_list.keys())
            for folder_name in all_list:
                if folder_name.startswith(text):
                    tab_list.append(folder_name)
            return tab_list[rank]

        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer)
        content = input(self._prompt)

        content = content.split(' ')  # 拆分命令
        cmd = content[0]
        args = ' '.join(content[1:])

        if not cmd:
            pass
        elif cmd == 'ls':
            self.ls()
        elif cmd == 'login':
            self.login()
        elif cmd == 'clear':
            self.clear()
        elif cmd == 'cd':
            self.cd(args)
        elif cmd == 'mkdir':
            self.mkdir(args)
        elif cmd == 'rm':
            self.rm(args)
        elif cmd == 'upload':
            self.upload(args)
        elif cmd == 'down':
            self.down(args)
        elif cmd == 'share':
            self.share(args)
        elif cmd == 'passwd':
            self.passwd(args)
        elif cmd == 'setpath':
            self.setpath()
        elif cmd == 'help':
            self.clear()
            self.help()
        else:
            print('✘ 不存在此命令，输入help查看帮助')


lzy_cmd = Commander()
lzy_cmd.login()
while True:
    try:
        lzy_cmd.run()
    except Exception as e:
        print('发生错误:{}'.format(e))
    except KeyboardInterrupt:
        yn = input('\n要退出吗(y/n) :')
        if yn == 'y':
            import sys

            sys.exit()
