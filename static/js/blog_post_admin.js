/**
 * Custom JavaScript for the blog post admin
 * Adds a modern Markdown editor with mobile support and image paste functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on post add/change forms
    if (!document.getElementById('id_content')) return;

    // Get post ID if available (for existing posts)
    const postIdInput = document.querySelector('input[name="post_id"]');
    const postId = postIdInput ? postIdInput.value : 'new';
    
    // Get the current form's action URL to extract CSRF token
    const form = document.querySelector('form');
    const csrfToken = form ? form.querySelector('input[name="csrfmiddlewaretoken"]').value : '';

    // Initialize the EasyMDE Markdown editor for the content field
    const easyMDE = new EasyMDE({
        element: document.getElementById('id_content'),
        spellChecker: true,
        autosave: {
            enabled: true,
            uniqueId: "blog-post-" + (document.getElementById('id_slug') ? document.getElementById('id_slug').value : 'new-post'),
            delay: 5000,
        },
        toolbar: [
            'bold', 'italic', 'heading', '|',
            'code', 'quote', 'unordered-list', 'ordered-list', '|',
            'link', 'image', '|',
            'preview', 'side-by-side', 'fullscreen', '|',
            'guide'
        ],
        renderingConfig: {
            codeSyntaxHighlighting: true,
        },
        status: ['autosave', 'lines', 'words', 'cursor'],
        placeholder: "Write your content here using Markdown...",
        maxHeight: '500px',
        minHeight: '300px',
        // Enable paste images
        uploadImage: true,
        imageUploadFunction: handleImageUpload,
    });

    // Save reference to CodeMirror instance
    const cm = easyMDE.codemirror;

    // Handle pasted images
    cm.on('paste', function(editor, event) {
        const clipboardData = event.clipboardData || window.clipboardData;
        
        // Check if clipboardData contains files (images)
        if (clipboardData && clipboardData.files && clipboardData.files.length > 0) {
            const file = clipboardData.files[0];
            
            // Check if the file is an image
            if (file.type.startsWith('image/')) {
                event.preventDefault(); // Prevent default paste behavior
                
                // Insert a placeholder while the image uploads
                const loadingPlaceholder = `![Uploading image...](loading)`;
                const cursor = cm.getCursor();
                cm.replaceRange(loadingPlaceholder, cursor);
                const placeholderPos = {
                    from: cursor,
                    to: { line: cursor.line, ch: cursor.ch + loadingPlaceholder.length }
                };
                
                // Read the image file and send it to the server
                processImageFile(file, placeholderPos);
            }
        } else if (clipboardData && clipboardData.items) {
            // For browsers that support clipboardData.items (most modern browsers)
            for (let i = 0; i < clipboardData.items.length; i++) {
                const item = clipboardData.items[i];
                if (item.type.indexOf('image') !== -1) {
                    event.preventDefault(); // Prevent default paste behavior
                    
                    // Get the image file
                    const file = item.getAsFile();
                    
                    // Insert a placeholder while the image uploads
                    const loadingPlaceholder = `![Uploading image...](loading)`;
                    const cursor = cm.getCursor();
                    cm.replaceRange(loadingPlaceholder, cursor);
                    const placeholderPos = {
                        from: cursor,
                        to: { line: cursor.line, ch: cursor.ch + loadingPlaceholder.length }
                    };
                    
                    // Read the image file and send it to the server
                    processImageFile(file, placeholderPos);
                    break;
                }
            }
        }
    });

    // Process image file and upload to server
    function processImageFile(file, placeholderPos) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const imageData = e.target.result; // Base64 encoded image data
            
            // Upload the image to the server
            uploadImageData(imageData, function(response) {
                if (response.success) {
                    // Create the markdown for the image
                    const imageMarkdown = `![Image](${response.url})`;
                    
                    // Replace the placeholder with the actual image markdown
                    cm.replaceRange(imageMarkdown, placeholderPos.from, placeholderPos.to);
                    
                    // Store the uploaded image info in a hidden field if it's a temporary upload
                    if (response.is_temp) {
                        storeTemporaryImageInfo(response.temp_path, response.url);
                    }
                } else {
                    // Show error and remove placeholder
                    alert('Failed to upload image: ' + (response.error || 'Unknown error'));
                    cm.replaceRange('', placeholderPos.from, placeholderPos.to);
                }
            });
        };
        
        reader.readAsDataURL(file);
    }

    // Upload the image data to the server
    function uploadImageData(imageData, callback) {
        const formData = new FormData();
        formData.append('image_data', imageData);
        formData.append('post_id', postId);
        
        fetch('/blog/upload/image/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            callback({ success: false, error: 'Network error' });
        });
    }

    // Handle image upload from toolbar button
    function handleImageUpload(file, onSuccess, onError) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('post_id', postId);
        
        fetch('/blog/upload/image/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                onSuccess(data.url);
                
                // Store the uploaded image info if it's a temporary upload
                if (data.is_temp) {
                    storeTemporaryImageInfo(data.temp_path, data.url);
                }
            } else {
                onError(data.error || 'Failed to upload image');
            }
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            onError('Network error');
        });
    }

    // Store temporary image paths to be processed on form submit
    function storeTemporaryImageInfo(tempPath, url) {
        // Check if we have a container for temporary images
        let tempImagesContainer = document.getElementById('temp-images-container');
        
        if (!tempImagesContainer) {
            // Create a container for temporary images if it doesn't exist
            tempImagesContainer = document.createElement('div');
            tempImagesContainer.id = 'temp-images-container';
            tempImagesContainer.style.display = 'none';
            form.appendChild(tempImagesContainer);
        }
        
        // Create a hidden input for this image
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'temp_images';
        input.value = JSON.stringify({ path: tempPath, url: url });
        tempImagesContainer.appendChild(input);
    }

    // Process temporary images on form submit
    if (form) {
        form.addEventListener('submit', function(e) {
            // The form will handle the submission normally
            // The backend will process the temporary images
            
            // Optionally, get content from EasyMDE if needed
            const contentField = document.getElementById('id_content');
            if (contentField) {
                contentField.value = easyMDE.value();
            }
        });
    }

    // Adjust editor for better mobile experience
    function adjustForMobile() {
        const isMobile = window.innerWidth < 768;
        const editorToolbar = document.querySelector('.editor-toolbar');
        
        if (editorToolbar) {
            if (isMobile) {
                // On mobile, make toolbar buttons smaller with less padding
                editorToolbar.style.flexWrap = 'wrap';
                const buttons = editorToolbar.querySelectorAll('button, a');
                buttons.forEach(btn => {
                    btn.style.padding = '6px';
                    btn.style.fontSize = '14px';
                });
            } else {
                // Reset styles on desktop
                editorToolbar.style.flexWrap = '';
                const buttons = editorToolbar.querySelectorAll('button, a');
                buttons.forEach(btn => {
                    btn.style.padding = '';
                    btn.style.fontSize = '';
                });
            }
        }
    }

    // Call on load and on resize
    adjustForMobile();
    window.addEventListener('resize', adjustForMobile);

    // Show/hide external URL field based on post type
    const postTypeSelect = document.getElementById('id_post_type');
    const externalUrlFieldset = document.querySelector('fieldset:nth-of-type(4)');
    
    function toggleExternalUrlField() {
        if (postTypeSelect.value === 'link') {
            externalUrlFieldset.style.display = 'block';
            // Expand the collapsed fieldset on mobile
            const legend = externalUrlFieldset.querySelector('h2');
            if (legend && legend.classList.contains('collapse-toggle')) {
                legend.classList.remove('collapsed');
                const collapseTarget = document.getElementById(legend.dataset.target);
                if (collapseTarget) collapseTarget.style.display = 'block';
            }
        } else {
            externalUrlFieldset.style.display = 'none';
        }
    }

    // Set initial state and add change listener
    if (postTypeSelect) {
        toggleExternalUrlField();
        postTypeSelect.addEventListener('change', toggleExternalUrlField);
    }

    // Better mobile experience for Django admin in general
    function enhanceMobileAdmin() {
        if (window.innerWidth < 768) {
            // Make the main content area full width
            const mainContent = document.getElementById('content-main');
            if (mainContent) mainContent.style.maxWidth = '100%';
            
            // Increase field fonts for better touch input
            const inputs = document.querySelectorAll('input[type="text"], input[type="url"], textarea:not(.CodeMirror)');
            inputs.forEach(input => {
                input.style.fontSize = '16px';  // Prevents iOS zoom on focus
                input.style.padding = '10px';
            });
            
            // Make select fields larger for better touch targets
            const selects = document.querySelectorAll('select');
            selects.forEach(select => {
                select.style.fontSize = '16px';
                select.style.height = '40px';
            });
            
            // Increase size of action buttons
            const buttons = document.querySelectorAll('input[type="submit"], .button');
            buttons.forEach(button => {
                button.style.padding = '12px 16px';
                button.style.fontSize = '16px';
            });
            
            // Add more space between form rows
            const formRows = document.querySelectorAll('.form-row');
            formRows.forEach(row => {
                row.style.padding = '12px 0';
            });
        }
    }
    
    enhanceMobileAdmin();
    window.addEventListener('resize', enhanceMobileAdmin);
});