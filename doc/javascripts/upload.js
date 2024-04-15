let data;
let fileUploaded = false;

document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
        data = e.target.result;
        fileUploaded = true; // Set the flag to indicate file upload completion
    };
    reader.readAsText(file);
});

function runAfterUpload() {
    if (!fileUploaded) {
        setTimeout(runAfterUpload, 100); // Check again after 100ms
        return;
    }

    // Your additional JavaScript code to run after file upload
    web_terminal(data);
}

runAfterUpload(); // Start checking for file upload completion