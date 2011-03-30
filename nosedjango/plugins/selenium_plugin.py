import os
import logging
import subprocess
import urllib2
import httplib
import time

import nose.case

from selenium.webdriver import Firefox as FirefoxWebDriver
from selenium.webdriver import Chrome as ChromeDriver
from selenium.webdriver import Remote as RemoteDriver
try:
    from selenium.webdriver.common.exceptions import (
        ErrorInResponseException,
        WebDriverException,
    )
except ImportError:
    from selenium.common.exceptions import (
        ErrorInResponseException,
        WebDriverException,
    )

from nosedjango.plugins.base_plugin import Plugin

class SeleniumPlugin(Plugin):
    name = 'selenium'

    def options(self, parser, env=None):
        if env is None:
            env = os.environ
        parser.add_option('--selenium-ss-dir',
                          help='Directory for failure screen shots.'
                          )
        parser.add_option('--headless',
                          help="Run the Selenium tests in a headless mode, with virtual frames starting with the given index (eg. 1)",
                          default=None)
        parser.add_option('--driver-type',
                          help='The type of driver that needs to be created',
                          default='firefox')
        parser.add_option('--remote-server-address',
                          help='Use a remote server to run the tests, must pass in the server address',
                          default='localhost')
        parser.add_option('--selenium-port',
                          help='The port for the selenium server',
                          default='4444')
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        if options.selenium_ss_dir:
            self.ss_dir = os.path.abspath(options.selenium_ss_dir)
        else:
            self.ss_dir = os.path.abspath('failure_screenshots')
        valid_browsers = ['firefox', 'internet_explorer', 'chrome']
        if options.driver_type not in valid_browsers:
            raise RuntimeError('--driver-type must be one of: %s' % ' '.join(valid_browsers))
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
        Plugin.configure(self, options, config)

    def get_driver(self):
        # Lazilly gets the driver one time cant call in begin since ssh tunnel
        # may not be created
        if self._driver:
            return self._driver

        if self._driver_type == 'firefox':
            self._driver = FirefoxWebDriver()
        elif self._driver_type == 'chrome':
            self._driver = ChromeDriver()
        else:
            timeout = 60
            step = 1
            current = 0
            while current < timeout:
                try:
                    self._driver = RemoteDriver(
                        'http://%s:%s/wd/hub' % (self._remote_server_address, self._selenium_port),
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

        # Set the logging level to INFO
        return self._driver


    def finalize(self, result):
        driver = self.get_driver()
        if driver:
            self.get_driver().quit()

        if self.xvfb_process:
            os.kill(self.xvfb_process.pid, 9)
            os.waitpid(self.xvfb_process.pid, 0)

    def begin(self):
        self.xvfb_process = None
        if self.run_headless:
            xvfb_display = self.x_display
            try:
                self.xvfb_process = subprocess.Popen(['xvfb', ':%s' % xvfb_display, '-ac', '-screen', '0', '1024x768x24'], stderr=subprocess.PIPE)
            except OSError:
                # Newer distros use Xvfb
                self.xvfb_process = subprocess.Popen(['Xvfb', ':%s' % xvfb_display, '-ac', '-screen', '0', '1024x768x24'], stderr=subprocess.PIPE)
            os.environ['DISPLAY'] = ':%s' % xvfb_display

    def beforeTest(self, test):
        driver = self.get_driver()
        logging.getLogger().setLevel(logging.INFO)
        setattr(test.test, 'driver', driver)
        # need to know the main window handle for cleaning up extra windows at
        # the end of each test
        if driver:
            self._current_windows_handle = driver.get_current_window_handle()

    def afterTest(self, test):
        driver = getattr(test.test, 'driver', False)
        if not driver:
            return
        if self._current_windows_handle:
            # close all extra windows except for the main window
            for window in driver.get_window_handles():
                if window != self._current_windows_handle:
                    driver.switch_to_window(window)
                    driver.close()
                    driver.switch_to_window(self._current_windows_handle)
        # deal with the onbeforeunload if it is there until selenium has a
        # way to do so in the api
        try:
            driver.execute_script('window.onbeforeunload = function(){};')
        except (ErrorInResponseException, AssertionError):
            pass
        except WebDriverException:
            driver.quit()
            self._driver = None


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

