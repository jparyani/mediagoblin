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

$(document).ready(function () {
    if (!$('#tile-map').length) {
        return;
    }
    console.log('Initializing map');

    var longitude = Number(
	$('#tile-map #gps-longitude').val());
    var latitude = Number(
	$('#tile-map #gps-latitude').val());

    // Get a new map instance attached and element with id="tile-map"
    var map = new L.Map('tile-map');

    var mqtileUrl = 'http://otile{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.jpg';
    var mqtileAttrib = '<a id="osm_license_link">see map license</a>';
    var mqtile = new L.TileLayer(
	mqtileUrl,
	{maxZoom: 18,
	 attribution: mqtileAttrib,
	 subdomains: '1234'});

    map.attributionControl.setPrefix('');
    var location = new L.LatLng(latitude, longitude);
    map.setView(location, 13).addLayer(mqtile);

    var marker = new L.Marker(location);
    map.addLayer(marker);
});
