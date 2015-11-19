import os.path

from nosedjango.plugins.base_plugin import Plugin

CONFIG_FILES = [
    # Linux users will prefer this
    "~/.djangosettingstargetrc",
    # Windows users will prefer this
    "~/.djangosettingstarget.cfg",
]


class SettingsTargetPlugin(Plugin):
    """
    Switch Django settings values based on a settings ``target`` input. Allows
    for the creation of different groups of settings that can be triggered
    based on different target values.

    For example, you might optionally use Amazon S3 as a file storage backend.
    Most of the time, you wouldn't want to actually use S3 when running unit
    tests, but sometimes you do want to actually test that integration. You
    would set up one target with actual S3 backend settings while using the
    DEFAULT target to blank them out.
    """
    name = 'django-settings-target'

    def options(self, parser, env):
        parser.add_option(
            '--django-settings-target-conf',
            help='Path to your settings target configuration file',
            default=None,
        )
        parser.add_option(
            '--django-settings-target',
            help='Named settings group or "target" to use for testing.',
            default=None,
        )
        super(SettingsTargetPlugin, self).options(parser, env)

    def get_config_files(self):
        return filter(os.path.exists,
                      map(os.path.expanduser, CONFIG_FILES))
