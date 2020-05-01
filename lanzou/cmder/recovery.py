from lanzou.cmder.utils import *
from lanzou.cmder import config


class Recovery:
    """回收站命令行模式"""

    def __init__(self, disk: LanZouCloud):
        self._prompt = 'Recovery > '
        self._reader_mode = config.reader_mode
        self._disk = disk

        print("回收站数据加载中...")
        self._file_list, self._folder_list = disk.get_rec_all()

    def ls(self):
        if self._reader_mode:  # 适宜屏幕阅读器的显示方式
            for file in self._file_list:
                print(f"{file.name}  上传时间:{file.time}")
            for folder in self._folder_list:
                print(f"{folder.name}/ 创建时间:{folder.time}")
                for i, file in enumerate(folder.files, 1):
                    print(f"{i}:{file.name}  大小:{file.size}")
                print("")
        else:  # 普通用户的显示方式
            for file in self._file_list:
                print("#{0:<12}{1:<14}{2}".format(file.id, file.time, file.name))
            for folder in self._folder_list:
                print("#{0:<12}{1:<14}▣ {2}".format(folder.id, folder.time, folder.name))
                for i, file in enumerate(folder.files, 1):
                    if i == len(folder.files):
                        print("{0:<27}└─ [{1}]\t{2}".format('', file.size, file.name))
                    else:
                        print("{0:<27}├─ [{1}]\t{2}".format('', file.size, file.name))

    def clean(self):
        """清空回收站"""
        choice = input('确认清空回收站?(y) ')
        if choice.lower() == 'y':
            if self._disk.clean_rec() == LanZouCloud.SUCCESS:
                self._file_list.clear()
                self._folder_list.clear()
                info('回收站清空成功!')
            else:
                error('回收站清空失败!')

    def rm(self, name):
        """彻底删除文件(夹)"""
        if file := self._file_list.find_by_name(name):  # 删除文件
            if self._disk.delete_rec(file.id, is_file=True) == LanZouCloud.SUCCESS:
                self._file_list.pop_by_id(file.id)
            else:
                error(f'彻底删除文件失败: {name}')
        elif folder := self._folder_list.find_by_name(name):  # 删除文件夹
            if self._disk.delete_rec(folder.id, is_file=False) == LanZouCloud.SUCCESS:
                self._folder_list.pop_by_id(folder.id)
            else:
                error(f'彻底删除文件夹失败: {name}')
        else:
            error(f'文件(夹)不存在: {name}')

    def rec(self, name):
        """恢复文件"""
        if file := self._file_list.find_by_name(name):
            if self._disk.recovery(file.id, True) == LanZouCloud.SUCCESS:
                info(f"文件恢复成功: {name}")
                self._file_list.pop_by_id(file.id)
            else:
                error(f'彻底删除文件失败: {name}')
        elif folder := self._folder_list.find_by_name(name):  # 删除文件夹
            if self._disk.recovery(folder.id, is_file=False) == LanZouCloud.SUCCESS:
                info(f"文件夹恢复成功: {name}")
                self._folder_list.pop_by_id(folder.id)
            else:
                error(f'彻底删除文件夹失败: {name}')
        else:
            error('(#`O′) 没有这个文件啊喂')

    def run(self):
        """在回收站模式下运行"""
        choice_list = self._file_list.all_name + self._folder_list.all_name
        cmd_list = ['clean', 'cd', 'rec', 'rm']
        set_completer(choice_list, cmd_list=cmd_list)

        while True:
            try:
                args = input(self._prompt).split()
                if len(args) == 0:
                    continue
            except KeyboardInterrupt:
                info('已退出回收站模式')
                break

            cmd, arg = args[0], ' '.join(args[1:])

            if cmd == 'ls':
                self.ls()
            elif cmd == 'clean':
                self.clean()
            elif cmd == 'rec':
                self.rec(arg)
            elif cmd == 'rm':
                self.rm(arg)
            elif cmd == 'cd' and arg == '..':
                print('')
                info('已退出回收站模式')
                break
            else:
                info('使用 cd .. 或 Crtl + C 退出回收站')
