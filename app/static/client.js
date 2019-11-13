var el = x => document.getElementById(x);

function showPicker() {
  el("file-input").click();
}

function showPicked(input) {
  el("upload-label").innerHTML = input.files[0].name;
  var reader = new FileReader();
  reader.onload = function(e) {
    el("image-picked").src = e.target.result;
    el("image-picked").className = ``;
    el("no-image-picked").className = "no-display";
    el("result-label").innerHTML = ``;
    el("result_micro-label").innerHTML = ``;
    el("top_5_results-label").innerHTML = ``;

  };
  reader.readAsDataURL(input.files[0]);
}

function useExampleImage() {
    el("upload-label").innerHTML = 'Carrier.jpg';
    el("no-image-picked").className = ``;
    el("image-picked").className = "no-display";
    el("result-label").innerHTML = `Major Class: Carrier (99% Probability)`;
    el("result_micro-label").innerHTML = `Specific Class guess: Liaoning 001 Carrier (99% Probability)`;
    el("top_5_results-label").innerHTML = `Top 5 Class & NATO Types with Probabilities: <table border="1" class="dataframe"><thead><tr style="text-align: right;"><th>Classes</th><th>Probability</th></tr></thead><tbody><tr><td>Liaoning 001 Carrier</td><td>99%</td></tr><tr><td>Fuqing 905 Tender</td><td>0%</td></tr><tr><td>Jiangkai I 054 Frigate</td><td>0%</td></tr><tr><td>Jianghu 053H1 Frigate</td><td>0%</td></tr><tr><td>Fuchi 903 Tender</td><td>0%</td></tr></tbody></table>`;
}


function analyze() {
  var uploadFiles = el("file-input").files;
  if (uploadFiles.length !== 1) alert("Please select a file to analyze!");

  el("analyze-button").innerHTML = "Analyzing...";
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
    true);
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
      var response = JSON.parse(e.target.responseText);
      el("result-label").innerHTML = `Major Class: ${response["result"]}`;
      el("result_micro-label").innerHTML = `Specific Class guess: ${response["result_micro"]}`;
      el("top_5_results-label").innerHTML = `Top 5 Class & NATO Types with Probabilities: ${response["top_5"]}`;
    }
    el("analyze-button").innerHTML = "Analyze (5-10 sec)";
  };

  var fileData = new FormData();
  fileData.append("file", uploadFiles[0]);
  xhr.send(fileData);
}

function submitHull() {
  var hullText = el("hull-text").value;
  if (hullText.length === 0) alert("Please input a number!");

  el("submit-hull-button").innerHTML = "Submitting...";
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/hull_lookup`,
    true);
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
      var response = JSON.parse(e.target.responseText);
      el("result_hull-label").innerHTML = `Hull ${hullText} lookup: ${response["hull_information"]}`;
    }
    el("submit-hull-button").innerHTML = "Submit";
  };

  var hullForm = new FormData();
  hullForm.append("hull_text", hullText);
  xhr.send(hullForm);
  el("result_hull-label").innerHTML = "Submitted no response";
}
