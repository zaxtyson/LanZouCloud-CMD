from getpass import getpass
from lanzou.api.types import *
from lanzou.api.utils import is_file_url, is_folder_url
from lanzou.api.models import FileList, FolderList
from lanzou.cmder import config
from lanzou.cmder.utils import *
from lanzou.cmder.recovery import Recovery
from webbrowser import open_new_tab


class Commander:
    """蓝奏网盘命令行"""

    def __init__(self):
        self._prompt = '> '
        self._disk = LanZouCloud()
        self._dir_list = FolderList()
        self._file_list = FileList()
        self._path_list = FolderList()
        self._parent_id = -1
        self._parent_name = ''
        self._work_name = ''
        self._work_id = -1
        self._last_work_id = -1
        self._disk.set_max_size(config.max_size)

    @staticmethod
    def clear():
        clear_screen()

    @staticmethod
    def help():
        print_help()

    @staticmethod
    def update():
        check_update()

    def cdrec(self):
        """进入回收站模式"""
        rec = Recovery(self._disk)
        rec.run()
        self.refresh()

    def refresh(self, dir_id=None):
        """刷新当前文件夹和路径信息"""
        dir_id = self._work_id if dir_id is None else dir_id
        self._file_list = self._disk.get_file_list(dir_id)
        self._dir_list = self._disk.get_dir_list(dir_id)
        self._path_list = self._disk.get_full_path(dir_id)
        self._prompt = '/'.join(self._path_list.all_name) + ' > '
        self._last_work_id = self._work_id
        self._work_name = self._path_list[-1].name
        self._work_id = self._path_list[-1].id
        if dir_id != -1:  # 如果存在上级路径
            self._parent_name = self._path_list[-2].name
            self._parent_id = self._path_list[-2].id

    def login(self):
        """登录网盘"""
        if not config.cookie or self._disk.login_by_cookie(config.cookie) != LanZouCloud.SUCCESS:
            username = input('输入用户名:')
            password = getpass('输入密码:')
            code = self._disk.login(username, password)
            if code == LanZouCloud.NETWORK_ERROR:
                error("登录失败,网络连接异常")
                return None
            elif code == LanZouCloud.FAILED:
                error('登录失败,用户名或密码错误 :(')
                return None
            # 登录成功保存用户 cookie
            config.cookie = self._disk.get_cookie()
        self.refresh()

    def clogin(self):
        """使用 cookie 登录"""
        open_new_tab('https://pc.woozooo.com/')
        info("请设置 Cookie 内容:")
        ylogin = input("ylogin=")
        disk_info = input("phpdisk_info=")
        if not ylogin or not disk_info:
            error("请输入正确的 Cookie 信息")
            return None
        cookie = {"ylogin": str(ylogin), "phpdisk_info": disk_info}
        if self._disk.login_by_cookie(cookie) == LanZouCloud.SUCCESS:
            config.cookie = cookie
            self.refresh()
        else:
            error("登录失败,请检查 Cookie 是否正确")

    def logout(self):
        """注销"""
        clear_screen()
        self._disk.logout()
        self._file_list.clear()
        self._dir_list.clear()
        self._path_list = FolderList()
        self._parent_id = -1
        self._work_id = -1
        self._last_work_id = -1
        self._parent_name = ''
        self._work_name = ''

        config.cookie = None

    def ls(self):
        """列出文件(夹)"""
        for folder in self._dir_list:
            pwd_str = '✦' if folder.has_pwd else '✧'
            print("#{0:<12}{1:<4}{2}{3}/".format(
                folder.id, pwd_str, text_align(folder.desc, 24), folder.name))
        for file in self._file_list:
            pwd_str = '✦' if file.has_pwd else '✧'
            print("#{0:<12}{1:<4}{2:<14}{3:<10}{4}".format(
                file.id, pwd_str, file.time, file.size, file.name))

    def cd(self, dir_name):
        """切换工作目录"""
        if not dir_name:
            info('cd .. 返回上级路径, cd - 返回上次路径, cd / 返回根目录')
        elif dir_name == '..':
            self.refresh(self._parent_id)
        elif dir_name == '/':
            self.refresh(-1)
        elif dir_name == '-':
            self.refresh(self._last_work_id)
        elif dir_name == '.':
            pass
        elif folder := self._dir_list.find_by_name(dir_name):
            self.refresh(folder.id)
        else:
            error(f'文件夹不存在: {dir_name}')

    def mkdir(self, name, desc=''):
        """创建文件夹"""
        if self._dir_list.find_by_name(name):
            error(f'文件夹已存在: {name}')
            return None

        dir_id = self._disk.mkdir(self._work_id, name, desc)
        if dir_id == LanZouCloud.MKDIR_ERROR:
            error(f'创建文件夹失败(深度最大 4 级)')
        else:  # 创建成功，添加到文件夹列表，减少向服务器请求次数
            self._dir_list.append(Folder(name, dir_id, False, desc))

    def rm(self, name):
        """删除文件(夹)"""
        if file := self._file_list.find_by_name(name):  # 删除文件
            if self._disk.delete(file.id, True) == LanZouCloud.SUCCESS:
                self._file_list.pop_by_id(file.id)
            else:
                error(f'删除文件失败: {name}')
        elif folder := self._dir_list.find_by_name(name):  # 删除文件夹
            if self._disk.delete(folder.id, False) == LanZouCloud.SUCCESS:
                self._dir_list.pop_by_id(folder.id)
            else:
                error(f'删除文件夹失败(存在子文件夹?): {name}')
        else:
            error(f'文件(夹)不存在: {name}')

    def rename(self, name):
        """重命名文件或文件夹(需要会员)"""
        if folder := self._dir_list.find_by_name(name):
            fid, is_file = folder.id, False
        elif file := self._file_list.find_by_name(name):
            fid, is_file = file.id, True
        else:
            error(f'没有这个文件(夹)的啦: {name}')
            return None

        new_name = input(f'重命名 "{name}" 为 ') or ''
        if not new_name:
            info(f'重命名操作取消')
            return None

        if is_file:
            if self._disk.rename_file(fid, new_name) != LanZouCloud.SUCCESS:
                error('(＃°Д°) 文件重命名失败, 请开通会员，文件名不要带后缀')
                return None
            # 只更新本地索引的文件夹名(调用refresh()要等 1.5s 才能刷新信息)
            self._file_list.update_by_id(fid, name=name)
        else:
            if self._disk.rename_dir(fid, new_name) != LanZouCloud.SUCCESS:
                error('文件夹重命名失败')
                return None
            self._dir_list.update_by_id(fid, name=new_name)

    def mv(self, name):
        """移动文件或文件夹"""
        if file := self._file_list.find_by_name(name):
            fid, is_file = file.id, True
        elif folder := self._dir_list.find_by_name(name):
            fid, is_file = folder.id, False
        else:
            error(f"文件(夹)不存在: {name}")
            return None

        path_list = self._disk.get_move_paths()
        path_list = {'/'.join(path.all_name): path[-1].id for path in path_list}
        choice_list = list(path_list.keys())

        def _condition(typed_str, choice_str):
            path_depth = len(choice_str.split('/'))
            # 没有输入时, 补全 LanZouCloud,深度 1
            if not typed_str and path_depth == 1:
                return True
            # LanZouCloud/ 深度为 2,补全同深度的文件夹 LanZouCloud/test 、LanZouCloud/txt
            # LanZouCloud/tx 应该补全 LanZouCloud/txt
            if path_depth == len(typed_str.split('/')) and choice_str.startswith(typed_str):
                return True

        set_completer(choice_list, condition=_condition)
        choice = input('请输入路径(TAB键补全) : ')
        if not choice or choice not in choice_list:
            error(f"目标路径不存在: {choice}")
            return None
        folder_id = path_list.get(choice)
        if is_file:
            if self._disk.move_file(fid, folder_id) == LanZouCloud.SUCCESS:
                self._file_list.pop_by_id(fid)
            else:
                error(f"移动文件到 {choice} 失败")
        else:
            if self._disk.move_folder(fid, folder_id) == LanZouCloud.SUCCESS:
                self._dir_list.pop_by_id(fid)
            else:
                error(f"移动文件夹到 {choice} 失败")

    def _down_by_id(self, name):
        """通过 id 下载文件(夹)"""
        save_path = config.save_path
        if file := self._file_list.find_by_name(name):  # 如果是文件
            code = self._disk.down_file_by_id(file.id, save_path, show_progress)
            if code != LanZouCloud.SUCCESS:
                error(f"文件下载失败: {name}")
        elif folder := self._dir_list.find_by_name(name):  # 如果是文件夹
            self._disk.down_dir_by_id(folder.id, save_path, callback=show_progress, mkdir=True,
                                      failed_callback=show_down_failed)
        else:
            error(f'文件(夹)不存在: {name}')

    def _down_by_url(self, url):
        """通过 url 下载"""
        save_path = config.save_path
        if is_file_url(url):  # 如果是文件
            code = self._disk.down_file_by_url(url, '', save_path, show_progress)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件的提取码 : ') or ''
                code2 = self._disk.down_file_by_url(url, str(pwd), save_path, show_progress)
                if code2 != LanZouCloud.SUCCESS:
                    error(f"下载失败,原因: {why_error(code2)}")
            elif code != LanZouCloud.SUCCESS:
                error(f"下载失败,原因: {why_error(code)}")
        elif is_folder_url(url):  # 如果是文件夹
            code = self._disk.down_dir_by_url(url, '', save_path, callback=show_progress, mkdir=True,
                                              failed_callback=show_down_failed)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件夹的提取码 : ') or ''
                code2 = self._disk.down_dir_by_url(url, str(pwd), save_path, callback=show_progress, mkdir=True,
                                                   failed_callback=show_down_failed)
                if code2 != LanZouCloud.SUCCESS:
                    error(f"下载失败,原因: {why_error(code2)}")
            elif code != LanZouCloud.SUCCESS:
                error(f"下载失败,原因: {why_error(code)}")
        else:  # 链接无效
            error('(。>︿<) 该分享链接无效')

    def down(self, arg):
        """自动选择下载方式"""
        try:
            if arg.startswith('http'):
                self._down_by_url(arg)
            else:
                self._down_by_id(arg)
        except KeyboardInterrupt:
            print('')
            info('当前下载任务已取消')

    def upload(self, path):
        """上传文件(夹)"""
        path = path.strip('\"\' ')  # 去除直接拖文件到窗口产生的引号
        if not os.path.exists(path):
            error(f'该路径不存在哦: {path}')
            return None

        try:
            if os.path.isdir(path):
                info(f'批量上传文件: {path}')
                self._disk.upload_dir(path, self._work_id, callback=show_progress, failed_callback=show_upload_failed)
                self.refresh()
            else:
                self._disk.upload_file(path, self._work_id, callback=show_progress)
                self.refresh()
        except KeyboardInterrupt:
            print('')
            info("上传已终止")

    def share(self, name):
        """显示分享信息"""
        if file := self._file_list.find_by_name(name):  # 文件
            inf = self._disk.get_file_info_by_id(file.id)
            if inf.code != LanZouCloud.SUCCESS:
                error('获取文件信息出错')
                return None

            print("-" * 50)
            print(f"文件名   : {name}")
            print(f"提取码   : {inf.pwd or '无'}")
            print(f"文件大小 : {inf.size}")
            print(f"上传时间 : {inf.time}")
            print(f"分享链接 : {inf.url}")
            print(f"描述信息 : {inf.desc or '无'}")
            print(f"下载直链 : {inf.durl or '无'}")
            print("-" * 50)

        elif folder := self._dir_list.find_by_name(name):  # 文件夹
            inf = self._disk.get_folder_info_by_id(folder.id)
            if inf.code != LanZouCloud.SUCCESS:
                print('ERROR : 获取文件夹信息出错')
                return None

            print("-" * 80)
            print(f"文件夹名 : {name}")
            print(f"提取码   : {inf.folder.pwd or '无'}")
            print(f"分享链接 : {inf.folder.url}")
            print(f"描述信息 : {inf.folder.desc or '无'}")
            print("-" * 80)

            for file in inf.files:
                print("+ {0:<12}{1:<9}{2}\t{3}".format(file.time, file.size, file.url, file.name))
            if len(inf.files) != 0:
                print("-" * 80)
        else:
            error(f"文件(夹)不存在: {name}")

    def passwd(self, name):
        """设置文件(夹)提取码"""
        if file := self._file_list.find_by_name(name):  # 文件
            inf = self._disk.get_share_info(file.id, True)
            new_pass = input(f'修改提取码 "{inf.pwd or "无"}" -> ')
            if 2 <= len(new_pass) <= 6:
                if new_pass == 'off': new_pass = ''
                if self._disk.set_passwd(file.id, str(new_pass), True) != LanZouCloud.SUCCESS:
                    error('设置文件提取码失败')
                self.refresh()
            else:
                error('提取码为2-6位字符,关闭请输入off')
        elif folder := self._dir_list.find_by_name(name):  # 文件夹
            inf = self._disk.get_share_info(folder.id, False)
            new_pass = input(f'修改提取码 "{inf.pwd or "无"}" -> ')
            if 2 <= len(new_pass) <= 12:
                if new_pass == 'off': new_pass = ''
                if self._disk.set_passwd(folder.id, str(new_pass), False) != LanZouCloud.SUCCESS:
                    error('设置文件夹提取码失败')
                self.refresh()
            else:
                error('提取码为2-12位字符,关闭请输入off')
        else:
            error(f'文件(夹)不存在: {name}')

    def desc(self, name):
        """设置文件描述"""
        if file := self._file_list.find_by_name(name):  # 文件
            inf = self._disk.get_share_info(file.id, True)
            print(f"当前描述: {inf.desc or '无'}")
            desc = input(f'修改为 -> ')
            if not desc:
                error(f'文件描述不允许为空')
                return None
            if self._disk.set_desc(file.id, str(desc), True) != LanZouCloud.SUCCESS:
                error(f'文件描述修改失败')
            self.refresh()
        elif folder := self._dir_list.find_by_name(name):  # 文件夹
            inf = self._disk.get_share_info(folder.id, False)
            print(f"当前描述: {inf.desc}")
            desc = input(f'修改为 -> ') or ''
            if self._disk.set_desc(folder.id, str(desc), False) == LanZouCloud.SUCCESS:
                if len(desc) == 0:
                    info('文件夹描述已关闭')
            else:
                error(f'文件夹描述修改失败')
            self.refresh()
        else:
            error(f'文件(夹)不存在: {name}')

    def setpath(self):
        """设置下载路径"""
        print(f"当前下载路径 : {config.save_path}")
        path = input('修改为 -> ').strip("\"\' ")
        if os.path.isdir(path):
            config.save_path = path
        else:
            error('路径非法,取消修改')

    def setsize(self):
        """设置上传限制"""
        print(f"当前限制(MB): {config.max_size}")
        max_size = input('修改为 -> ')
        if not max_size.isnumeric():
            error("请输入大于 100 的数字")
            return None
        if self._disk.set_max_size(int(max_size)) != LanZouCloud.SUCCESS:
            error("设置失败，限制值必需大于 100")
            return None
        config.max_size = int(max_size)

    def run(self):
        """处理一条用户命令"""
        choice_list = self._file_list.all_name + self._dir_list.all_name
        cmd_list = ['login', 'clogin', 'logout', 'ls', 'clear', 'cdrec', 'setpath', 'setsize', 'help', 'update', 'rm',
                    'cd', 'mkdir', 'upload', 'down', 'share', 'passwd', 'rename', 'mv', 'desc', 'refresh']

        set_completer(choice_list, cmd_list=cmd_list)

        try:
            args = input(self._prompt).split()
            if len(args) == 0:
                return None
        except KeyboardInterrupt:
            print('')
            info('退出本程序请输入 bye')
            return None

        cmd, arg = args[0], ' '.join(args[1:])  # 命令, 参数(可带有空格)

        no_arg_cmd = ['ls', 'login', 'clogin', 'cdrec', 'clear', 'setpath', 'setsize', 'help', 'update', 'refresh',
                      'logout']
        cmd_with_arg = ['rm', 'cd', 'mkdir', 'upload', 'down', 'share', 'passwd', 'rename', 'mv', 'desc']

        if cmd in no_arg_cmd:
            getattr(self, cmd)()
        elif cmd in cmd_with_arg:
            getattr(self, cmd)(arg)
        elif cmd == 'bye':
            exit(0)
        else:
            error('命令不存在哦，输入 help 查看帮助')
