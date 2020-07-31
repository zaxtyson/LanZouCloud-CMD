from sys import exit as exit_cmd
from webbrowser import open_new_tab
from time import strftime, localtime
import csv
from lanzou.api.models import FileList, FolderList
from lanzou.api.types import *
from lanzou.cmder import config
from lanzou.cmder.downloader import Downloader, Uploader
from lanzou.cmder.manager import global_task_mgr
from lanzou.cmder.recovery import Recovery
from lanzou.cmder.utils import *


class Commander:
    """蓝奏网盘命令行"""

    def __init__(self):
        self._prompt = '> '
        self._disk = LanZouCloud()
        self._disk.ignore_limits()
        self._task_mgr = global_task_mgr
        self._dir_list = FolderList()
        self._file_list = FileList()
        self._path_list = FolderList()
        self._parent_id = -1
        self._parent_name = ''
        self._work_name = ''
        self._work_id = -1
        self._last_work_id = -1
        self._reader_mode = config.reader_mode
        self._default_dir_pwd = config.default_dir_pwd
        self._disk.set_max_size(config.max_size)
        self._disk.set_upload_delay(config.upload_delay)

    @staticmethod
    def clear():
        clear_screen()

    @staticmethod
    def help():
        print_help()

    @staticmethod
    def update():
        check_update()

    def bye(self):
        if self._task_mgr.has_alive_task():
            info(f"有任务在后台运行, 退出请直接关闭窗口")
        else:
            exit_cmd(0)

    def rmode(self):
        """适用于屏幕阅读器用户的显示方式"""
        choice = input("以适宜屏幕阅读器的方式显示(y): ")
        if choice and choice.lower() == 'y':
            config.reader_mode = True
            self._reader_mode = True
            info("已启用 Reader Mode")
        else:
            config.reader_mode = False
            self._reader_mode = False
            info("已关闭 Reader Mode")

    def cdrec(self):
        """进入回收站模式"""
        rec = Recovery(self._disk)
        rec.run()
        self.refresh()

    def xghost(self):
        """扫描并删除幽灵文件夹"""
        choice = input("需要清理幽灵文件夹吗(y): ")
        if choice and choice.lower() == 'y':
            self._disk.clean_ghost_folders()
            info("清理已完成")
        else:
            info("清理操作已取消")

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
        """使用 cookie 登录"""
        if not config.cookie or self._disk.login_by_cookie(config.cookie) != LanZouCloud.SUCCESS:
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
            else:
                error("登录失败,请检查 Cookie 是否正确")
        self.refresh()

    def logout(self):
        """注销"""
        clear_screen()
        self._prompt = '> '
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
        if self._reader_mode:  # 方便屏幕阅读器阅读
            for folder in self._dir_list:
                pwd_str = '有提取码' if folder.has_pwd else ''
                print(f"{folder.name}/  {folder.desc}  {pwd_str}")
            for file in self._file_list:
                pwd_str = '有提取码' if file.has_pwd else ''
                print(f"{file.name}  大小:{file.size}  上传时间:{file.time}  下载次数:{file.downs}  {pwd_str}")
        else:  # 普通用户显示方式
            for folder in self._dir_list:
                pwd_str = '✦' if folder.has_pwd else '✧'
                print("#{0:<12}{1:<4}{2}{3}/".format(
                    folder.id, pwd_str, text_align(folder.desc, 28), folder.name))
            for file in self._file_list:
                pwd_str = '✦' if file.has_pwd else '✧'
                print("#{0:<12}{1:<4}{2:<12}{3:>8}{4:>6}  {5}".format(
                    file.id, pwd_str, file.time, file.size, file.downs, file.name))

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

    def mkdir(self, name):
        """创建文件夹"""
        if self._dir_list.find_by_name(name):
            error(f'文件夹已存在: {name}')
            return None

        dir_id = self._disk.mkdir(self._work_id, name, '')
        if dir_id == LanZouCloud.MKDIR_ERROR:
            error(f'创建文件夹失败(深度最大 4 级)')
            return None
        # 创建成功，添加到文件夹列表，减少向服务器请求次数
        self._disk.set_passwd(dir_id, self._default_dir_pwd, is_file=False)
        self._dir_list.append(Folder(name, dir_id, bool(self._default_dir_pwd), ''))

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

    def down(self, arg):
        """自动选择下载方式"""
        downloader = Downloader(self._disk)
        if arg.startswith('http'):
            downloader.set_url(arg)
        elif file := self._file_list.find_by_name(arg):  # 如果是文件
            path = '/'.join(self._path_list.all_name) + '/' + arg  # 文件在网盘的绝对路径
            downloader.set_fid(file.id, is_file=True, f_path=path)
        elif folder := self._dir_list.find_by_name(arg):  # 如果是文件夹
            path = '/'.join(self._path_list.all_name) + '/' + arg + '/'  # 文件夹绝对路径, 加 '/' 以便区分
            downloader.set_fid(folder.id, is_file=False, f_path=path)
        else:
            error(f'文件(夹)不存在: {arg}')
            return None
        # 提交下载任务
        info("下载任务已提交, 使用 jobs 命令查看进度")
        self._task_mgr.add_task(downloader)

    def jobs(self, arg):
        """显示后台任务列表"""
        if arg.isnumeric():
            self._task_mgr.show_detail(int(arg))
        else:
            self._task_mgr.show_tasks()

    def upload(self, path):
        """上传文件(夹)"""
        path = path.strip('\"\' ')  # 去除直接拖文件到窗口产生的引号
        if not os.path.exists(path):
            error(f'该路径不存在哦: {path}')
            return None
        uploader = Uploader(self._disk)
        if os.path.isfile(path):
            uploader.set_upload_path(path, is_file=True)
        else:
            uploader.set_upload_path(path, is_file=False)
        uploader.set_target(self._work_id, self._work_name)
        info("上传任务已提交, 使用 jobs 命令查看进度")
        self._task_mgr.add_task(uploader)

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
            inf = self._disk.get_share_info(folder.id, is_file=False)
            if inf.code != LanZouCloud.SUCCESS:
                print('ERROR : 获取文件夹信息出错')
                return None

            print("-" * 50)
            print(f"文件夹名 : {name}")
            print(f"提取码   : {inf.pwd or '无'}")
            print(f"分享链接 : {inf.url}")
            print(f"描述信息 : {inf.desc or '无'}")
            print("-" * 50)
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

    def export(self, name):
        """文件链接信息导出到文件"""
        if folder := self._dir_list.find_by_name(name):
            if not os.path.exists(config.save_path):
                os.makedirs(config.save_path)
            csv_path = config.save_path + os.sep + strftime("%Y-%m-%d_%H-%M-%S", localtime()) + '.csv'
            print(f"正在导出 {name} 下的文件信息, 请稍等...")
            folder_info = self._disk.get_folder_info_by_id(folder.id)
            with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                for file in folder_info.files:
                    writer.writerow([file.name, file.time, file.size, file.url])

            info(f"信息已导出至文件: {csv_path}")
        else:
            error(f'文件夹不存在: {name}')

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

    def setdelay(self):
        """设置大文件上传延时"""
        print("大文件数据块上传延时范围(秒), 如: 0 60")
        print(f"当前配置: {config.upload_delay}")
        tr = input("请输入延时范围: ").split()
        if len(tr) != 2:
            error("格式有误!")
            return None
        tr = (int(tr[0]), int(tr[1]))
        self._disk.set_upload_delay(tr)
        config.upload_delay = tr

    def setpasswd(self):
        """设置文件(夹)默认上传密码"""
        print("关闭提取码请输入 off")
        print(f"当前配置: 文件: {config.default_file_pwd or '无'}, 文件夹: {config.default_dir_pwd or '无'}")
        file_pwd = input("设置文件默认提取码(2-6位): ")
        if 2 <= len(file_pwd) <= 6:
            config.default_file_pwd = '' if file_pwd == 'off' else file_pwd
        dir_pwd = input("设置文件夹默认提取码(2-12位): ")
        if 2 <= len(dir_pwd) <= 12:
            config.default_dir_pwd = '' if dir_pwd == 'off' else dir_pwd
        info(f"修改成功: 文件: {config.default_file_pwd or '无'}, 文件夹: {config.default_dir_pwd or '无'}, 配置将在下次启动时生效")

    def run(self):
        """处理一条用户命令"""
        no_arg_cmd = ['bye', 'cdrec', 'clear', 'help', 'login', 'logout', 'ls', 'refresh', 'rmode', 'setpath',
                      'setsize', 'update', 'xghost', 'setdelay', 'setpasswd']
        cmd_with_arg = ['cd', 'desc', 'down', 'jobs', 'mkdir', 'mv', 'passwd', 'rename', 'rm', 'share', 'upload', 'export']

        choice_list = self._file_list.all_name + self._dir_list.all_name
        cmd_list = no_arg_cmd + cmd_with_arg
        set_completer(choice_list, cmd_list=cmd_list)

        try:
            args = input(self._prompt).split(' ', 1)
            if len(args) == 0:
                return None
        except KeyboardInterrupt:
            print('')
            info('退出本程序请输入 bye')
            return None

        cmd, arg = (args[0], '') if len(args) == 1 else (args[0], args[1])  # 命令, 参数(可带有空格, 没有参数就设为空)

        if cmd in no_arg_cmd:
            getattr(self, cmd)()
        elif cmd in cmd_with_arg:
            getattr(self, cmd)(arg)
