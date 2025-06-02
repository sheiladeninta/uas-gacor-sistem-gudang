from app import app
from models import User, db
from werkzeug.security import generate_password_hash

def seed_users():
    with app.app_context():
        # Hapus semua data user yang ada (opsional)
        User.query.delete()
        
        # Data user yang akan ditambahkan
        users = [
            {
                'user_id': 1202223144,
                'nama': 'lala',
                'password': 'staff123'
            },
            {
                'user_id': 1202223324,
                'nama': 'sheila',
                'password': 'staff123'
            },
            {
                'user_id': 1202220266,
                'nama': 'yoga',
                'password': 'staff123'
            },
            {
                'user_id': 1202220123,
                'nama': 'fajar',
                'password': 'staff123'
            },
            {
                'user_id': 1202223029,
                'nama': 'naza',
                'password': 'staff123'
            }
        ]
        
        try:
            # Tambahkan user ke database
            for user_data in users:
                user = User(
                    user_id=user_data['user_id'],
                    nama=user_data['nama'],
                    password=generate_password_hash(user_data['password'])
                )
                db.session.add(user)
            
            db.session.commit()
            print("Data user berhasil ditambahkan!")
        except Exception as e:
            db.session.rollback()
            print(f"Terjadi kesalahan: {str(e)}")

if __name__ == '__main__':
    seed_users() 