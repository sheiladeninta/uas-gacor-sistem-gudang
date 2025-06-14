# routes/client_routes.py
from flask import Blueprint, render_template, jsonify, request, session, flash, redirect, url_for
from services.procurement_service import ProcurementService
from functools import wraps

client_bp = Blueprint('client', __name__, url_prefix='/client')
procurement_service = ProcurementService()

def client_required(f):
    """Decorator untuk memastikan user adalah client"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication untuk testing - comment out untuk production
        return f(*args, **kwargs)
        
        # Uncomment dibawah ini untuk enable authentication
        # if 'user_type' not in session or session['user_type'] != 'client':
        #     return redirect(url_for('auth.login'))
        # return f(*args, **kwargs)
    return decorated_function

@client_bp.route('/order/list-needs')
@client_required
def list_needs():
    """
    Menampilkan halaman daftar kebutuhan bahan makanan
    """
    procurement_data = procurement_service.get_procurement_list()
    
    if procurement_data is None:
        procurement_data = []

    # Optional: log data buat debug
    # print(procurement_data)

    return render_template(
        'order/client/list-needs.html',
        procurements=procurement_data
    )

@client_bp.route('/api/procurement-needs')
@client_required
def get_procurement_needs():
    """
    API endpoint untuk mengambil data procurement needs
    """
    try:
        # Ambil data dari API resto
        procurement_data = procurement_service.get_procurement_list()
        
        if procurement_data is None:
            return jsonify({
                'success': False,
                'message': 'Failed to fetch procurement data',
                'data': []
            }), 500
            
        # Filter hanya yang masih dibutuhkan
        needs = procurement_service.filter_procurement_needs(procurement_data)
        
        # Format data untuk frontend
        formatted_needs = []
        for need in needs:
            formatted_needs.append({
                'id': need.get('id'),
                'item_name': need.get('item_name', 'N/A'),
                'quantity': need.get('quantity', 0),
                'unit': need.get('unit', 'pcs'),
                'priority': need.get('priority', 'normal'),
                'needed_date': need.get('needed_date', ''),
                'description': need.get('description', ''),
                'status': need.get('status', 'pending'),
                'restaurant_name': need.get('restaurant_name', 'Unknown'),
                'created_at': need.get('created_at', '')
            })
            
        return jsonify({
            'success': True,
            'message': 'Data retrieved successfully',
            'data': formatted_needs,
            'total': len(formatted_needs)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'data': []
        }), 500

@client_bp.route('/api/procurement-needs/<int:need_id>')
@client_required
def get_procurement_detail(need_id):
    """
    API endpoint untuk mengambil detail procurement need
    """
    try:
        detail = procurement_service.get_procurement_by_id(need_id)
        
        if detail is None:
            return jsonify({
                'success': False,
                'message': 'Procurement need not found'
            }), 404
            
        return jsonify({
            'success': True,
            'data': detail
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500