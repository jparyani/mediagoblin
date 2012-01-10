$(document).ready(function () {
    var longitude = Number(
	$('#tile-map #gps-longitude').val());
    var latitude = Number(
	$('#tile-map #gps-latitude').val());

    console.log(longitude, latitude);

    var map = new L.Map('tile-map');

    var mqtileUrl = 'http://otile{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.jpg';
    var mqtileAttrib = 'Map data &copy; '
	+ String(new Date().getFullYear())
	+ ' OpenStreetMap contributors, CC-BY-SA.'
	+ ' Imaging &copy; '
	+ String(new Date().getFullYear())
	+ ' <a target="_blank" href="http://mapquest.com">MapQuest</a>.';
    var mqtile = new L.TileLayer(
	mqtileUrl,
	{maxZoom: 18,
	 attribution: mqtileAttrib,
	 subdomains: '1234'});

    var location = new L.LatLng(latitude, longitude); // geographical point (longitude and latitude)
    map.setView(location, 13).addLayer(mqtile);

    var marker = new L.Marker(location);
    map.addLayer(marker);
});
