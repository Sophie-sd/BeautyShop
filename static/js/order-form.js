document.addEventListener('DOMContentLoaded', function() {
    const deliveryMethodSelect = document.getElementById('delivery_method');
    const deliveryCityInput = document.getElementById('delivery_city');
    const deliveryTypeInput = document.getElementById('delivery_type');
    const deliveryAddressInput = document.getElementById('delivery_address');
    const deliveryAddressWrapper = document.querySelector('.delivery-address-wrapper');
    const cityResultsContainer = document.getElementById('city_results');
    const warehouseResultsContainer = document.getElementById('warehouse_results');
    const npCityRefInput = document.getElementById('np_city_ref');
    const npWarehouseRefInput = document.getElementById('np_warehouse_ref');
    const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
    const deliveryAddressLabel = document.getElementById('delivery_address_label');
    const pickupInfo = document.getElementById('pickup_info');
    
    let selectedCityRef = '';
    let searchTimeout = null;
    let allWarehouses = [];
    
    const PICKUP_ADDRESS = 'Україна, Черкаська область, м.Монастирище, вул. Соборна 126Д';
    
    function updateDeliveryFields() {
        const deliveryMethod = deliveryMethodSelect.value;
        
        deliveryCityInput.parentElement.style.display = 'none';
        deliveryAddressWrapper.style.display = 'none';
        cityResultsContainer.style.display = 'none';
        warehouseResultsContainer.style.display = 'none';
        warehouseResultsContainer.innerHTML = '';
        pickupInfo.style.display = 'none';
        deliveryAddressInput.style.display = 'block';
        
        deliveryCityInput.value = '';
        deliveryAddressInput.value = '';
        deliveryTypeInput.value = '';
        npCityRefInput.value = '';
        npWarehouseRefInput.value = '';
        selectedCityRef = '';
        allWarehouses = [];
        
        deliveryCityInput.removeAttribute('required');
        deliveryAddressInput.removeAttribute('required');
        
        if (deliveryMethod === 'nova_poshta') {
            deliveryCityInput.parentElement.style.display = 'block';
            deliveryAddressWrapper.style.display = 'block';
            
            deliveryCityInput.setAttribute('required', 'required');
            deliveryAddressInput.setAttribute('required', 'required');
            
            deliveryAddressLabel.textContent = 'Відділення/Поштомат *';
            deliveryCityInput.placeholder = 'Почніть вводити назву міста...';
            deliveryAddressInput.placeholder = 'Введіть номер або адресу для пошуку';
            deliveryAddressInput.readOnly = false;
        } else if (deliveryMethod === 'ukrposhta') {
            deliveryCityInput.parentElement.style.display = 'block';
            deliveryAddressWrapper.style.display = 'block';
            
            deliveryCityInput.setAttribute('required', 'required');
            deliveryAddressInput.setAttribute('required', 'required');
            
            deliveryAddressLabel.textContent = 'Адреса *';
            deliveryCityInput.placeholder = 'Місто доставки';
            deliveryAddressInput.placeholder = 'Введіть адресу або індекс відділення';
            deliveryAddressInput.readOnly = false;
        } else if (deliveryMethod === 'pickup') {
            deliveryAddressWrapper.style.display = 'block';
            deliveryAddressInput.style.display = 'none';
            pickupInfo.style.display = 'block';
            deliveryAddressInput.value = PICKUP_ADDRESS;
            deliveryCityInput.value = 'Монастирище';
        }
        
        updatePaymentOptions();
    }
    
    function updatePaymentOptions() {
        const deliveryMethod = deliveryMethodSelect.value;
        
        paymentMethodRadios.forEach(radio => {
            const paymentOption = radio.closest('.payment-method');
            if (!paymentOption) return;
            
            if (deliveryMethod === 'nova_poshta' || deliveryMethod === 'ukrposhta') {
                if (radio.value === 'cash') {
                    paymentOption.style.display = 'block';
                    radio.parentElement.querySelector('span').textContent = 'Оплата при отриманні';
                } else if (radio.value === 'liqpay') {
                    paymentOption.style.display = 'block';
                } else {
                    paymentOption.style.display = 'none';
                }
            } else {
                paymentOption.style.display = 'block';
                if (radio.value === 'cash') {
                    if (deliveryMethod === 'pickup') {
                        radio.parentElement.querySelector('span').textContent = 'Оплата при отриманні (самовивіз)';
                    } else {
                        radio.parentElement.querySelector('span').textContent = 'Оплата при отриманні';
                    }
                }
            }
        });
        
        const checkedRadio = document.querySelector('input[name="payment_method"]:checked');
        if (checkedRadio && checkedRadio.closest('.payment-method').style.display === 'none') {
            const visibleRadio = document.querySelector('input[name="payment_method"]:not([style*="display: none"])');
            if (visibleRadio) {
                visibleRadio.checked = true;
            }
        }
    }
    
    function searchCities(query) {
        if (query.length < 2) {
            cityResultsContainer.style.display = 'none';
            return;
        }
        
        fetch(`/orders/np/search-cities/?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.cities.length > 0) {
                    cityResultsContainer.innerHTML = '';
                    data.cities.forEach(city => {
                        const item = document.createElement('div');
                        item.className = 'autocomplete-item';
                        item.textContent = city.present;
                        item.dataset.ref = city.ref;
                        item.addEventListener('click', function() {
                            selectCity(city);
                        });
                        cityResultsContainer.appendChild(item);
                    });
                    cityResultsContainer.style.display = 'block';
                } else {
                    cityResultsContainer.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Помилка пошуку міст:', error);
                cityResultsContainer.style.display = 'none';
            });
    }
    
    function selectCity(city) {
        console.log('Місто обрано:', city);
        deliveryCityInput.value = city.mainDescription;
        npCityRefInput.value = city.ref;
        selectedCityRef = city.ref;
        cityResultsContainer.style.display = 'none';
        
        deliveryAddressInput.value = '';
        npWarehouseRefInput.value = '';
        warehouseResultsContainer.innerHTML = '';
        
        console.log('Викликаємо loadWarehouses');
        loadWarehouses();
    }
    
    function loadWarehouses() {
        if (!selectedCityRef) {
            console.warn('loadWarehouses: selectedCityRef порожній');
            return;
        }
        
        console.log('loadWarehouses викликано для міста:', selectedCityRef);
        
        warehouseResultsContainer.innerHTML = '<div class="loading">Завантаження відділень...</div>';
        warehouseResultsContainer.style.display = 'block';
        
        const url = `/orders/np/get-warehouses/?city_ref=${encodeURIComponent(selectedCityRef)}&type=`;
        console.log('Запит до:', url);
        
        fetch(url)
            .then(response => {
                console.log('Відповідь отримано:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Дані отримано:', data);
                if (data.success && data.warehouses && data.warehouses.length > 0) {
                    allWarehouses = data.warehouses;
                    console.log(`Завантажено ${data.warehouses.length} відділень та поштоматів`);
                    displayWarehouses(allWarehouses);
                } else {
                    console.warn('Відділення не знайдено або порожній масив');
                    warehouseResultsContainer.innerHTML = '<div class="no-results">Відділення не знайдено</div>';
                }
            })
            .catch(error => {
                console.error('Помилка завантаження відділень:', error);
                warehouseResultsContainer.innerHTML = '<div class="error">Помилка завантаження</div>';
            });
    }
    
    function displayWarehouses(warehouses) {
        warehouseResultsContainer.innerHTML = '';
        
        if (warehouses.length === 0) {
            warehouseResultsContainer.innerHTML = '<div class="no-results">Нічого не знайдено</div>';
            warehouseResultsContainer.style.display = 'block';
            return;
        }
        
        warehouses.forEach(warehouse => {
            const item = document.createElement('div');
            item.className = 'warehouse-item';
            
            const warehouseType = warehouse.categoryOfWarehouse === 'Postomat' ? 'Поштомат' : 'Відділення';
            
            item.innerHTML = `
                <div class="warehouse-number">${warehouseType} #${warehouse.number}</div>
                <div class="warehouse-address">${warehouse.description}</div>
            `;
            item.dataset.ref = warehouse.ref;
            item.dataset.description = warehouse.description;
            item.dataset.type = warehouse.categoryOfWarehouse === 'Postomat' ? 'postomat' : 'warehouse';
            item.addEventListener('click', function() {
                selectWarehouse(warehouse);
            });
            warehouseResultsContainer.appendChild(item);
        });
        
        warehouseResultsContainer.style.display = 'block';
    }
    
    function filterWarehouses(searchText) {
        if (!searchText || searchText.length < 1) {
            displayWarehouses(allWarehouses);
            return;
        }
        
        const searchLower = searchText.toLowerCase();
        const filtered = allWarehouses.filter(warehouse => {
            return warehouse.number.toString().includes(searchLower) ||
                   warehouse.description.toLowerCase().includes(searchLower) ||
                   warehouse.shortAddress.toLowerCase().includes(searchLower);
        });
        
        console.log(`Фільтрація: знайдено ${filtered.length} з ${allWarehouses.length}`);
        displayWarehouses(filtered);
    }
    
    function selectWarehouse(warehouse) {
        const warehouseType = warehouse.categoryOfWarehouse === 'Postomat' ? 'Поштомат' : 'Відділення';
        deliveryAddressInput.value = `${warehouseType} №${warehouse.number}: ${warehouse.description}`;
        npWarehouseRefInput.value = warehouse.ref;
        deliveryTypeInput.value = warehouse.categoryOfWarehouse === 'Postomat' ? 'postomat' : 'warehouse';
        
        warehouseResultsContainer.style.display = 'none';
        
        console.log('Обрано:', {
            type: deliveryTypeInput.value,
            ref: warehouse.ref,
            address: deliveryAddressInput.value
        });
    }
    
    deliveryMethodSelect.addEventListener('change', updateDeliveryFields);
    
    deliveryCityInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (deliveryMethodSelect.value === 'nova_poshta') {
            searchTimeout = setTimeout(() => {
                searchCities(query);
            }, 300);
        }
    });
    
    deliveryAddressInput.addEventListener('input', function() {
        const searchText = this.value.trim();
        
        if (deliveryMethodSelect.value === 'nova_poshta' && allWarehouses.length > 0) {
            filterWarehouses(searchText);
        }
    });
    
    deliveryAddressInput.addEventListener('focus', function() {
        if (deliveryMethodSelect.value === 'nova_poshta' && allWarehouses.length > 0) {
            const searchText = this.value.trim();
            filterWarehouses(searchText);
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#delivery_city') && !e.target.closest('#city_results')) {
            cityResultsContainer.style.display = 'none';
        }
        
        if (!e.target.closest('#delivery_address') && !e.target.closest('#warehouse_results')) {
            warehouseResultsContainer.style.display = 'none';
        }
    });
    
    updateDeliveryFields();
    
    const paymentFailedToast = document.getElementById('paymentFailedToast');
    if (paymentFailedToast && paymentFailedToast.dataset.show === 'true') {
        setTimeout(function() {
            paymentFailedToast.classList.add('cart-toast-show');
        }, 100);
        
        setTimeout(function() {
            paymentFailedToast.classList.remove('cart-toast-show');
        }, 6000);
    }
    
    const orderForm = document.querySelector('.order-form');
    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            const phoneInput = document.getElementById('phone');
            if (phoneInput && phoneInput.value) {
                let phoneValue = phoneInput.value.trim().replace(/\D/g, '');
                if (phoneValue.startsWith('38') && phoneValue.length === 12) {
                    phoneInput.value = '+' + phoneValue;
                } else if (phoneValue.length === 10) {
                    phoneInput.value = '+38' + phoneValue;
                }
            }
        });
    }
});

