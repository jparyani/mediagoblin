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

function init_report_resolution_form() {
    hidden_input_names = {
        'takeaway':['take_away_privileges'],
        'userban':['user_banned_until','why_user_was_banned'],
        'sendmessage':['message_to_user']
}
    init_user_banned_form();
    $('form#resolution_form').hide()
    $('#open_resolution_form').click(function() {
        $('form#resolution_form').toggle();
        $.each(hidden_input_names, function(key, list){
            $.each(list, function(index, name){
                $('label[for='+name+']').hide();
                $('#'+name).hide();
            });
        });
    });
    $('#action_to_resolve').change(function() {
        $('ul#action_to_resolve li input:checked').each(function() {
            $.each(hidden_input_names[$(this).val()], function(index, name){
                $('label[for='+name+']').show();
                $('#'+name).show();
            });
        });
        $('ul#action_to_resolve li input:not(:checked)').each(function() {
            $.each(hidden_input_names[$(this).val()], function(index, name){
                $('label[for='+name+']').hide();
                $('#'+name).hide();
            });
        });
    });
    $("#submit_this_report").click(function(){
        submit_user_banned_form()
    });
}

function submit_user_banned_form() {
    if ($("#user_banned_until").val() == 'YYYY-MM-DD'){
        $("#user_banned_until").val("");
    }
}

function init_user_banned_form() {
    $('#user_banned_until').val("YYYY-MM-DD")
    $("#user_banned_until").focus(function() {
        $(this).val("");
        $(this).unbind('focus');
    });
}
