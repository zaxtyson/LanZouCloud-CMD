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
        except Exception as e:
            error(e)
