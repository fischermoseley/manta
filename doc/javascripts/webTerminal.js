document.getElementById('connectButton').addEventListener('click', selectPort);

async function selectPort(){
    await navigator.serial.requestPort();
}

// Start Web Worker for Serial API
globalThis.receiveBuffer = [];

const serialWorker = new Worker("../javascripts/serial.js");
function sendToSerialWorker(data){
    console.log("Main -> Worker: ", data);
    serialWorker.postMessage(data);
}

serialWorker.onmessage = (e) => {
    console.log("Worker -> Main: ", e.data);
    receiveBuffer.push(e.data);
};

// Main function for the Web Terminal
async function WebTerminal(data){
    let pyodide = await loadPyodide();

    // Load Manta.yaml into pyodide's file system
    pyodide.FS.writeFile("/manta.yaml", data, { encoding: "utf8" });

    // Load micropip, setuptools, manta
    await pyodide.loadPackage("micropip");
    await pyodide.loadPackage("setuptools");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install('../assets/manta-1.0.0-py3-none-any.whl');

    pyodide.runPythonAsync(`
        import asyncio
        from js import sendToSerialWorker
        from js import receiveBuffer
        from manta import Manta

        #m = Manta("/manta.yaml")

        print("Sending read request")
        sendToSerialWorker("R0000\\r\\n")

        for _ in range(10):
            print(len(receiveBuffer))
            print(receiveBuffer)
            await asyncio.sleep(0.1)

        print("Python Complete")
    `);
}
