document.addEventListener('DOMContentLoaded', () => {
    // --- File Drag & Drop and Selection ---
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-elem');
    const nasPathInput = document.getElementById('nas-path');

    if (dropArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
        });

        // Handle dropped files
        dropArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }
    }

    if (fileInput) {
        // Handle file selection via button
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleFiles(files) {
        if (files.length === 0) {
            console.log('No files selected.');
            return;
        }
        
        // Assuming folder selection, webkitdirectory gives a flat list.
        // The path can be inferred from the first file's webkitRelativePath.
        const firstFile = files[0];
        if (firstFile && firstFile.webkitRelativePath) {
            const pathParts = firstFile.webkitRelativePath.split('/');
            if (pathParts.length > 1) {
                nasPathInput.value = pathParts[0]; // Set input to the folder name
                logToOutput(`Folder selected: ${pathParts[0]} with ${files.length} files.`);
            }
        } else {
            // Handle individual file selection
            const fileNames = Array.from(files).map(f => f.name).join(', ');
            nasPathInput.value = fileNames;
            logToOutput(`Files selected: ${fileNames}`);
        }
    }

    // --- Log Output ---
    const logOutput = document.getElementById('log-output');
    const clearOutputBtn = document.getElementById('clear-output');

    function logToOutput(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        const time = new Date().toLocaleTimeString('en-GB');
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'log-time';
        timeSpan.textContent = `[${time}]`;
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'log-message';
        messageSpan.textContent = message;
        
        entry.appendChild(timeSpan);
        entry.appendChild(messageSpan);
        
        logOutput.appendChild(entry);
        logOutput.scrollTop = logOutput.scrollHeight; // Auto-scroll to bottom
    }

    if (clearOutputBtn) {
        clearOutputBtn.addEventListener('click', () => {
            logOutput.innerHTML = '';
            logToOutput('Output cleared.');
        });
    }

    // --- Color Picker Sync ---
    const colorPicker = document.getElementById('custom-color-picker');
    const colorText = document.getElementById('custom-color-text');

    if(colorPicker && colorText) {
        colorPicker.addEventListener('input', (e) => {
            colorText.value = e.target.value.toUpperCase();
        });
        colorText.addEventListener('input', (e) => {
            colorPicker.value = e.target.value;
        });
    }
    
    console.log('UI script loaded and initialized.');
});
