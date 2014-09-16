# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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


import wtforms


class AddSimpleForm(wtforms.Form):
    image = wtforms.FileField()
    name = wtforms.TextField(
        validators=[wtforms.validators.Length(min=0, max=500)])
    comment = wtforms.TextField()
    # tags = wtforms.FieldList(wtforms.TextField())
    category = wtforms.IntegerField()
    level = wtforms.IntegerField()


_md5_validator = wtforms.validators.Regexp(r"^[0-9a-fA-F]{32}$")


class AddForm(wtforms.Form):
    original_sum = wtforms.TextField(None,
        [_md5_validator,
         wtforms.validators.InputRequired()])
    thumbnail_sum = wtforms.TextField(None,
        [wtforms.validators.Optional(),
         _md5_validator])
    file_sum = wtforms.TextField(None, [_md5_validator])
    name = wtforms.TextField()
    date_creation = wtforms.TextField()
    categories = wtforms.TextField()
