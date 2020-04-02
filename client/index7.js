  var url = 'http://127.0.0.1:5000';

  


  fetch(url + '/video', {
  method: 'POST', 
  mode: 'no-cors', 
  body: JSON.stringify({'email': 'navbahl@hotmail.com', 'password': 'Harsh@123' }),
  redirect: 'follow',
  headers: new Headers({
      'Accept': 'application/json',
      'Content-Type': 'application/json'
  })
}).then(function() { var videoLinkJson = response.values();
                     var videoLinkArrays = Object.videoLinkJson;
                     console.log(videoLinkArrays);   
                        })
  .catch(function(res){ console.log(response) })
