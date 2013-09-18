/**
 * GNU MediaGoblin -- federated, autonomous media hosting
 * Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

$(document).ready(function(){
    var file = document.getElementById('file');
    var uploaded = parseInt(document.getElementById('uploaded').value);
    var upload_limit = parseInt(document.getElementById('upload_limit').value);
    var max_file_size = parseInt(document.getElementById('max_file_size').value);

    file.onchange = function() {
        var file_size = file.files[0].size / (1024.0 * 1024);

        if (file_size >= max_file_size) {
            $('#file').after('<p id="file_size_error" class="form_field_error">Sorry, the file size is too big.</p>'); 
        }
        else if (document.getElementById('file_size_error')) {
            $('#file_size_error').hide();
        }

        if (upload_limit) {
            if ( uploaded + file_size >= upload_limit) {
                $('#file').after('<p id="upload_limit_error" class="form_field_error">Sorry, uploading this file will put you over your upload limit.</p>');
            }
            else if (document.getElementById('upload_limit_error')) {
                $('#upload_limit_error').hide();
            console.log(file_size >= max_file_size);
            }
        }
    };
});
