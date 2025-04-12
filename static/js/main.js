// Main JavaScript for BITS Confessions Bot

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Highlight search terms in results
    highlightSearchTerms();
    
    // Category card click handler
    setupCategoryCards();
    
    // Mobile category dropdown handler
    setupMobileCategoryDropdown();
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

/**
 * Highlights search terms in confession text
 */
function highlightSearchTerms() {
    const searchQuery = document.getElementById('search-query');
    
    if (!searchQuery) {
        return;
    }
    
    const query = searchQuery.textContent.trim();
    if (!query) {
        return;
    }
    
    const terms = query.toLowerCase().split(/\s+/).filter(term => term.length > 3);
    
    const confessions = document.querySelectorAll('.confession-text');
    
    confessions.forEach(confession => {
        let text = confession.innerHTML;
        
        // Highlight each term
        terms.forEach(term => {
            if (term) {
                const regex = new RegExp('(' + term + ')', 'gi');
                text = text.replace(regex, '<span class="highlight">$1</span>');
            }
        });
        
        confession.innerHTML = text;
    });
}

/**
 * Sets up category cards to filter search
 */
function setupCategoryCards() {
    const categoryCards = document.querySelectorAll('.category-card');
    
    categoryCards.forEach(card => {
        card.addEventListener('click', function() {
            const categoryId = this.dataset.categoryId;
            const categoryName = this.dataset.categoryName;
            
            // Update hidden input in search form
            const categoryInput = document.getElementById('category-input');
            if (categoryInput) {
                categoryInput.value = categoryId;
            }
            
            // Update dropdown button text if exists
            const dropdownButton = document.getElementById('category-dropdown');
            if (dropdownButton) {
                dropdownButton.innerHTML = `Category: ${categoryName} <span class="caret"></span>`;
            }
            
            // Optional: Submit form automatically
            // document.getElementById('search-form').submit();
        });
    });
}

/**
 * Sets up mobile category dropdown
 */
function setupMobileCategoryDropdown() {
    const dropdownItems = document.querySelectorAll('.category-dropdown-item');
    
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const categoryId = this.dataset.categoryId;
            const categoryName = this.dataset.categoryName;
            
            // Update hidden input
            const categoryInput = document.getElementById('category-input');
            if (categoryInput) {
                categoryInput.value = categoryId;
            }
            
            // Update dropdown text
            const dropdownButton = document.getElementById('category-dropdown');
            if (dropdownButton) {
                dropdownButton.innerHTML = `Category: ${categoryName} <span class="caret"></span>`;
            }
        });
    });
}
