import os.path
import shutil

from nosedjango.plugins.base_plugin import Plugin


class FileStoragePlugin(Plugin):
    """
    Set up a test file system so you're writing to a specific directory for
    your testing.
    """
    name = 'django-testfs'

    def beforeTestSetup(self, settings, setup_test_environment, connection):
        """
        Create a unique directory for media for use during testing. We want a
        unique directory because we empty the dir after every test to guard
        against side effects. This also allows the use of multiprocess for
        testing without worrying about different processes interacting via
        the storage system.
        """
        settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'  # noqa
        from django.core.files.storage import default_storage

        token = self.get_unique_token()

        default_storage.location = os.path.join(
            settings.MEDIA_ROOT,
            "_nj/%s" % token)
        default_storage.base_url = os.path.join(
            settings.MEDIA_URL,
            '_nj/%s/' % token)

    def afterRollback(self, settings):
        """
        After every test, we want to empty the media directory so that media
        left over from one test doesn't affect a later test.
        """
        self.clear_test_media()

    def clear_test_media(self):
        from django.core.files.storage import default_storage
        try:
            shutil.rmtree(default_storage.location)
        except OSError:
            # If nothing was added to storage, this directory will be empty
            # and will error out
            pass
