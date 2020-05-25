// let m = moment();

async function postData(url = "", data = {}) {
	// Default options are marked with *
	const response = await fetch(url, {
		method: "POST", // *GET, POST, PUT, DELETE, etc.
		mode: "cors", // no-cors, *cors, same-origin
		cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
		headers: {
			"Content-Type": "application/json",
			// 'Content-Type': 'application/x-www-form-urlencoded',
		},
		body: JSON.stringify(data), // body data type must match "Content-Type" header
	});
	return await response.json(); // parses JSON response into native JavaScript objects
}

async function abortSnaps() {
	var i;
	for (i = 0; i <= 3; i++) {
		await fetch("https://arlocam.herokuapp.com/snapstop").then(
			(response) => {
				// console.log(response);
				response.json().then((data) => {
					console.log(data);
				});
			}
		);
	}
	console.log("Done");
}

function toggleView() {
	$(".deletionOptions").toggleClass("d-none");
}

function deleteTimelapse() {
	var json = prompt("Code");
	fetch("https://arlocam.herokuapp.com/del_timelapse", {
		method: "post",
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json",
		},
		body: json,
	})
		.then(function (data) {
			console.log("Request succeeded with JSON response", data);
		})
		.catch(function (error) {
			console.log("Request failed", error);
		});
}

function recentTimelapse(prop) {
	fetch("https://arlocam.herokuapp.com/get_timelapse")
		.then((response) => response.json())
		.then((json) => {
			console.log(json);
			$(".video").siblings().remove();

			// var test = JSON.stringify(json);
			// console.log(test[0])
			// <video src="${mostRecent}" id="timelapse" class="border img-fluid" controls style="background:black">
			// </video>
			// console.log(l);

			$.each(json, function (k, v) {
				console.log(v.title);
				const dateFrom = moment(v.datefrom, "DDMMYYYY");
				console.log(dateFrom);
				const dateTo = moment(v.dateto, "DDMMYYYY");
				console.log(dateTo);
				var diff = dateTo.diff(dateFrom, prop);
				if (diff == 1) {
					$(".video")
						.clone()
						.appendTo(".gallery")
						.addClass(k)
						.removeClass("video")
						.css("display", "block");
					$(`.${k} .videoTitle`).text(v.title);
					$(`.${k} .videoDateFrom`).append(
						`<b>Date From</b>: ${dateFrom.format("DD/MM/YYYY")}`
					);
					$(`.${k} .videoDateTo`).append(
						`<b>Date To</b>: ${dateTo.format("DD/MM/YYYY")}`
					);
					var video = $(`.${k}`).find("video")[0];
					video.src = v.url;
					video.load();
				}
			});

			//       <h2>Lists of videos</h2><ul>
			//         <li>
			//           https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-05-12%2008%3A55%3A02%2B01%3A00.avi?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200513%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200513T110656Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=35c6b827dea72351a1f46a724bca8ce0974d78511aa699df68373e505c276a5f
			//                             </li>
			//       </ul>
			// index7.js: 38 < h2 > Lists of videos</h2 > <ul>
			//         <li>
			//           https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-05-12%2015%3A25%3A12%2B01%3A00.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200513%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200513T110656Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=451c3a2069c063a77e270e982f83dd6ce2f97e2759fbf9b12244f819571a25db
			//                             </li>
			//       </ul>
			//       index7.js: 38 < h2 > Lists of videos</h2 > <ul>
			//         <li>
			//           https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-05-12%2015%3A27%3A47%2B01%3A00.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200513%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200513T110656Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=a956f773f9700eb8208732b65b198b79b499dd48e2f9b5a017d8c76129b5c368
			//                             </li>
			//       </ul>

			// <ul>
			//   <li>
			//     https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-05-12%2008%3A55%3A02%2B01%3A00.avi?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200513%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200513T112453Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=3c39d783017a3fd4795fb81ee5035cdc97efc32db80d5d60fa45afe57874366e
			//                       </li>

			//   <li>
			//     https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-05-12%2015%3A25%3A12%2B01%3A00.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200513%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200513T112453Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=206693016f95e86ce574220f8f0e2a88e3e48dda06b0d518c1d5ebf4a22c3778
			//                       </li>

			//   <li>
			//     https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-05-12%2015%3A27%3A47%2B01%3A00.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200513%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200513T112453Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=c303d4318c3d84db8af6f45ef97d00bda48915852b9195482ce4dc2cc6fef82e
			//                       </li>
			// </ul>
		});
}

