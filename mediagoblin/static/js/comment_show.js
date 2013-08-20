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
var content="";

function previewComment(){
    if ($('#comment_content').val() && (content != $('#comment_content').val())) {
        content = $('#comment_content').val();
        $.post($('#previewURL').val(),$('#form_comment').serialize(),
        function(data){
            preview = JSON.parse(data)
            $('#comment_preview').replaceWith("<div id=comment_preview><h3>" + $('#previewText').val() +"</h3><br />" + preview.content + 
            "<hr style='border: 1px solid #333;' /></div>");
        });
    }
}
$(document).ready(function(){
  $('#form_comment').hide();
  $('#button_addcomment').click(function(){
    $(this).fadeOut('fast');
    $('#form_comment').slideDown(function(){
    setInterval("previewComment()",1000);
        $('#comment_content').focus();
    });
  });
});
