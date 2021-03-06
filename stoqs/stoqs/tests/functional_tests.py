#!/usr/bin/env python

__author__ = "Mike McCann"
__copyright__ = "Copyright 2011, MBARI"
__credits__ = ["Chander Ganesan, Open Technology Group"]
__license__ = "GPL"
__version__ = "$Revision: 12276 $".split()[1]
__maintainer__ = "Mike McCann"
__email__ = "mccann at mbari.org"
__status__ = "Development"
__doc__ = '''

Functional tests for the stoqs application

Mike McCann

@undocumented: __doc__ parser
@author: __author__
@status: __status__
@license: __license__
'''

from django.test import TestCase
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import logging

logger = logging.getLogger(__name__)

class BrowserTestCase(TestCase):
    '''Use selenium to test things in the browser'''

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(1200, 768)
        self.browser.set_window_position(300, 0)
        self.browser.implicitly_wait(10)

    def tearDown(self):
        self.browser.quit()

    def _mapserver_loading_panel_test(self):
        '''Wait for ajax-loader GIF image to go away'''
        seconds = 2
        wait = WebDriverWait(self.browser, seconds)
        try:
            wait.until(lambda display: self.browser.find_element_by_id('map').
                        find_element_by_class_name('olControlLoadingPanel').
                        value_of_css_property('display') == 'none')
        except TimeoutException as e:
            return ('Mapserver images did not load after waiting ' +
                    str(seconds) + ' seconds')
        else:
            return ''

    def _wait_until_visible_then_click(self, element, scroll_up=True):
        # See: http://stackoverflow.com/questions/23857145/selenium-python-element-not-clickable
        element = WebDriverWait(self.browser, 5, poll_frequency=.2).until(
                        EC.visibility_of(element))
        if scroll_up:
            self.browser.execute_script("window.scrollTo(0, 0)")

        element.click()

    def _test_share_view(self, func_name):
        # Generic for any func_name that creates a view to share
        getattr(self, func_name)()

        share_view = self.browser.find_element_by_id('permalink')
        share_view.click()
        permalink = self.browser.find_element_by_id('permalink-box'
                             ).find_element_by_name('permalink')
        self._wait_until_visible_then_click(permalink)
        permalink_url = permalink.get_attribute('value')

        # Restart browser and load permalink
        self.tearDown()
        self.setUp()
        self.browser.get(permalink_url)
        self.assertEquals('', self._mapserver_loading_panel_test())

    def test_campaign_page(self):
        self.browser.get('http://localhost:8000/')
        self.assertIn('Campaign List', self.browser.title)

    def test_query_page(self):
        self.browser.get('http://localhost:8000/default/query/')
        self.assertIn('default', self.browser.title)
        self.assertEquals('', self._mapserver_loading_panel_test())

    def test_dorado_trajectory(self):
        self.browser.get('http://localhost:8000/default/query/')
        try:
            # Click on Platforms to expand
            platforms_anchor = self.browser.find_element_by_id(
                                    'platforms-anchor')
            self._wait_until_visible_then_click(platforms_anchor)
        except NoSuchElementException as e:
            print e
            print "Is the development server running?"
            return

        # Finds <tr> for 'dorado' then gets the button for clicking
        dorado_button = self.browser.find_element_by_id('dorado'
                            ).find_element_by_tag_name('button')
        self._wait_until_visible_then_click(dorado_button)

        # Test that Mapserver returns images
        self.assertEquals('', self._mapserver_loading_panel_test())

        # Test Spatial 3D
        spatial_3d_anchor = self.browser.find_element_by_id('spatial-3d-anchor')
        self._wait_until_visible_then_click(spatial_3d_anchor)
        showplatforms = self.browser.find_element_by_id('showplatforms')
        self._wait_until_visible_then_click(showplatforms)
        assert 'geolocation' == self.browser.find_element_by_id('dorado_LOCATION').tag_name

    def test_m1_timeseries(self):
        self.browser.get('http://localhost:8000/default/query/')
        # Test Temporal->Parameter for timeseries plots
        parameter_tab = self.browser.find_element_by_id('temporal-parameter-li')
        self._wait_until_visible_then_click(parameter_tab)
        si = self.browser.find_element_by_id('stride-info')
        self._wait_until_visible_then_click(si)
        assert 'bb470' in si.text

    def test_share_view_trajectory(self):
        self._test_share_view('test_dorado_trajectory')
        self.browser.implicitly_wait(10)
        assert 'geolocation' == self.browser.find_element_by_id('dorado_LOCATION').tag_name

    def test_share_view_timeseries(self):
        self._test_share_view('test_m1_timeseries')
        si = self.browser.find_element_by_id('stride-info')
        self._wait_until_visible_then_click(si)
        assert 'bb470' in si.text