// var p = {
//   "video0": {
//     "url": "https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-04-29%2009%3A08%3A36%2B01%3A00.avi?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200429%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200429T124307Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=3c7e47ab87cfd5b2d443bb7f0bc9f408a996906f46315f2a87f8ef7c85cdc6f1",
//     "datefrom": "26042020",
//     "dateto": "30042020"
//   },
//   "video1": {
//     "url": "https://s3.eu-west-2.amazonaws.com/arlocam-timelapse/timelapse-2020-04-29%2012%3A51%3A46%2B01%3A00.avi?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJIOPZACTSKHZXTVA%2F20200429%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20200429T124307Z&X-Amz-Expires=604000&X-Amz-SignedHeaders=host&X-Amz-Signature=05700d2d123cadaf3a5d31dc09d76301fb2ddaf9570f37c9010ddecf46279a2b",
//     "datefrom": "26042020",
//     "dateto": "30042020"
//   }
// }

//if i=0 i<=Object.keys(p).length i++
//else break
// var y = Object.keys(p).length;
// var x = [];
// for(var i=0; i<y; i++){

//  x[i] = "video" + i;
//  console.log(x)
// }

// function requestDate() {
//   var dateFrom = prompt("Enter the dateFrom (ddmmyyyy)");
//   var dateTo = prompt("Enter the dateTo (ddmmyyyy)");
//   fetch('https://arlocam.herokuapp.com/timelapse', {'datefrom': dateTo, 'dateto': dateFrom} ,{
//     method:'POST',
//     hmode: 'cors', // no-cors, *cors, same-origin
//     cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
//     headers: {
//       'Content-Type': 'application/json'
//       // 'Content-Type': 'application/x-www-form-urlencoded',
//     },
//     body: JSON.stringify(data)
//   })
//         .then((res) => res.json)
//         .then((data) => console.log(data))
// }

function generateSnaps() {
	var seconds = prompt("Please enter the snapshot interval");
	fetch("https://arlocam.herokuapp.com/snapshot?x=" + seconds).then(
		(data) => {
			document.querySelector(".generateShots").innerHTML = "OK!";
		}
	);
}

async function logintoarlo() {
	var email = prompt("Please enter your email");
	var password = prompt("Please enter your password");
	await postData("https://arlocam.herokuapp.com/login", {
		email: email,
		password: password,
	}).then((data) => {
		console.log(data);
	});
}

// async function requestLapse() {
// var dateFrom = prompt("Enter the dateFrom (ddmmyyyy)");
// var dateTo = prompt("Enter the dateTo (ddmmyyyy)");
// await postData('https://arlocam.herokuapp.com/timelapse', {'datefrom': dateFrom, 'dateto': dateTo })
// .then((data) => {

//   console.log(data)
//   });
//   location.reload();
// }
async function requestLapse(prop) {
	let m = moment();
	// var month = `${moment().subtract(1, 'months')}`;
	// console.log(month)
	// console.log(`${m.toISOString()}`)
	var dateTo = m.add(1, "days").format("DDMMYYYY");
	var dateFrom = m.subtract(1, prop).subtract(1, "days").format("DDMMYYYY");
	await postData("https://arlocam.herokuapp.com/timelapse", {
		datefrom: dateFrom,
		dateto: dateTo,
	}).then((data) => {
		// document.querySelector('.requestLapse').innerHTML = "OK!"
		console.log(data);
	});
	location.reload();
}
