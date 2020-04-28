import gdb


class QuitCommand(gdb.Command):

    _quit_tpl = 'quit {code}'.format
    _error = '128+$_siginfo.si_signo'
    _code = '$_exitcode'

    def __init__(self):
        super().__init__('quit_command', gdb.COMMAND_NONE)

    def invoke(self, _, from_tty):
        sig_info = gdb.parse_and_eval('$_siginfo')
        code = self._code if sig_info.type.name == 'void' else self._error
        gdb.execute(self._quit_tpl(code=code), from_tty=from_tty)


class InitCommand(gdb.Command):

    _init_commands = (
        'handle SIG38 nostop noprint pass',
        'set breakpoint pending on',
        'set confirm off',
        'set prompt',
        'maint set internal-error quit yes',
        'maint set internal-error corefile no',
        'set backtrace limit 25',
        'set print elements 10',
        'set python print-stack full',
        'set trace-commands on',
        'set overload-resolution off',
    )

    def __init__(self):
        super().__init__('init_command', gdb.COMMAND_NONE)

    def invoke(self, _, from_tty):
        for command in self._init_commands:
            gdb.execute(command, from_tty=from_tty)


InitCommand()
QuitCommand()


# '-ex', 'print $_siginfo',
# '-ex', 'info locals',
# '-ex', 'info registers',
# '-ex', 'backtrace full',
# '-ex', 'disassemble',
# '-ex', 'symbol-file',
# '-ex', 'sharedlibrary',
# '-ex', 'info proc mappings',
# '-ex', 'info threads',
# '-ex', 'shared',
# '-ex', 'info sharedlibrary',
# gdb.execute('info sharedlibrary', from_tty=from_tty, to_string=True)
# gdb.execute('info registers', from_tty=from_tty, to_string=True)
