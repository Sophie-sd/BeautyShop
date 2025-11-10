class CatalogManager {
    constructor() {
        this.filtersForm = document.getElementById('filtersForm');
        this.init();
    }
    
    init() {
        this.cacheElements();
        this.bindEvents();
        this.initMobileFilters();
        this.setActiveSortFromURL();
    }
    
    cacheElements() {
        this.clearAllFiltersBtn = document.querySelectorAll('#clearAllFilters');
        this.applyFiltersBtn = document.getElementById('applyFiltersBtn');
        this.mobileFiltersBtn = document.getElementById('mobileFiltersBtn');
        this.mobileFiltersModal = document.getElementById('mobileFiltersModal');
        this.sortSelectBtn = document.getElementById('sortSelectBtn');
        this.sortDropdown = document.getElementById('sortDropdown');
        this.mobileFiltersClose = document.getElementById('mobileFiltersClose');
        this.desktopSortSelect = document.getElementById('desktopSortSelect');
    }
    
    bindEvents() {
        if (!this.filtersForm) return;
        
        const checkboxes = this.filtersForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.filtersForm.submit();
            });
        });
        
        const priceInputs = this.filtersForm.querySelectorAll('input[type="number"]');
        priceInputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.filtersForm.submit();
                }
            });
        });
        
        if (this.applyFiltersBtn) {
            this.applyFiltersBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.filtersForm.submit();
            });
        }
        
        this.clearAllFiltersBtn.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = window.location.pathname;
            });
        });
        
        if (this.desktopSortSelect) {
            this.desktopSortSelect.addEventListener('change', () => {
                const url = new URL(window.location);
                const value = this.desktopSortSelect.value;
                if (value && value !== 'default') {
                    url.searchParams.set('sort', value);
                } else {
                    url.searchParams.delete('sort');
                }
                url.searchParams.delete('page');
                window.location.href = url.toString();
            });
        }
            
        if (this.sortSelectBtn && this.sortDropdown) {
            this.sortSelectBtn.addEventListener('click', () => this.toggleSortDropdown());
            
            this.sortDropdown.addEventListener('click', (e) => {
                if (e.target.classList.contains('sort-option')) {
                    const value = e.target.dataset.value;
                    const text = e.target.textContent;
                    this.selectSortOption(value, text);
                }
            });
        }
        
        document.addEventListener('click', (e) => {
            if (this.sortSelectBtn && this.sortDropdown) {
                if (!this.sortSelectBtn.contains(e.target) && !this.sortDropdown.contains(e.target)) {
                    this.closeSortDropdown();
                }
            }
        });
    }
    
    setActiveSortFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const sortValue = urlParams.get('sort') || 'default';
        
        if (this.desktopSortSelect) {
            this.desktopSortSelect.value = sortValue;
        }
        
        if (this.sortDropdown) {
            const sortOption = this.sortDropdown.querySelector(`[data-value="${sortValue}"]`);
            if (sortOption) {
                this.sortDropdown.querySelectorAll('.sort-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                sortOption.classList.add('selected');
                
                const textSpan = this.sortSelectBtn?.querySelector('.sort-select-text');
                if (textSpan && sortValue !== 'default') {
                    textSpan.textContent = sortOption.textContent;
                }
            }
        }
    }
    
    toggleSortDropdown() {
        if (!this.sortDropdown || !this.sortSelectBtn) return;
        
        const isHidden = this.sortDropdown.classList.contains('hidden');
        
        if (isHidden) {
            this.sortDropdown.classList.remove('hidden');
            this.sortSelectBtn.classList.add('active');
        } else {
            this.closeSortDropdown();
        }
    }
    
    closeSortDropdown() {
        if (!this.sortDropdown || !this.sortSelectBtn) return;
        
        this.sortDropdown.classList.add('hidden');
        this.sortSelectBtn.classList.remove('active');
    }
    
    selectSortOption(value, text) {
        const textSpan = this.sortSelectBtn.querySelector('.sort-select-text');
        if (textSpan) {
            textSpan.textContent = text;
        }
        
        this.sortDropdown.querySelectorAll('.sort-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        const selectedOption = this.sortDropdown.querySelector(`[data-value="${value}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        const url = new URL(window.location);
        if (value && value !== 'default') {
            url.searchParams.set('sort', value);
        } else {
            url.searchParams.delete('sort');
        }
        url.searchParams.delete('page');
        
        window.location.href = url.toString();
        
        this.closeSortDropdown();
    }
    
    initMobileFilters() {
        if (!this.mobileFiltersBtn || !this.mobileFiltersModal) return;
        
        const modalBody = this.mobileFiltersModal.querySelector('.modal-filters__body');
        const closeBtn = this.mobileFiltersModal.querySelector('.modal-filters__close');
        const backdrop = this.mobileFiltersModal.querySelector('.modal-filters__backdrop');
        const applyBtn = this.mobileFiltersModal.querySelector('.modal-filters__apply');
        const clearBtn = this.mobileFiltersModal.querySelector('.modal-filters__clear');
        
        this.mobileFiltersBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.copyFiltersToModal();
            this.mobileFiltersModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            
            const firstInput = modalBody.querySelector('input, select');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        });
        
        const closeModal = () => {
            this.mobileFiltersModal.classList.add('hidden');
            document.body.style.overflow = '';
        };
        
        closeBtn?.addEventListener('click', closeModal);
        backdrop?.addEventListener('click', closeModal);
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.mobileFiltersModal.classList.contains('hidden')) {
                closeModal();
            }
        });
        
        applyBtn?.addEventListener('click', () => {
            this.copyFiltersFromModal();
            this.filtersForm.submit();
            closeModal();
        });
        
        clearBtn?.addEventListener('click', () => {
            window.location.href = window.location.pathname;
        });
    }
    
    copyFiltersToModal() {
        const modalBody = this.mobileFiltersModal.querySelector('.modal-filters__body');
        const filtersContent = document.querySelector('.filters-content');
        
        if (filtersContent && modalBody) {
            modalBody.innerHTML = filtersContent.innerHTML;
            
            modalBody.querySelectorAll('input, select').forEach(element => {
                const originalElement = document.getElementById(element.id);
                if (originalElement) {
                    if (element.type === 'checkbox') {
                        element.checked = originalElement.checked;
                    } else {
                        element.value = originalElement.value;
                    }
                }
            });
        }
    }
    
    copyFiltersFromModal() {
        const modalBody = this.mobileFiltersModal.querySelector('.modal-filters__body');
        
        modalBody.querySelectorAll('input, select').forEach(element => {
            const originalElement = document.getElementById(element.id);
            if (originalElement) {
                if (element.type === 'checkbox') {
                    originalElement.checked = element.checked;
                } else {
                    originalElement.value = element.value;
                }
            }
        });
    }
}

// Ініціалізація після завантаження DOM
document.addEventListener('DOMContentLoaded', () => {
    const catalog = new CatalogManager();
    
    // Експортуємо в глобальний простір для налагодження
    window.catalog = catalog;
});
