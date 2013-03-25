# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import struct


class ThreeDeeParseError(Exception):
    pass


class ThreeDee():
    """
    3D model parser base class.  Derrived classes are used for basic
    analysis of 3D models, and are not intended to be used for 3D
    rendering.
    """

    def __init__(self, fileob):
        self.verts = []
        self.average = [0, 0, 0]
        self.min = [None, None, None]
        self.max = [None, None, None]
        self.width = 0  # x axis
        self.depth = 0  # y axis
        self.height = 0 # z axis

        self.load(fileob)
        if not len(self.verts):
            raise ThreeDeeParseError("Empty model.")

        for vector in self.verts:
            for i in range(3):
                num = vector[i]
                self.average[i] += num
                if not self.min[i]:
                    self.min[i] = num
                    self.max[i] = num
                else:
                    if self.min[i] > num:
                        self.min[i] = num
                    if self.max[i] < num:
                        self.max[i] = num

        for i in range(3):
            self.average[i]/=len(self.verts)

        self.width = abs(self.min[0] - self.max[0])
        self.depth = abs(self.min[1] - self.max[1])
        self.height = abs(self.min[2] - self.max[2])


    def load(self, fileob):
        """Override this method in your subclass."""
        pass


class ObjModel(ThreeDee):
    """
    Parser for textureless wavefront obj files.  File format
    reference: http://en.wikipedia.org/wiki/Wavefront_.obj_file
    """

    def __vector(self, line, expected=3):
        nums = map(float, line.strip().split(" ")[1:])
        return tuple(nums[:expected])
    
    def load(self, fileob):
        for line in fileob:
            line = line.strip()
            if line[0] == "v":
                self.verts.append(self.__vector(line))
            

class BinaryStlModel(ThreeDee):
    """
    Parser for ascii-encoded stl files.  File format reference:
    http://en.wikipedia.org/wiki/STL_%28file_format%29#Binary_STL
    """

    def load(self, fileob):
        fileob.seek(80) # skip the header
        count = struct.unpack("<I", fileob.read(4))[0]
        for i in range(count):
            fileob.read(12) # skip the normal vector
            for v in range(3):
                self.verts.append(struct.unpack("<3f", fileob.read(12)))
            fileob.read(2) # skip the attribute bytes


def auto_detect(fileob, hint):
    """
    Attempt to divine which parser to use to divine information about
    the model / verify the file."""

    if hint == "obj" or not hint:
        try:
            return ObjModel(fileob)
        except ThreeDeeParseError:
            pass

    if hint == "stl" or not hint:
        try:
            # HACK Ascii formatted stls are similar enough to obj
            # files that we can just use the same parser for both.
            # Isn't that something?
            return ObjModel(fileob)
        except ThreeDeeParseError:
            pass
        except ValueError:
            pass
        except IndexError:
            pass
        try:
            # It is pretty important that the binary stl model loader
            # is tried second, because its possible for it to parse
            # total garbage from plaintext =)
            return BinaryStlModel(fileob)
        except ThreeDeeParseError:
            pass
        except MemoryError:
            pass

    raise ThreeDeeParseError("Could not successfully parse the model :(")
