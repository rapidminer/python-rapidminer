#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2025 RapidMiner GmbH
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see https://www.gnu.org/licenses/.
#
# Import all modules so they're accessible as rapidminer.core.modulename
from . import serdeutils
from . import utilities
from . import config
from . import resources
from . import connections
from . import oauthenticator
from . import studio
from . import server
from . import project
from . import scoring
from . import web_api

from .studio import Studio
from .server import Server, get_server
from .project import Project
from .scoring import Scoring
from .resources import File, RepositoryLocation, ProjectLocation
from .connections import Connections
from .web_api import WebApi