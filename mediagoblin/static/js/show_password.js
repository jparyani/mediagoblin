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
  //Create a duplicate password field. We could change the input type dynamically, but this angers the IE gods (not just IE6).
  $("#password").after('<input type="text" value="" name="password_clear" id="password_clear" /><label><input type="checkbox" id="password_boolean" />Show password</label>');
  $('#password_clear').hide();
  $('#password_boolean').click(function(){
    if($('#password_boolean').prop("checked")) {
      $('#password_clear').val($('#password').val());
      $('#password').hide();
      $('#password_clear').show();
    } else {
      $('#password').val($('#password_clear').val());
      $('#password_clear').hide();
      $('#password').show();
    };
  });
  $('#password,#password_clear').keyup(function(){
    $('#password').val($(this).val());
    $('#password_clear').val($(this).val());
  });
});
