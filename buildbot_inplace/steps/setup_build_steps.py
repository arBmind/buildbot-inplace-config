""" Buildbot inplace config
(C) Copyright 2015-2017 HicknHack Software GmbH

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
from buildbot.process.buildstep import LoggingBuildStep, SUCCESS
from buildbot.steps.shell import ShellCommand
from buildbot.steps.shellsequence import ShellSequence
from buildbot.steps.transfer import FileUpload
from twisted.internet import defer

from .setup import SetupStep
from .configured_step_mixin import ConfiguredStepMixin


class SetupBuildSteps(LoggingBuildStep, ConfiguredStepMixin):
    """A Composite Step that dynamically adds profile steps to run profile setups and build command steps."""

    def __init__(self, config, *args, **kwargs):
        self.global_config = config
        super(SetupBuildSteps, self).__init__(*args, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        inplace_config = yield self.get_inplace_config()
        profile = inplace_config.profile_named_get(self.build.properties['inplace_profile'])
        env = {}

        for setup in profile.setups:
            desc = "Preparing %s" % setup
            prepare_dict = dict(name=desc, description=desc, descriptionDone=desc)
            self._add_step(SetupStep(setup, config=self.global_config, env=env, **prepare_dict))

        profile_commands = inplace_config.profile_commands(profile)
        for pc in profile_commands:
            shell_dict = dict(name=pc.name, description=pc.name, descriptionDone=pc.name)
            if len(pc.commands) == 1:
                self._add_step(ShellCommand(command=pc.commands[0], env=env, **shell_dict))
            else:
                self._add_step(ShellSequence(pc.commands, env=env, **shell_dict))
            if pc.product:
                self._add_step(FileUpload(name='Upload ' + pc.product, workersrc=pc.product, masterdest=pc.product, **upload_dict))
        defer.returnValue(SUCCESS)

    def start(self):
        raise NotImplementedError("Use run()")

    def _add_step(self, step):
        build = self.build
        step.setBuild(build)
        step.setWorker(build.workerforbuilder.worker)
        build.steps.append(step)
