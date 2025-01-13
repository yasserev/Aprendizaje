document.addEventListener('DOMContentLoaded', function() {
    // Configurar todas las áreas de carga
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        const input = area.querySelector('.file-input');
        
        // Manejar clic en el área
        area.addEventListener('click', () => {
            input.click();
        });

        // Manejar cambio en el input
        input.addEventListener('change', (e) => {
            handleFiles(e.target.files, area.id);
        });

        // Manejar eventos de arrastrar y soltar
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            handleFiles(e.dataTransfer.files, area.id);
        });
    });
});

function showMessage(message, isError = false) {
    // Crear o actualizar el elemento de mensaje
    let messageElement = document.getElementById('message-alert');
    if (!messageElement) {
        messageElement = document.createElement('div');
        messageElement.id = 'message-alert';
        messageElement.style.position = 'fixed';
        messageElement.style.top = '20px';
        messageElement.style.right = '20px';
        messageElement.style.zIndex = '1000';
        messageElement.style.padding = '15px';
        messageElement.style.borderRadius = '5px';
        messageElement.style.maxWidth = '300px';
        document.body.appendChild(messageElement);
    }

    // Establecer el estilo según el tipo de mensaje
    messageElement.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
    messageElement.style.color = isError ? '#721c24' : '#155724';
    messageElement.style.border = `1px solid ${isError ? '#f5c6cb' : '#c3e6cb'}`;
    messageElement.textContent = message;

    // Mostrar el mensaje
    messageElement.style.display = 'block';

    // Ocultar después de 5 segundos
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 5000);
}

function handleFiles(files, areaId) {
    // Mostrar indicador de carga
    const area = document.getElementById(areaId);
    const loadingText = area.querySelector('.upload-text span');
    const originalText = loadingText.textContent;
    loadingText.textContent = 'Procesando...';

    const formData = new FormData();
    
    // Añadir archivos al FormData según el área
    if (areaId === 'mergePdfArea') {
        for (let file of files) {
            formData.append('files[]', file);
        }
    } else {
        formData.append('file', files[0]);
    }

    // Determinar la URL del endpoint según el área
    let endpoint = '';
    switch (areaId) {
        case 'convertToPdfArea':
            endpoint = '/convert-to-pdf';
            break;
        case 'convertFromPdfArea':
            endpoint = '/convert-from-pdf';
            break;
        case 'mergePdfArea':
            endpoint = '/merge';
            break;
        case 'splitPdfArea':
            endpoint = '/split';
            break;
        case 'editPdfArea':
            endpoint = '/edit';
            break;
        case 'signPdfArea':
            endpoint = '/sign';
            break;
    }

    // Enviar archivos al servidor
    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/pdf')) {
            // Es un PDF, descargarlo
            return response.blob().then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                // Obtener el nombre del archivo del header Content-Disposition
                const disposition = response.headers.get('content-disposition');
                const filename = disposition ? disposition.split('filename=')[1].replace(/['"]/g, '') : 'converted.pdf';
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                showMessage('Archivo convertido y descargado exitosamente');
                return null; // No intentar parsear como JSON
            });
        } else if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data) { // Solo procesar si hay datos JSON (no para descargas de PDF)
            if (data.error) {
                showMessage(data.error, true);
            } else {
                showMessage(data.message || 'Operación completada con éxito');
                if (data.downloadUrl) {
                    window.location.href = data.downloadUrl;
                }
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error al procesar el archivo: ' + error.message, true);
    })
    .finally(() => {
        // Restaurar el texto original
        loadingText.textContent = originalText;
    });
}
