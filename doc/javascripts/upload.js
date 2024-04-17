let data;
let fileUploaded = false;

// Map the fake upload button to the real (hidden) upload button
document.addEventListener("DOMContentLoaded", function() {
    const uploadButton = document.getElementById("uploadButton");
    const fileInput = document.getElementById("fileInput");
    const filePathDisplay = document.getElementById("filePath");

    uploadButton.addEventListener("click", function() {
        fileInput.click();
    });

    fileInput.addEventListener("change", function() {
        const filePath = fileInput.value; // Get the file path from the file input
        filePathDisplay.textContent = "Loaded " + filePath; // Display the file path
    });
});

// Update fileUploaded flag when a file gets uploaded
document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
        data = e.target.result;
        fileUploaded = true;
    };
    reader.readAsText(file);
});

// Continuously poll to see if the file has been uploaded
function runAfterUpload() {
    if (!fileUploaded) {
        setTimeout(runAfterUpload, 100); // Check again after 100ms
        return;
    }

    // Additional JavaScript code to run after file upload
    // WebTerminal(data);
}

runAfterUpload();