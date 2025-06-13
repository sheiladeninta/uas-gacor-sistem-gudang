from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import datetime
from config import Config
from models import db, QualityControl
import requests

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/api/qc/submit', methods=['POST'])
def submit_qc():
    """Submit QC result for an item"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['inventory_log_id', 'item_code', 'name', 'status']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate status
        status_map = {
            'lulus': 'approved',
            'gagal': 'rejected'
        }
        status = status_map.get(data['status'].lower(), data['status'])
        if status not in ['approved', 'rejected']:
            return jsonify({'error': 'Invalid status. Must be approved or rejected'}), 400
            
        # If status is rejected, notes is required
        if status == 'rejected' and not data.get('notes', '').strip():
            return jsonify({'error': 'Notes is required when status is rejected'}), 400
            
        # Create QC result
        qc_result = QualityControl(
            inventory_log_id=data['inventory_log_id'],
            item_code=data['item_code'],
            name=data['name'],
            status=status,
            notes=data.get('notes'),
            checked_at=datetime.utcnow()
        )
        
        db.session.add(qc_result)
        db.session.commit()
        
        # Notify inventory service
        try:
            response = requests.post(
                f'http://localhost:5001/api/items/{data["item_code"]}/qc-result',
                json={
                    'status': status,
                    'notes': data.get('notes'),
                    'checked_at': qc_result.checked_at.isoformat()
                }
            )
            if response.status_code != 200:
                print(f"Warning: Failed to notify inventory service: {response.text}")
        except Exception as e:
            print(f"Warning: Failed to notify inventory service: {str(e)}")
        
        return jsonify({
            'message': 'QC result submitted successfully',
            'data': {
                **qc_result.to_dict(),
                'status_text': 'Lulus' if status == 'approved' else 'Gagal'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/qc/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics including total, passed, failed and pending items"""
    try:
        # Get date range from query params for filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query
        query = QualityControl.query
        
        # Apply date filters if provided
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(QualityControl.checked_at >= start)
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(QualityControl.checked_at <= end)
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400

        # Get counts for different statuses
        total = query.count()
        passed = query.filter_by(status='approved').count()
        failed = query.filter_by(status='rejected').count()
        
        # Get pending items count from inventory service
        try:
            response = requests.get('http://localhost:5001/api/items/pending-qc')
            if response.status_code == 200:
                pending_items = len(response.json())
            else:
                pending_items = 0
        except:
            pending_items = 0
        
        return jsonify({
            'total_items': total,
            'passed_qc': passed,
            'failed_qc': failed,
            'pending_qc': pending_items,
            'pass_rate': round((passed / total * 100) if total > 0 else 0, 2),
            'fail_rate': round((failed / total * 100) if total > 0 else 0, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/qc/items', methods=['GET'])
def list_qc_items():
    """Get all QC items with filters"""
    try:
        # Get filter parameters
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        # Base query
        query = QualityControl.query
        
        # Apply filters
        if status and status.lower() != 'semua':
            status_map = {
                'lulus': 'approved',
                'gagal': 'rejected',
                'pending': 'pending'
            }
            query = query.filter_by(status=status_map.get(status.lower(), status))
            
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(QualityControl.checked_at >= start)
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
                
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(QualityControl.checked_at <= end)
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400
                
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    QualityControl.item_code.ilike(search_term),
                    QualityControl.name.ilike(search_term)
                )
            )
            
        # Execute query
        items = query.order_by(QualityControl.checked_at.desc()).all()
        return jsonify([{
            **item.to_dict(),
            'tanggal_masuk': item.checked_at.strftime('%Y-%m-%d %H:%M:%S') if item.checked_at else None,
            'status_text': 'Lulus' if item.status == 'approved' else 'Gagal' if item.status == 'rejected' else 'Pending'
        } for item in items]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
