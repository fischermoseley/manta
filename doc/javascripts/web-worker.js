let pyodide;

importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

(async function() {
  pyodide = await loadPyodide({ indexURL : "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/" });
    const response = await fetch('../assets/main.py');
    pyodide.runPython(await response.text());
    console.log("(Web Worker) Python loaded!");
})()

addEventListener('message', function(e) {
  console.log("(Web Worker): Message received from main thread: ", e.data);
  const output = pyodide.globals.get("capture")(e.data);
});

function blockingRequestToURL(url) {
  const request = new XMLHttpRequest();

  // `false` makes the request synchronous
  request.open('GET', url, false);
  request.send(null);
  console.log('status', request.status);
  return request.responseText;
}

function workerReadSerial() {
  console.log("(Web Worker): workerReadSerial called");
  postMessage({awaitingRead: true});
  data = blockingRequestToURL('/read_serial/');
  postMessage({awaitingRead: false});
  return data;
}

function workerWriteSerial(data) {
  console.log("(Web Worker): workerWriteSerial called with: ", data);
  postMessage({awaitingWrite: true, writeData: data});
  blockingRequestToURL('/write_serial/');
  postMessage({awaitingWrite: false, writeData: undefined});
}