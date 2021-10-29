#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2021 RapidMiner GmbH
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

__version__ = "9.10.0.1-dev"

from .core.studio import Studio
from .core.server import Server
from .core.project import Project
from .core.server import get_server
from .core.scoring import Scoring
from .core.resources import File
from .core.resources import RepositoryLocation
from .core.connections import Connections
from .core.webservice import route
from flask import request