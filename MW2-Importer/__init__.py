# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "C2M_IMPORT",
    "author" : "SHEILAN",
    "description" : "Import C2M Files",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 3),
    "location" : "File > Import",
    "warning" : "",
    "category" : "Import-Export"
}

import bpy,os
from bpy.props import BoolProperty,StringProperty,FloatProperty
from bpy_extras.io_utils import ImportHelper

from . c2m_operators import*

def register():
    bpy.utils.register_class(C2M_ImportFile)
    bpy.types.TOPBAR_MT_file_import.append(import_c2m_menu)

def unregister():
    bpy.utils.unregister_class(C2M_ImportFile)
    bpy.types.TOPBAR_MT_file_import.remove(import_c2m_menu)

if __name__=="__main__":
    register()