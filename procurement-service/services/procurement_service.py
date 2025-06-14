# services/procurement_service.py
import requests
from typing import List, Dict, Optional
import logging

class ProcurementService:
    def __init__(self):
        self.base_url = "https://1741-2404-8000-1024-8859-11b-7657-b8ee-8946.ngrok-free.app/api"
        self.headers = {
            'ngrok-skip-browser-warning': 'true',  # Skip ngrok warning page
            'Content-Type': 'application/json'
        }
        
    def get_procurement_list(self) -> Optional[List[Dict]]:
        """
        Mengambil daftar procurement/kebutuhan bahan dari API resto
        """
        try:
            response = requests.get(
                f"{self.base_url}/procurement",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else data.get('data', [])
            else:
                logging.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return None
            
    def get_procurement_by_id(self, procurement_id: int) -> Optional[Dict]:
        """
        Mengambil detail procurement berdasarkan ID
        """
        try:
            response = requests.get(
                f"{self.base_url}/procurement/{procurement_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"API Error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return None
            
    def filter_procurement_needs(self, procurement_list: List[Dict]) -> List[Dict]:
        """
        Filter hanya procurement yang statusnya masih dibutuhkan
        """
        if not procurement_list:
            return []
            
        return [
            item for item in procurement_list 
            if item.get('status', '').lower() in ['pending', 'needed', 'requested']
        ]