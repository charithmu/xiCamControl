
async function startCapture() {
  let manaul = document.getElementById("btnradio32").checked;
  let save = document.getElementById("btnradio21").checked;

  const response = await fetch("/start_capture?manual=" + manaul + "&save=" + save);
  return response.text();
}

async function stopCapture() {
  const response = await fetch("/stop_capture");
  return response.text();
}

const start_capture = () => {
  startCapture().then((result) => {
    if (result == "Capture started.") {
      document.getElementById("startBtn").disabled = true;
      document.getElementById("stopBtn").disabled = false;
      document.getElementById("image_feed").src = "/image_stream";

      document.getElementById("status-msg").classList.remove("bg-danger");
      document.getElementById("status-msg").classList.add("bg-success");
      document.getElementById("status-msg").innerHTML = "Success: " + result;
    } else {
      document.getElementById("status-msg").classList.remove("bg-success");
      document.getElementById("status-msg").classList.add("bg-danger");
      document.getElementById("status-msg").innerHTML = "Error: " + result;
    }
  });
};

const stop_capture = () => {
  stopCapture().then((result) => {
    if (result == "Capture stopped.") {
      document.getElementById("startBtn").disabled = false;
      document.getElementById("stopBtn").disabled = true;
      document.getElementById("image_feed").src = "static/preview.jpg";

      document.getElementById("status-msg").classList.remove("bg-danger");
      document.getElementById("status-msg").classList.add("bg-success");
      document.getElementById("status-msg").innerHTML = "Success: " + result;
    } else {
      document.getElementById("status-msg").classList.remove("bg-success");
      document.getElementById("status-msg").classList.add("bg-danger");
      document.getElementById("status-msg").innerHTML = "Error: " + result;
    }
  });
};

// const save = () => {
//   var a = document.createElement("a");
//   a.href = document.getElementById("image_feed").src;
//   a.download = "image.png";
//   a.click();
//   console.log("saving image.");
// };

// const imageElement = document.getElementById('latest-image');
// const refreshImage = () => {
// imageElement.src = `/getLatestImage`;
// };
// setInterval(refreshImage, 1000);

// function refreshImage() {
// fetch('/latest_image')
// .then(response => response.json())
// .then(data => {
// console.log('Latest image:', data.latest_image);
// document.getElementById("webcamImage").src = '/images/' + data.latest_image;
// })
// .catch((error) => {
// console.error('Error:', error);
// });
// }

// setInterval(refreshImage, 1000); // Refresh image every second
