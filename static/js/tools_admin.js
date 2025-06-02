// Tools Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize HTML content textarea
    const htmlTextarea = document.querySelector('#id_html_content');
    if (htmlTextarea) {
        // Auto-resize functionality
        function autoResize() {
            htmlTextarea.style.height = 'auto';
            htmlTextarea.style.height = Math.max(htmlTextarea.scrollHeight, 400) + 'px';
        }
        
        htmlTextarea.addEventListener('input', autoResize);
        autoResize(); // Initial resize
        
        // Auto-extract title when HTML is pasted
        htmlTextarea.addEventListener('paste', function(e) {
            setTimeout(function() {
                const nameField = document.querySelector('#id_name');
                if (nameField && !nameField.value.trim()) {
                    const htmlContent = htmlTextarea.value;
                    const titleMatch = htmlContent.match(/<title[^>]*>(.*?)<\/title>/i);
                    if (titleMatch) {
                        nameField.value = titleMatch[1].trim();
                        nameField.style.background = '#f0f8ff';
                        setTimeout(() => {
                            nameField.style.background = '';
                        }, 2000);
                    }
                }
            }, 100);
        });
    }
    
    // Add helpful tooltips
    const descriptionField = document.querySelector('#id_description');
    if (descriptionField && !descriptionField.value) {
        descriptionField.placeholder = 'Optional: Describe what this tool does (will be shown in the tools list)';
    }
    
    // Enhance slug field display
    const slugField = document.querySelector('#id_slug');
    if (slugField) {
        const slugHelp = document.createElement('div');
        slugHelp.style.cssText = 'font-size: 11px; color: #666; margin-top: 4px;';
        slugHelp.innerHTML = 'Auto-generated from name. Tool will be accessible at <code>/tools/[slug]/</code>';
        slugField.parentNode.appendChild(slugHelp);
    }
    
    // Add syntax highlighting hint
    if (htmlTextarea) {
        const hint = document.createElement('div');
        hint.style.cssText = 'font-size: 11px; color: #666; margin-top: 5px; font-style: italic;';
        hint.innerHTML = '💡 Tip: Paste complete HTML artifact code here. Name will be auto-extracted from &lt;title&gt; tag.';
        htmlTextarea.parentNode.appendChild(hint);
    }
    
    // Preview link enhancement
    const previewLinks = document.querySelectorAll('a[href*="/tools/"]');
    previewLinks.forEach(link => {
        if (link.textContent.includes('View Tool')) {
            link.style.cssText = 'background: #28a745; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;';
        }
    });
});

// Add live character count for HTML field
function addCharacterCount() {
    const htmlTextarea = document.querySelector('#id_html_content');
    if (htmlTextarea) {
        const counter = document.createElement('div');
        counter.style.cssText = 'text-align: right; font-size: 11px; color: #666; margin-top: 2px;';
        
        function updateCount() {
            const count = htmlTextarea.value.length;
            counter.textContent = `${count.toLocaleString()} characters`;
            
            if (count > 50000) {
                counter.style.color = '#d63384';
            } else if (count > 25000) {
                counter.style.color = '#fd7e14';
            } else {
                counter.style.color = '#666';
            }
        }
        
        htmlTextarea.addEventListener('input', updateCount);
        htmlTextarea.parentNode.appendChild(counter);
        updateCount();
    }
}

// Initialize character count when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addCharacterCount);
} else {
    addCharacterCount();
}