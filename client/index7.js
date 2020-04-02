  var url = 'site';

  


  fetch(url + '/video', {
  method: 'POST', 
  mode: 'cors', 
  body: JSON.stringify({'email': 'navbahl@hotmail.com', 'password': 'Harsh@123' }),
  redirect: 'follow',
  headers: new Headers({
      'Accept': 'application/json',
      'Content-Type': 'application/json'
  })
}).then(function() { var videoLinkJson = res.values();
                     var videoLinkArrays = Object.videoLinkJson;
                     console.log(videoLinkArrays);   
                        })
  .catch(function(res){ console.log(res) })
