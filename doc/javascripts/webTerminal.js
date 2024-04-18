// serial
let port;

async function connect() {
    try {
        const serialPort = await navigator.serial.requestPort();
        await serialPort.open({ baudRate: 115200 });
        port = serialPort;
        console.log('Connected to serial device:', port);
    } catch (error) {
        console.error('Error connecting to serial device:', error);
    }
}

async function write(data) {
    console.log("(Main) write() called with: ", data);
    const writer = port.writable.getWriter();
    await writer.write(new TextEncoder().encode(data));
    await writer.releaseLock();
}

async function read() {
    console.log("(Main) read() called");
    const reader = port.readable.getReader();
    const {value, done} = await reader.read();
    reader.releaseLock();

    if (!done) {
        return new TextDecoder().decode(value);
    }
}

// workers
let serviceWorker;

navigator.serviceWorker.register('../javascripts/service-worker.js').then(function(registration) {
  serviceWorker = registration.active;
  if (!serviceWorker) {
    location.reload();
  }
});

// main loop
let awaitingRead = false;
let awaitingWrite = false;
let writeData;

const worker = new Worker('../javascripts/web-worker.js');
worker.onmessage = function(e) {
  console.log("(Main) received message from web worker: ", e.data);
  if ("awaitingRead" in e.data) {awaitingRead = e.data.awaitingRead};
  if ("awaitingWrite" in e.data) {awaitingWrite = e.data.awaitingWrite};
  if ("writeData" in e.data) {writeData = e.data.writeData};
};

async function capture() {
    console.log("(Main): Sending message to Web Worker: ", "");
    worker.postMessage("");
}

async function checkForAwaitingInput() {
  if (awaitingRead) {
    let out = await read();
    console.log("(Main): Sending message to Service Worker: ", out);
    serviceWorker.postMessage(out);
  }

  if (awaitingWrite) {
    let out = await write(writeData);
    console.log("(Main): Sending message to Service Worker: ", out);
    serviceWorker.postMessage(out);
  }
}

setInterval(checkForAwaitingInput, 100);
