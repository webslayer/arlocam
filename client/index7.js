async function postData(url = '', data = {}) {
  // Default options are marked with *
  const response = await fetch(url, {
    method: 'POST', // *GET, POST, PUT, DELETE, etc.
    mode: 'cors', // no-cors, *cors, same-origin
    cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
    headers: {
      'Content-Type': 'application/json'
      // 'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: JSON.stringify(data) // body data type must match "Content-Type" header
  });
  return await JSON.parse(response); // parses JSON response into native JavaScript objects
}


var xyz = postData('http://127.0.0.1:5000/video', {'email': 'navbahl@hotmail.com', 'password': 'Harsh@123' })
  .then((data) => {
    var x = Object.values(data);
    console.log(x); // JSON data parsed by `response.json()` call
    
    var mylapse = document.getElementById('timelapse');
    var thislapse = x;
    var activeVideo = 0;

    mylapse.addEventListener('ended', function(e) {
      // update the new active video index
      activeVideo = (++activeVideo) % thislapse.length;

      // update the video source and play
      mylapse.src = thislapse[activeVideo];
      mylapse.play();
    });
  
  });

