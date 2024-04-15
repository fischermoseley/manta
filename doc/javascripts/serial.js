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
    console.log('Sent:', data);
}

async function read() {
    const port = await getPort();
    const reader = port.readable.getReader();
    const {value, done} = await reader.read();
    reader.releaseLock();

    if (!done) {
        const data = new TextDecoder().decode(value);
        console.log('Received:', data);
        return data;
    }
}
