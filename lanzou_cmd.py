from lanzou.cmder.cmder import Commander
from lanzou.cmder.utils import *

if __name__ == '__main__':
    set_console_style()
    check_update()
    print_logo()
    commander = Commander()
    commander.login()

    while True:
        try:
            commander.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:  # 捕获意外发生的异常, 以便定位 bug
            raise_file = e.__traceback__.tb_frame.f_globals['__file__']
            raise_line = e.__traceback__.tb_lineno
            msg = f'File: {raise_file}[{raise_line}]\nReason: {e}'
            error(msg)
