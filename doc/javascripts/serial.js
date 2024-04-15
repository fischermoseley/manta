let port;

async function getPort() {
    if (port) return port;
    try {
        [port] = await navigator.serial.getPorts();
        await port.open({ baudRate: 115200 });
        console.log('Connected to serial device:', port);
        return port;
    } catch (error) {
        console.error('Error connecting to serial device:', error);
    }
}

async function write(data) {
    const port = await getPort();
    const writer = port.writable.getWriter();
    await writer.write(new TextEncoder().encode(data));
    await writer.releaseLock();
}

async function read() {
    const port = await getPort();
    const reader = port.readable.getReader();
    const {value, done} = await reader.read();
    reader.releaseLock();

    if (!done) {
        return new TextDecoder().decode(value);
    }
}

self.addEventListener('message', async function(event) {
    await write(event.data);
});

async function readWrapper() {
    if (port) {
        self.postMessage(await read()); // this is a hack but i'm curious
    }
}

setInterval(readWrapper, 500);