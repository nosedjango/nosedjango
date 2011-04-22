import math
import random
import string

from nose.plugins.base import Plugin as NosePlugin

class Plugin(NosePlugin):
    django_plugin = True
    _unique_token = None

    def get_unique_token(self):
        """
        Get a unique token for usage in differentiating test runs that need to
        run in parallel.
        """
        if self._unique_token == None:
            self._unique_token = self._random_token()

        return self._unique_token

    def _random_token(self, bits=128):
        """
        Generates a random token, using the url-safe base64 alphabet.
        The "bits" argument specifies the bits of randomness to use.
        """
        alphabet = string.ascii_letters + string.digits + '-_'
        # alphabet length is 64, so each letter provides lg(64) = 6 bits
        num_letters = int(math.ceil(bits / 6.0))
        return ''.join(random.choice(alphabet) for i in range(num_letters))

class IPluginInterface(object):
    """
    IPluginInteface describes the NoseDjango plugin API. Do not subclass or use
    this class directly. This interface describes an API **in addition** to
    the API described with ``nose.plugins.base.IPluginInterface``.
    """
    def __new__(cls, *arg, **kw):
        raise TypeError("IPluginInterface class is for documentation only")

    def beforeConnectionSetup(self, settings):
        pass

    def beforeTestSetup(self, settings, setup_test_environment, connection):
        pass

    def afterTestSetup(self, settings):
        pass

    def beforeTestDb(self, settings, connection, management):
        pass

    def afterTestDb(self, settings, connection):
        pass

    def beforeTransactionManagement(self, settings, test):
        pass

    def afterTransactionManagement(self, settings, test):
        pass

    def beforeFixtureLoad(self, settings, test):
        pass

    def afterFixtureLoad(self, settings, test):
        pass

    def beforeUrlConfLoad(self, settings, test):
        pass

    def afterUrlConfLoad(self, settings, test):
        pass

    def beforeDestroyTestDb(self, settings, connection):
        pass

    def afterDestroyTestDb(self, settings, connection):
        pass

    def beforeTeardownTestEnv(self, settings, teardown_test_environment):
        pass

    def afterTeardownTestEnv(self, settings):
        pass
