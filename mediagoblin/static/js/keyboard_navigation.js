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

/* It must be wrapped into a function and you also cannot use
 * $(':not(textarea, input)') because of some reason. */

$(document).ready(function(){
  $('textarea, input').keydown(function(event){
    event.stopPropagation();
  });
});

$(document).keydown(function(event){
  switch(event.which){
    case 37:
      if($('a.navigation_left').length) {
        window.location = $('a.navigation_left').attr('href');
      }
      break;
    case 39:
      if($('a.navigation_right').length) {
      window.location = $('a.navigation_right').attr('href');
      }
      break;
  }
});
