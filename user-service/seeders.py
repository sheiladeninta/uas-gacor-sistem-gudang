from models import db, User, UserRole

def seed_staff():
    # Daftar staff yang akan di-seed
    staff_list = [
        {
            'nama': 'admin',
            'username' : 'admin.gacor',
            'password': 'admin123',
            'email': 'admin@example.com',
            'role': UserRole.STAFF.value
        },
        {
            'nama': 'sheila',
            'username' : 'sheila.gacor',
            'password': 'sheila123',
            'email': 'sheila@example.com',
            'role': UserRole.STAFF.value
        }
    ]

    # Cek dan tambahkan staff jika belum ada
    for staff_data in staff_list:
        existing_staff = User.query.filter_by(nama=staff_data['nama']).first()
        if not existing_staff:
            staff = User(**staff_data)
            db.session.add(staff)
    
    db.session.commit()
    print("Staff data has been seeded successfully!") 