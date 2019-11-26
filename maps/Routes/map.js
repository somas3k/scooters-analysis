const home = {
  lat: 50.049683,
  lng: 19.944544,
};

//
var map;
var carPath = [];

const mydata = routes;

const colorArray = ['#FF6633', '#FFB399', '#FF33FF', '#00B3E6', 
'#E6B333', '#3366E6', '#999966', '#99FF99', '#B34D4D',
'#80B300', '#809900', '#E6B3B3', '#6680B3', '#66991A', 
'#FF99E6', '#CCFF1A', '#FF1A66', '#E6331A', '#33FFCC',
'#66994D', '#B366CC', '#4D8000', '#B33300', '#CC80CC', 
'#66664D', '#991AFF', '#E666FF', '#4DB3FF', '#1AB399',
'#E666B3', '#33991A', '#CC9999', '#B3B31A', '#00E680', 
'#4D8066', '#809980', '#E6FF80', '#1AFF33', '#999933',
'#FF3380', '#CCCC00', '#66E64D', '#4D80CC', '#9900B3', 
'#E64D66', '#4DB380', '#FF4D4D', '#99E6E6', '#6666FF'];


document.getElementById('routeList').appendChild(makeUL(Object.keys(mydata)));

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    center: {lat: home.lat, lng: home.lng},
    zoom: 12,
  });
}

function addMarker(location, map) {
  var marker = new google.maps.Marker({
    position: location,
    map,
  });
  return marker;
}


function clearPolyline() {
  const myNode = document.getElementById("details");
  while (myNode.firstChild) {
    myNode.removeChild(myNode.firstChild);
  }
  carPath.forEach(path => path.setMap(null));
  carPath = [];
}

function getPolylineCoordinates(routes) {
  let coordinates = [];
  let p = 0;

  routes.forEach((route) => {
    const lastLocation = coordinates.length > 0 && coordinates[p-1][coordinates[p-1].length - 1];
    if (lastLocation
        && lastLocation.lat === route.from.location.lat
        && lastLocation.lng === route.from.location.lng) {
      coordinates[p-1].push({
        lat: route.to.location.lat,
        lng: route.to.location.lng,
        name: route.to.location.name,
        stays_at: route.to.stays_at,
      });
    } else {
      coordinates.push([
        {
          lat: route.from.location.lat,
          lng: route.from.location.lng,
          name: route.from.location.name,
          stays_at: route.from.stays_at,
        }, {
          lat: route.to.location.lat,
          lng: route.to.location.lng,
          name: route.to.location.name,
          stays_at: route.to.stays_at,
        },
      ]);
      p = p+1;
    }  
  })

  return coordinates;
}

function drawCarPolyline(coordinates, map) {

  const paths = [];
  console.log(coordinates);

  coordinates.forEach((carCoordinate, index) => {
    const carPath = new google.maps.Polyline({
      path: carCoordinate,
      geodesic: true,
      strokeColor: colorArray[index],
      strokeOpacity: 1.0,
      strokeWeight: 5
    });

    carPath.setMap(map);

    paths.push(carPath);
  });

  return paths;
}

function describeRoute(coordinates) {
  coordinates.forEach((carRoutes, index) => {
    let trace = '';
    carRoutes.forEach(route => {
     trace = trace + ' -> ' + route.name;
    });
    var h = document.createElement("H3");
    var t = document.createTextNode(trace);
    h.style.color = colorArray[index];
    h.appendChild(t);
    document.getElementById("details").appendChild(h);
  });
}

function changeCarRoutes(carId) {
  clearPolyline();
  
  if (mydata[carId]) {
    const coordinates = getPolylineCoordinates(mydata[carId]);
    carPath = drawCarPolyline(coordinates, map);
    describeRoute(coordinates);
  }
}

function makeUL(array) {
  var list = document.createElement('ul');
  list.id = 'cars';

  for (var i = 0; i < array.length; i++) {
      var item = document.createElement('li');
      const carId = array[i];
      item.appendChild(document.createTextNode(array[i]));
      item.onclick = function () { changeCarRoutes(carId); }
      list.appendChild(item);
  }
  return list;
}