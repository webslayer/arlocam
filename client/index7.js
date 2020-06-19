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

function recentTimelapse() {
	fetch("https://arlocam.herokuapp.com/get_timelapse")
		.then((response) => response.json())
		.then((json) => {
			console.log(json);
			$(".video").siblings().remove();

			$.each(json, function (k, v) {
				console.log(v.title);
				const dateFrom = moment(v.datefrom, "DDMMYYYY");
				console.log(dateFrom);
				const dateTo = moment(v.dateto, "DDMMYYYY");
				console.log(dateTo);
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
			});
		});
}

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

async function requestLapse(prop) {
	let m = moment();
	await fetch("https://arlocam.herokuapp.com/get_timelapse")
		.then((response) => response.json())
		.then((json) => {
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
		});
	var dateTo = m.add(1, "days").format("DDMMYYYY");
	var dateFrom = m.subtract(1, prop).format("DDMMYYYY");

	await postData("https://arlocam.herokuapp.com/timelapse", {
		datefrom: dateFrom,
		dateto: dateTo,
	}).then((data) => {
		// document.querySelector('.requestLapse').innerHTML = "OK!"
		console.log(data);
	});
	location.reload();
	recentTimelapse();
}
