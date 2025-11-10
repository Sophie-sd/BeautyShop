document.addEventListener('DOMContentLoaded', function() {
    const deliveryMethodSelect = document.getElementById('delivery_method');
    const deliveryCityInput = document.getElementById('delivery_city');
    const deliveryTypeSelect = document.getElementById('delivery_type');
    const deliveryAddressInput = document.getElementById('delivery_address');
    const deliveryTypeWrapper = document.querySelector('.delivery-type-wrapper');
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
    
    const PICKUP_ADDRESS = 'Україна, Черкаська область, м.Монастирище, вул. Соборна 126Д';
    
    function updateDeliveryFields() {
        const deliveryMethod = deliveryMethodSelect.value;
        
        deliveryCityInput.parentElement.style.display = 'none';
        deliveryTypeWrapper.style.display = 'none';
        deliveryAddressWrapper.style.display = 'none';
        cityResultsContainer.style.display = 'none';
        warehouseResultsContainer.style.display = 'none';
        pickupInfo.style.display = 'none';
        deliveryAddressInput.style.display = 'block';
        
        deliveryCityInput.value = '';
        deliveryAddressInput.value = '';
        deliveryTypeSelect.value = '';
        npCityRefInput.value = '';
        npWarehouseRefInput.value = '';
        selectedCityRef = '';
        
        deliveryCityInput.removeAttribute('required');
        deliveryAddressInput.removeAttribute('required');
        deliveryTypeSelect.removeAttribute('required');
        
        if (deliveryMethod === 'nova_poshta') {
            deliveryCityInput.parentElement.style.display = 'block';
            deliveryTypeWrapper.style.display = 'block';
            deliveryAddressWrapper.style.display = 'block';
            
            deliveryCityInput.setAttribute('required', 'required');
            deliveryTypeSelect.setAttribute('required', 'required');
            deliveryAddressInput.setAttribute('required', 'required');
            
            deliveryAddressLabel.textContent = 'Відділення/Поштомат *';
            deliveryCityInput.placeholder = 'Почніть вводити назву міста...';
            deliveryAddressInput.placeholder = 'Оберіть відділення або поштомат зі списку нижче';
            deliveryAddressInput.readOnly = true;
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
        } else if (deliveryMethod === 'courier') {
            deliveryCityInput.parentElement.style.display = 'block';
            deliveryAddressWrapper.style.display = 'block';
            
            deliveryCityInput.setAttribute('required', 'required');
            deliveryAddressInput.setAttribute('required', 'required');
            
            deliveryAddressLabel.textContent = 'Адреса *';
            deliveryCityInput.placeholder = 'Місто доставки';
            deliveryAddressInput.placeholder = 'Вулиця, будинок, квартира';
            deliveryAddressInput.readOnly = false;
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
        deliveryCityInput.value = city.mainDescription;
        npCityRefInput.value = city.ref;
        selectedCityRef = city.ref;
        cityResultsContainer.style.display = 'none';
        
        deliveryAddressInput.value = '';
        npWarehouseRefInput.value = '';
        warehouseResultsContainer.innerHTML = '';
        warehouseResultsContainer.style.display = 'none';
        
        if (deliveryTypeSelect.value) {
            loadWarehouses();
        }
    }
    
    function loadWarehouses() {
        if (!selectedCityRef) return;
        
        const warehouseType = deliveryTypeSelect.value;
        
        warehouseResultsContainer.innerHTML = '<div class="loading">Завантаження...</div>';
        warehouseResultsContainer.style.display = 'block';
        
        fetch(`/orders/np/get-warehouses/?city_ref=${encodeURIComponent(selectedCityRef)}&type=${warehouseType}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.warehouses.length > 0) {
                    warehouseResultsContainer.innerHTML = '';
                    data.warehouses.forEach(warehouse => {
                        const item = document.createElement('div');
                        item.className = 'warehouse-item';
                        item.innerHTML = `
                            <div class="warehouse-number">#${warehouse.number}</div>
                            <div class="warehouse-address">${warehouse.description}</div>
                        `;
                        item.dataset.ref = warehouse.ref;
                        item.dataset.description = warehouse.description;
                        item.addEventListener('click', function() {
                            selectWarehouse(warehouse);
                        });
                        warehouseResultsContainer.appendChild(item);
                    });
                } else {
                    warehouseResultsContainer.innerHTML = '<div class="no-results">Відділення не знайдено</div>';
                }
            })
            .catch(error => {
                console.error('Помилка завантаження відділень:', error);
                warehouseResultsContainer.innerHTML = '<div class="error">Помилка завантаження</div>';
            });
    }
    
    function selectWarehouse(warehouse) {
        deliveryAddressInput.value = warehouse.description;
        npWarehouseRefInput.value = warehouse.ref;
        
        const selectedItems = warehouseResultsContainer.querySelectorAll('.warehouse-item');
        selectedItems.forEach(item => item.classList.remove('selected'));
        
        const selectedItem = warehouseResultsContainer.querySelector(`[data-ref="${warehouse.ref}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }
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
    
    deliveryTypeSelect.addEventListener('change', function() {
        deliveryAddressInput.value = '';
        npWarehouseRefInput.value = '';
        warehouseResultsContainer.innerHTML = '';
        
        const selectedType = deliveryTypeSelect.value;
        if (selectedType === 'warehouse') {
            deliveryAddressLabel.textContent = 'Відділення *';
        } else if (selectedType === 'postomat') {
            deliveryAddressLabel.textContent = 'Поштомат *';
        } else {
            deliveryAddressLabel.textContent = 'Відділення/Поштомат *';
        }
        
        if (selectedCityRef && selectedType) {
            loadWarehouses();
        } else if (!selectedCityRef) {
            warehouseResultsContainer.innerHTML = '<div class="loading">Спочатку оберіть місто</div>';
            warehouseResultsContainer.style.display = 'block';
        } else {
            warehouseResultsContainer.style.display = 'none';
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#delivery_city') && !e.target.closest('#city_results')) {
            cityResultsContainer.style.display = 'none';
        }
    });
    
    updateDeliveryFields();
});

