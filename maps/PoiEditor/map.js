const home = {
  lat: 50.049683,
  lng: 19.944544,
};

//
var map;
var infowindow;
var lines;
var service;
var poiList = [];
var delay = 0;

const mydata = JSON.parse(pois);
const timestamps = Object.keys(mydata);
let timestampIndex = 0;
let markers = [];

document.getElementById("changeLocationButton").addEventListener("click", drawAnotherLocations);
document.getElementById("drawLocationButton").addEventListener("click", drawCarLocations);
document.getElementById("clearLocationButton").addEventListener("click", clearCarLocations);
document.getElementById("savePoiButton").addEventListener("click", savePoi);

function getId() {
 return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

function drawAnotherLocations() {
  timestampIndex = (timestampIndex + 1) % timestamps.length;
  drawCarLocations();
}

function drawCarLocations() {
  markers.forEach(marker => marker.setMap(null));
  markers = [];

  mydata[timestamps[timestampIndex]].forEach(location => {
    const marker = addCarMarker(location, map, '483151');
    markers.push(marker);
  });
}

function clearCarLocations() {
  markers.forEach(marker => marker.setMap(null));
  markers = [];
}

function savePoi() {
  console.log(JSON.stringify(poiList));
  const fileName = `poi_${getId()}`;
  download(fileName, JSON.stringify(poiList));
  console.log("Saved as - ", fileName);
}

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    center: {lat: home.lat, lng: home.lng},
    zoom: 12,
  });
  service = new google.maps.places.PlacesService(map);
  infowindow = new google.maps.InfoWindow();

  this.placesService = new google.maps.places.PlacesService(map);
  
  google.maps.event.addListener(map, 'click', function(e) {
    e.stop();
    console.log('clicked @', e);
    if (e.placeId) {
      getPlaceDetails(e.placeId);
    }
  });
}

function getPlaceDetails(placeId) {
  this.placesService.getDetails({placeId: placeId}, function(place, status) {
    if (status === 'OK') {
      const newPoi = {
        place_id: place.place_id,
        lng: place.geometry.location.lng(),
        lat: place.geometry.location.lat(),
        address: place.formatted_address,
        name: place.name,
        rating: place.rating,
        user_ratings_total: place.user_ratings_total,
        types: place.types,
        website: place.website,
      };
      const addedMarker = addMarker({ lat: newPoi.lat, lng: newPoi.lng }, map, '7A908E');
      google.maps.event.addListener(addedMarker, 'click', () => {
        poiList = poiList.filter(poi => poi.lat !== newPoi.lat && poi.lng !== newPoi.lng);
        addedMarker.setMap(null);
      })
      poiList.push(newPoi);
    }
  });
}

function addCarMarker(location, map, color) {
  var marker = new google.maps.Marker({
    position: location,
    map,
  });
  return marker;
}

function addMarker(location, map, color) {
  var marker = new google.maps.Circle({
    center: location,
    strokeColor: '#483151',
    strokeOpacity: 0,
    strokeWeight: 2,
    fillColor: `#${color}`,
    fillOpacity: 0.5,
    radius: 70,
    map,
  });
  return marker;
}

function download(filename, text) {
  var pom = document.createElement('a');
  pom.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  pom.setAttribute('download', filename);

  if (document.createEvent) {
      var event = document.createEvent('MouseEvents');
      event.initEvent('click', true, true);
      pom.dispatchEvent(event);
  }
  else {
      pom.click();
  }
}

