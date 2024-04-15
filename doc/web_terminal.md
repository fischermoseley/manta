

## Open Serial Port
<button class="md-button" id="connectButton">Connect</button>

## Load Manta Configuration File
<button class="md-button" id="uploadButton">Upload File</button>
<input type="file" id="fileInput" accept=".yaml,.yml" style="display: none">
<div id="filePath"></div>


<!-- Load Javascript -->
<script src="../javascripts/web_terminal.js"></script>
<script src="../javascripts/serial.js"></script>
<script src="../javascripts/upload.js"></script>
<script src="https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js"></script>

<script>
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

</script>

<!-- <iframe src="https://app.surfer-project.org/?load_url=https://app.surfer-project.org/picorv32.vcd&amp;startup_commands=show_quick_start;module_add%20testbench.top;toggle_menu" ,="" style="width: 100%; height: 100%"></iframe> -->