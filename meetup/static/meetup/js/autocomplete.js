/**
 * Location autocomplete using the Django backend
 * which proxies to Photon geocoder and Postcodes.io.
 */

function setupAutocomplete(inputEl, dropdownEl, onSelect) {
    var debounceTimer = null;
    var selectedIndex = -1;
    var currentResults = [];

    inputEl.addEventListener('input', function() {
        var query = inputEl.value.trim();
        clearTimeout(debounceTimer);

        if (query.length < 3) {
            hideDropdown();
            return;
        }

        debounceTimer = setTimeout(function() {
            fetchSuggestions(query);
        }, 300);
    });

    inputEl.addEventListener('keydown', function(e) {
        if (!dropdownEl.classList.contains('active')) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, currentResults.length - 1);
            highlightItem();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            highlightItem();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && selectedIndex < currentResults.length) {
                selectResult(currentResults[selectedIndex]);
            }
        } else if (e.key === 'Escape') {
            hideDropdown();
        }
    });

    inputEl.addEventListener('blur', function() {
        // Delay to allow click on dropdown item
        setTimeout(function() { hideDropdown(); }, 200);
    });

    function fetchSuggestions(query) {
        fetch('/meetup/api/autocomplete/?q=' + encodeURIComponent(query))
            .then(function(response) { return response.json(); })
            .then(function(data) {
                currentResults = data.results || [];
                selectedIndex = -1;
                renderDropdown();
            })
            .catch(function() {
                hideDropdown();
            });
    }

    function renderDropdown() {
        if (currentResults.length === 0) {
            hideDropdown();
            return;
        }

        dropdownEl.innerHTML = '';
        currentResults.forEach(function(result, idx) {
            var item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = result.label;
            item.addEventListener('mousedown', function(e) {
                e.preventDefault();
                selectResult(result);
            });
            dropdownEl.appendChild(item);
        });
        dropdownEl.classList.add('active');
    }

    function highlightItem() {
        var items = dropdownEl.querySelectorAll('.autocomplete-item');
        items.forEach(function(item, idx) {
            item.classList.toggle('selected', idx === selectedIndex);
        });
    }

    function selectResult(result) {
        inputEl.value = result.label;
        hideDropdown();
        onSelect(result);
    }

    function hideDropdown() {
        dropdownEl.classList.remove('active');
        dropdownEl.innerHTML = '';
        currentResults = [];
        selectedIndex = -1;
    }
}
