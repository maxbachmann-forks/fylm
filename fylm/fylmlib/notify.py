# -*- coding: future_fstrings -*-
# Copyright 2018 Brandon Shelley. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Notification handler for Fylm.

This module is used to send notifications to various external integrations.
"""

from __future__ import unicode_literals, print_function
from builtins import *
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
import os
import shutil

from plexapi.server import PlexServer
from fylmlib.pushover import init, Client
from colors import color
import requests

from fylmlib.pyfancy import *
from fylmlib.ansi import ansi
from fylmlib.log import log
import fylmlib.config as config
from fylmlib.console import console

"""Notification handler for Fylm.

This module handles all external services notifications.
Currently only Plex is supported, but Pushover is coming soon.
"""

def plex():
    """Plex notification handler.

    Notify Plex that it should check for updates.
    """

    # Check if Plex notifications are enabled, and that we're not running in 
    # quiet or rename modes.
    if (config.plex.enabled is True 
        and config.quiet is False 
        and config.rename_only is False
        and config.test is False):

        # Disable the log so that HTTP ops aren't printed to the log.
        log.disable()
        try:
            # Create a connection to the Plex server
            plex = PlexServer(baseurl=config.plex.baseurl, token=config.plex.token, timeout=10)
        except Exception as e:
            # If the connection fails, log the error and print a response to the console.
            log.enable()
            console().red(f'Could not connect to Plex server on {config.plex.baseurl}').print()
            console.error(e)
            return

        console().white('\nUpdating plex...').print()

        # If the connection was successful, tell Plex to update specified sections if running
        # in live mode. No need to notify in test mode since there won't be any changes.
        if not config.test:
            for section in (plex.library.section(section) for section in config.plex.sections):
                section.refresh()

        console().green(' Done ✓\n').print()

        # Re-enable logging when done.
        log.enable()

def pushover(film):
    """Pushover notification handler.

    Notify Pushover that an action has been performed.
    """

    # Check if Pushover notifications are enabled, and that we're not running in 
    # quiet or rename modes.
    if (config.pushover.enabled is True 
        and config.quiet is False 
        and config.rename_only is False
        and config.test is False):

        attachment = None
        images_path = os.path.join(os.getcwd(), 'fylm/__images__')
        if not os.path.exists(images_path):
            os.makedirs(images_path)

        if film.poster_path:
            url = urljoin('https://image.tmdb.org/t/p/w185/', film.poster_path)
            img = os.path.join(images_path, film.poster_path)
            response = requests.get(url, stream=True)
            with open(img, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            attachment = ("image.jpg", open(img, "rb"), "image/jpeg")

        # Application API token/key, which can be found by selecting your app
        # from https://pushover.net/apps and copying the key.
        init(config.pushover.app_token)

        # Initialize the Pushover client with your Pushover user key, which can
        # be found at https://pushover.net
        pushover = Client(config.pushover.user_key)

        message = ('. '.join(film.overview.split('.  ')[:2]) + '.'[:200] + '...') if len(film.overview) > 200 else film.overview

        pushover.send_message(
            message=f"{film.title} ({film.year})\n{message}", 
            attachment=attachment,
            title='Fylm Added')

        os.remove(img)