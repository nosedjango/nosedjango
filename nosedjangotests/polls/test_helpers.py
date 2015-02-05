import os

from django.conf import settings
from django.test.testcases import TestCase
from django.test.client import Client


class PolicyStatFixturesMixin(object):
    def set_initial_fixtures(self):
        self.fixtures = getattr(self, 'fixtures', [])

    def __init__(self, *args, **kwargs):
        self.set_initial_fixtures()
        super(PolicyStatFixturesMixin, self).__init__(*args, **kwargs)


class PolicyStatTestingUtilsMixin(object):
    pass


class TenantTestClientMixin(object):
    use_sphinx_patch = True
    enforce_csrf_checks = False
    enable_secure_request = False

    def setUp(self):
        self.client = TenantTestClient(
            REMOTE_ADDR='localhost',
            use_sphinx_patch=self.use_sphinx_patch,
            enforce_csrf_checks=self.enforce_csrf_checks,
            enable_secure_request=self.enable_secure_request,
        )
        super(TenantTestClientMixin, self).setUp()
        if self.enable_secure_request:
            # This forces request.is_secure() to return True for
            # RequestFactories only
            os.environ['HTTPS'] = 'on'


class TenantTestClient(Client):
    def __init__(
        self,
        use_sphinx_patch=True,
        enable_secure_request=False,
        *args,
        **kwargs
    ):
        super(TenantTestClient, self).__init__(*args, **kwargs)
        self.use_sphinx_patch = use_sphinx_patch
        self._subdomain = ''
        self.enable_secure_request = enable_secure_request


class SiteDomainOverrideMixin(object):
    def setUp(self):
        settings.SITE_DOMAIN = 'testserver'
        super(SiteDomainOverrideMixin, self).setUp()


class FactoryClientMixin(
    SiteDomainOverrideMixin,
    TenantTestClientMixin,
    PolicyStatTestingUtilsMixin,
):
    create_site_admin = True
    create_superuser = False
    auto_login_as_site_admin = True
    auto_login_as_superuser = False

    def setUpClient(self):
        pass

    def setUp(self):
        super(FactoryClientMixin, self).setUp()


class AssertHelpersMixin(object):
    pass


class BaseTestMixin(AssertHelpersMixin):
    patches = {}
    feature_switches = {}
    switches = {}

    def setUp(self):
        super(BaseTestMixin, self).setUp()

    def tearDown(self):
        super(BaseTestMixin, self).tearDown()


class BaseTestCase(BaseTestMixin, TestCase):
    pass


class ClientTestCase(
    PolicyStatFixturesMixin,
    PolicyStatTestingUtilsMixin,
    TenantTestClientMixin,
    SiteDomainOverrideMixin,
    BaseTestCase,
):
    pass


class FactoryClientTestCase(FactoryClientMixin, BaseTestCase):
    pass
