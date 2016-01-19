import os
import logging
import subprocess
import urllib2
import httplib
import time
from pprint import pprint

import nose.case

from nosedjango.plugins.base_plugin import Plugin


class SeleniumPlugin(Plugin):
    name = 'selenium'

    def options(self, parser, env=None):
        if env is None:
            env = os.environ
        parser.add_option(
            '--selenium-ss-dir',
            help='Directory for failure screen shots.'
        )
        parser.add_option(
            '--headless',
            help=(
                "Run the Selenium tests in a headless mode, with virtual "
                "frames starting with the given index (eg. 1)"
            ),
            default=None,
        )
        parser.add_option(
            '--driver-type',
            help='The type of driver that needs to be created',
            default='firefox',
        )
        parser.add_option(
            '--firefox-binary',
            help='the path to the firefox browser binary',
            default=None,
        )
        parser.add_option(
            '--remote-server-address',
            help='Use a remote server to run the tests, must pass in the server address',  # noqa
            default='localhost',
        )
        parser.add_option(
            '--selenium-port',
            help='The port for the selenium server',
            default='4444',
        )
        parser.add_option(
            '--track-stats',
            help=(
                'After the suite is run print a table of test '
                'name/runtime/number of trips to the server.  defaults to '
                'ordering by trips to the server'
            ),
            default=None,
        )
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        if options.selenium_ss_dir:
            self.ss_dir = os.path.abspath(options.selenium_ss_dir)
        else:
            self.ss_dir = os.path.abspath('failure_screenshots')
        valid_browsers = ['firefox', 'internet_explorer', 'chrome']
        if options.driver_type not in valid_browsers:
            raise RuntimeError(
                '--driver-type must be one of: %s' % ' '.join(valid_browsers)
            )
        self._firefox_binary = options.firefox_binary
        self._driver_type = options.driver_type.replace('_', ' ')
        self._remote_server_address = options.remote_server_address
        self._selenium_port = options.selenium_port
        self._driver = None
        self._current_windows_handle = None

        self.x_display = 1
        self.run_headless = False
        if options.headless:
            self.run_headless = True
            self.x_display = int(options.headless)
        if options.track_stats and options.track_stats not in ('trips', 'runtime'):  # noqa
            raise RuntimeError('--track-stats must be "trips" or "runtime"')
        self._track_stats = options.track_stats
        Plugin.configure(self, options, config)

    def get_driver(self):
        from selenium.webdriver import Firefox as FirefoxWebDriver
        from selenium.webdriver import Chrome as ChromeDriver
        from selenium.webdriver import Remote as RemoteDriver

        # Lazilly gets the driver one time cant call in begin since ssh tunnel
        # may not be created
        if self._driver:
            return self._driver

        if self._driver_type == 'firefox':
            if self._firefox_binary is None:
                self._driver = FirefoxWebDriver()
            else:
                from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
                binary = FirefoxBinary(self._firefox_binary)
                self._driver = FirefoxWebDriver(firefox_binary=binary)
        elif self._driver_type == 'chrome':
            self._driver = ChromeDriver()
        else:
            timeout = 60
            step = 1
            current = 0
            while current < timeout:
                try:
                    self._driver = RemoteDriver(
                        'http://%s:%s/wd/hub' % (
                            self._remote_server_address,
                            self._selenium_port,
                        ),
                        self._driver_type,
                        'WINDOWS',
                    )
                    break
                except urllib2.URLError:
                    time.sleep(step)
                    current += step
                except httplib.BadStatusLine:
                    self._driver = None
                    break
            if current >= timeout:
                raise urllib2.URLError('timeout')

        monkey_patch_methods(self._driver)
        return self._driver

    def finalize(self, result):
        if self._track_stats and self.times:
            print '-' * 80
            if self._track_stats == 'runtime':
                order = 1
            elif self._track_stats == 'trips':
                order = 2
            pprint(sorted(self.times, key=lambda x: x[order]))
            print '-' * 80
        driver = self.get_driver()
        if driver:
            driver.quit()

        if self.xvfb_process:
            os.kill(self.xvfb_process.pid, 9)
            os.waitpid(self.xvfb_process.pid, 0)

    def begin(self):
        self.xvfb_process = None
        if self.run_headless:
            xvfb_display = self.x_display
            try:
                self.xvfb_process = subprocess.Popen(
                    [
                        'xvfb',
                        ':%s' % xvfb_display,
                        '-ac',
                        '-screen',
                        '0',
                        '1024x768x24',
                    ],
                    stderr=subprocess.PIPE,
                )
            except OSError:
                # Newer distros use Xvfb
                self.xvfb_process = subprocess.Popen(
                    [
                        'Xvfb',
                        ':%s' % xvfb_display,
                        '-ac',
                        '-screen',
                        '0',
                        '1024x768x24',
                    ],
                    stderr=subprocess.PIPE,
                )
            os.environ['DISPLAY'] = ':%s' % xvfb_display

    def beforeTest(self, test):
        self.start_time = time.time()
        driver = self.get_driver()
        logging.getLogger().setLevel(logging.INFO)
        setattr(test.test, 'driver', driver)
        # need to know the main window handle for cleaning up extra windows at
        # the end of each test
        if driver:
            self._current_windows_handle = driver.current_window_handle

    def afterTest(self, test):
        if not hasattr(self, 'times'):
            self.times = []
        if self.times and self._driver:
            self.times.append((
                test.address()[2],
                int(time.time() - self.start_time),
                self._driver.roundtrip_counter
            ))
            self._driver.roundtrip_counter = 0
        driver = getattr(test.test, 'driver', False)
        if not driver:
            return
        if self._current_windows_handle:
            # close all extra windows except for the main window
            for window in driver.window_handles:
                if window != self._current_windows_handle:
                    driver.switch_to_window(window)
                    driver.close()
                    driver.switch_to_window(self._current_windows_handle)

    def handleError(self, test, err):
        if isinstance(test, nose.case.Test) and \
           getattr(test.context, 'selenium_take_ss', False):
            self._take_screenshot(test)

    def handleFailure(self, test, err):
        if isinstance(test, nose.case.Test) and \
           getattr(test.context, 'selenium_take_ss', False):
            self._take_screenshot(test)

    def _take_screenshot(self, test):
        driver_attr = getattr(test.context, 'selenium_driver_attr', 'driver')
        try:
            driver = getattr(test.test, driver_attr)
        except AttributeError:
            print "Error attempting to take failure screenshot"
            return

        # Make the failure ss directory if it doesn't exist
        if not os.path.exists(self.ss_dir):
            os.makedirs(self.ss_dir)

        ss_file = os.path.join(self.ss_dir, '%s.png' % test.id())

        # The Remote server does not have the attribute ``save_screenshot``, so
        # we have to check to see if it is there before using it
        if hasattr(driver, 'save_screenshot'):
            driver.save_screenshot(ss_file)


