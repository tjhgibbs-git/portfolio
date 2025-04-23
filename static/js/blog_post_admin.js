/**
 * Custom JavaScript for the blog post admin
 * Adds a modern Markdown editor with mobile support
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on post add/change forms
    if (!document.getElementById('id_content')) return;

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
    });

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