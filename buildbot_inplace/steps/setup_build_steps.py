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
from buildbot.process.buildstep import BuildStep, ShellMixin, SUCCESS
from buildbot.process.properties import Property
from buildbot.steps.shell import ShellCommand, SetPropertyFromCommand
from buildbot.steps.shellsequence import ShellSequence
from buildbot.steps.transfer import MultipleFileUpload
from buildbot.util import flatten
from twisted.internet import defer

from .configured_step_mixin import ConfiguredStepMixin
from .setup import SetupStep
from .redmine_upload import RedmineUpload
from .github_upload import GithubUpload


def glob2list(rc, stdout, stderr):
    """Converts a string to a list of lines"""
    product_files = [l.strip() for l in stdout.split('\n') if l.strip()]
    return {'product_files': product_files}


class SetupBuildSteps(ShellMixin, BuildStep, ConfiguredStepMixin):
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
                self._add_step(ShellCommand(command=pc.commands[0], env=env, haltOnFailure=True, **shell_dict))
            else:
                self._add_step(ShellSequence(pc.commands, env=env, haltOnFailure=True, **shell_dict))

            masterdest = 'products/' + self.build.properties['inplace_project']
            project = self.global_config.projects.named_get(self.build.properties['inplace_project'])

            redmine = pc.redmine_deploy
            github = pc.github_deploy

            if pc.products and (redmine or github):
                self._add_step(MultipleFileUpload(name='Upload products \'' + ', '.join(flatten([pc.products])) + '\'',
                                                  workersrcs=pc.products,
                                                  masterdest=masterdest))

                if redmine:
                    self._add_step(RedmineUpload(
                        name='Upload products to Redmine',
                        project=project,
                        products=pc.products,
                        product_dir=masterdest,
                        deploy_config=redmine
                    ))

                if github:
                    self._add_step(GithubUpload(
                        name='Upload products to Github',
                        project=project,
                        products=pc.products,
                        product_dir=masterdest,
                        deploy_config=github
                    ))

            if pc.products_command and (redmine or github):
                self._add_step(SetPropertyFromCommand(
                    name='Set property from command \'' + pc.products_command + '\'',
                    command=pc.products_command,
                    extract_fn=glob2list,
                    haltOnFailure=True))
                self._add_step(MultipleFileUpload(
                    name='Upload products from command \'' + pc.products_command + '\'',
                    workersrcs=Property('product_files'),
                    masterdest=masterdest))

                if redmine:
                    self._add_step(RedmineUpload(
                        name='Upload products to Redmine',
                        project=project,
                        products=Property('product_files'),
                        product_dir=masterdest,
                        deploy_config=redmine,
                    ))

                if github:
                    self._add_step(GithubUpload(
                        name='Upload products to Github',
                        project=project,
                        products=Property('product_files'),
                        product_dir=masterdest,
                        deploy_config=github,
                    ))

        defer.returnValue(SUCCESS)

    def start(self):
        raise NotImplementedError("Use run()")

    def _add_step(self, step):
        build = self.build
        step.setBuild(build)
        step.setWorker(build.workerforbuilder.worker)
        build.steps.append(step)