def monkey_patch_methods(driver):
    # Keep track of how many trips to execute are made
    old_execute = driver.__class__.execute

    def new_execute(self, *args, **kwargs):
        roundtrip_counter = getattr(driver, 'roundtrip_counter', 0)
        driver.roundtrip_counter = roundtrip_counter + 1
        return old_execute(self, *args, **kwargs)
    driver.__class__.execute = new_execute

    # If there is an alert when trying to get a page, accept it
    old_get = driver.__class__.get

    def new_get(self, *args, **kwargs):
        old_get(self, *args, **kwargs)
        accept_alert(driver)
    driver.__class__.get = new_get

    # Need to move away from the page to ensure if there is an alert on the
    # page it gets dealt with prior to closing the window
    old_close = driver.__class__.close

    def new_close(self, *args, **kwargs):
        self.get('http://www.google.com')  # Random page to ensure page is changed
        old_close(self, *args, **kwargs)
    driver.__class__.close = new_close

    old_quit = driver.__class__.quit

    def new_quit(self, *args, **kwargs):
        self.close()  # Need to handle onbeforeunload alerts
        old_quit(self, *args, **kwargs)
    driver.__class__.quit = new_quit


def accept_alert(driver):
    from selenium.common.exceptions import WebDriverException

    alert = driver.switch_to_alert()
    try:
        alert.accept()
    except WebDriverException:
        pass
