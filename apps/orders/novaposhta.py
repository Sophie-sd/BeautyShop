"""
API клієнт для роботи з Новою Поштою
"""
import requests
from django.conf import settings


class NovaPoshtaAPI:
    """Клас для роботи з API Нової Пошти"""
    
    API_URL = 'https://api.novaposhta.ua/v2.0/json/'
    API_KEY = '118c5e07e74e4d3c47590240014609fc'
    
    def __init__(self):
        self.api_key = self.API_KEY
    
    def _make_request(self, model, method, properties=None):
        """Базовий метод для запитів до API"""
        if properties is None:
            properties = {}
        
        data = {
            'apiKey': self.api_key,
            'modelName': model,
            'calledMethod': method,
            'methodProperties': properties
        }
        
        try:
            response = requests.post(self.API_URL, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                return result.get('data', [])
            else:
                errors = result.get('errors', [])
                print(f"Nova Poshta API Error: {errors}")
                return []
        except Exception as e:
            print(f"Nova Poshta Request Error: {e}")
            return []
    
    def search_cities(self, query):
        """Пошук міст за назвою"""
        properties = {
            'FindByString': query,
            'Limit': 20
        }
        cities = self._make_request('Address', 'getCities', properties)
        
        if not cities:
            return []
        
        result = []
        for city_data in cities:
            result.append({
                'ref': city_data.get('Ref', ''),
                'present': city_data.get('Description', ''),
                'mainDescription': city_data.get('Description', ''),
                'area': city_data.get('Area', ''),
                'region': city_data.get('SettlementType', '')
            })
        
        return result
    
    def get_warehouses(self, city_ref, warehouse_type=''):
        """Отримання відділень/поштоматів міста"""
        properties = {
            'CityRef': city_ref,
            'Limit': 500
        }
        
        if warehouse_type == 'postomat':
            properties['TypeOfWarehouseRef'] = '9a68df70-0267-42a8-bb5c-37f427e36ee4'
        
        warehouses = self._make_request('Address', 'getWarehouses', properties)
        
        result = []
        for warehouse in warehouses:
            warehouse_data = {
                'ref': warehouse.get('Ref', ''),
                'description': warehouse.get('Description', ''),
                'descriptionRu': warehouse.get('DescriptionRu', ''),
                'shortAddress': warehouse.get('ShortAddress', ''),
                'shortAddressRu': warehouse.get('ShortAddressRu', ''),
                'number': warehouse.get('Number', ''),
                'typeOfWarehouse': warehouse.get('TypeOfWarehouse', ''),
                'schedule': warehouse.get('Schedule', {}),
                'phone': warehouse.get('Phone', ''),
                'categoryOfWarehouse': warehouse.get('CategoryOfWarehouse', '')
            }
            result.append(warehouse_data)
        
        return result
    
    def get_delivery_cost(self, city_sender_ref, city_recipient_ref, weight, cost):
        """Розрахунок вартості доставки"""
        properties = {
            'CitySender': city_sender_ref,
            'CityRecipient': city_recipient_ref,
            'Weight': str(weight),
            'ServiceType': 'WarehouseWarehouse',
            'Cost': str(cost),
            'CargoType': 'Cargo',
            'SeatsAmount': '1'
        }
        
        result = self._make_request('InternetDocument', 'getDocumentPrice', properties)
        
        if result:
            return {
                'cost': result[0].get('Cost', 0),
                'costRedelivery': result[0].get('CostRedelivery', 0)
            }
        
        return {'cost': 0, 'costRedelivery': 0}

