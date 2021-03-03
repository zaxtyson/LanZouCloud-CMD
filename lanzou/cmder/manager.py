from lanzou.cmder.downloader import TaskType
from lanzou.cmder.utils import info, error

__all__ = ['global_task_mgr']


class TaskManager(object):
    """下载/上传任务管理器"""

    def __init__(self):
        self._tasks = []

    def is_empty(self):
        """任务列表是否为空"""
        return len(self._tasks) == 0

    def has_alive_task(self):
        """是否有任务在后台运行"""
        for task in self._tasks:
            if task.is_alive():
                return True
        return False

    def add_task(self, task):
        """提交一个上传/下载任务"""
        for t in self._tasks:
            if task.get_cmd_info() == t.get_cmd_info():  # 操作指令相同,认为是相同的任务
                old_pid = t.get_task_id()
                if t.is_alive():  # 下载任务正在运行
                    info(f"任务正在后台运行: PID {old_pid}")
                    return None
                else:  # 下载任务为 Finished 或 Error 状态
                    choice = input(f"任务已完成, PID {old_pid}, 重试?(y)")
                    if choice.lower() == 'y':
                        task.set_task_id(old_pid)
                        self._tasks[old_pid] = task
                        task.start()
                return None
        # 没有发现重复的任务
        task.set_task_id(len(self._tasks))
        self._tasks.append(task)
        task.start()

    @staticmethod
    def _get_task_status(task):
        now_size, total_size = task.get_process()
        percent = now_size / total_size * 100
        has_error = len(task.get_err_msg()) != 0
        if task.is_alive():  # 任务执行中
            status = '\033[1;32m运行中\033[0m'
        elif not task.is_alive() and has_error:  # 任务执行完成, 但是有错误信息
            status = '\033[1;31m出错  \033[0m'
        else:  # 任务正常执行完成
            status = '\033[1;34m已完成\033[0m'
        return percent, status

    def show_tasks(self):
        if self.is_empty():
            print(f"没有任务在后台运行哦")
            return

        print('-' * 100)
        for pid, task in enumerate(self._tasks):
            percent, status = self._get_task_status(task)
            if task.get_task_type() == TaskType.DOWNLOAD:
                d_arg, f_name = task.get_cmd_info()
                d_arg = f_name if type(d_arg) == int else d_arg  # 显示 id 对应的文件名
                print(f"ID: {pid} | 状态: {status} | 进度: {percent:6.2f}% | 下载: {d_arg}")
            else:
                up_path, folder_name = task.get_cmd_info()
                print(f"ID: {pid} | 状态: {status} | 进度: {percent:6.2f}% | 上传: {up_path} -> {folder_name}")
        print('-' * 100)

    def show_detail(self, pid=-1):
        """显示任务详情"""
        if pid < 0 or pid >= len(self._tasks):
            error(f"进程号不存在: PID {pid}")
            return

        task = self._tasks[pid]
        percent, status = self._get_task_status(task)
        print('-' * 60)
        print(f"进程ID号: {pid}")
        print(f"任务状态: {status}")
        print(f"任务类型: {'下载' if task.get_task_type() == TaskType.DOWNLOAD else '上传'}")
        print(f"任务进度: {percent:.2f}%")
        print("错误信息:")
        if not task.get_err_msg():
            print("\t没有错误, 一切正常 :)")
            print('-' * 60)
            return
        # 显示出错信息
        for msg in task.get_err_msg():
            print("\t" + msg)
        print('-' * 60)


# 全局任务管理器对象
global_task_mgr = TaskManager()
