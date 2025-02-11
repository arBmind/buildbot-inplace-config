""" Buildbot inplace config
(C) Copyright 2015-2019 HicknHack Software GmbH

The original code can be found at:
https://github.com/hicknhack-software/buildbot-inplace-config

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from ..worker import Worker
from re import sub

class WorkerCommands(dict):
    @property
    def path_delimiter(self):
        return ':'

    @property
    def directory_separator(self):
        return '/'

    @property
    def command_delimiter(self):
        return ';'

    @property
    def shell_command(self):
        return ['bash', '-c']

    @property
    def env_command(self):
        return 'env'

    @property
    def python_command(self):
        return 'python'

    @property
    def script_prefix(self):
        return '. '

    @property
    def script_suffix(self):
        return '.sh'

    @property
    def remove_command(self):
        return 'rm -rf'

    @property
    def echo_command(self):
        return 'echo'

    @property
    def append_output_to_file(self):
        return '>>'

    @property
    def output_to_file(self):
        return '>'

    @property
    def home_path_var(self):
        return '$HOME'

    def create_path_to(self, components):
        return sub(self.directory_separator + '+', self.directory_separator, self.directory_separator.join(components))


class CmdWorkerCommands(WorkerCommands):
    @property
    def path_delimiter(self):
        return ';'

    @property
    def directory_separator(self):
        return r'\\'

    @property
    def command_delimiter(self):
        return '&'

    @property
    def shell_command(self):
        return ['cmd', '/C']

    @property
    def env_command(self):
        return 'set'

    @property
    def script_prefix(self):
        return ''

    @property
    def script_suffix(self):
        return '.bat'

    @property
    def remove_command(self):
        return 'del'

    @property
    def home_path_var(self):
        return '%HOMEPATH%'


def get_worker_commands(worker_info):
    assert isinstance(worker_info, Worker)
    return CmdWorkerCommands() if worker_info.shell == 'cmd' else WorkerCommands()
