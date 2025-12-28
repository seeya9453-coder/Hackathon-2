from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import random
import firebase_admin
from firebase_admin import credentials, firestore
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cyberpunk_secret_key_very_secure_12345')

# CORS Configuration for Netlify frontend
CORS(app, 
     supports_credentials=True,
     origins=[
         "https://cyberverseeeeee.netlify.app", 
         "http://localhost:*",
         "http://127.0.0.1:*"
     ],
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS"])

# --- Firebase Initialization ---
firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
if firebase_creds:
    try:
        cred_dict = json.loads(firebase_creds)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin Initialized from Env Var")
    except Exception as e:
        print(f"❌ Error initializing Firebase from Env Var: {e}")
else:
    print("⚠️ WARNING: No FIREBASE_CREDENTIALS env var found.")

db = firestore.client() if firebase_admin._apps else None

# --- Mock Data Generation ---
def create_mock_data():
    if not db: return

    cafes_ref = db.collection('cafes')
    if len(list(cafes_ref.limit(1).stream())) > 0:
        return

    print("🌱 Seeding Database with Mock Data...")

    areas = ['Andheri', 'Bandra', 'Powai', 'Juhu', 'Colaba']
    cafe_names = ['Neon Nexus', 'Cyber Hive', 'Glitch Gaming', 'Vertex Lounge', 'Obsidian Den', 
                  'Pixel Point', 'Matrix Zone', 'Netrunner Hub', 'Synthetix', 'Void Café',
                  'Bit Bunker', 'Circuit City', 'Holo Haven', 'Quantum Quay', 'Zion Gate']
    
    pc_games = ["Valorant", "CS2", "Dota 2", "League of Legends", "Fortnite", "PUBG", "Age of Empires"]
    ps5_games = ["Warzone", "Apex Legends", "FIFA 24", "GTA V", "Spider-Man", "Tekken 8"]
    
    unique_images = [
        "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1593508512255-86ab42a8e620?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1612287230217-9694659afa18?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1574375927938-d5a98e8efe30?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1605901309584-818e25960b8f?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1628143229871-70d592473461?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1589241062272-c0a000072dfa?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1551103782-8ab07afd45c1?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1598550476439-cce86041e880?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1650392305713-fbce880628e9?auto=format&fit=crop&w=800&q=80"
    ]
    random.shuffle(unique_images)
    num_cafes = min(len(cafe_names), len(unique_images))

    for i in range(num_cafes): 
        all_games = ", ".join(random.sample(pc_games, 4) + random.sample(ps5_games, 2))
        c_name = cafe_names[i]
        
        cafe_data = {
            'name': c_name,
            'area': random.choice(areas),
            'price_per_hour': random.choice([150, 200, 250, 300, 400]),
            'rating': round(random.uniform(3.5, 5.0), 1),
            'distance_km': round(random.uniform(0.5, 15.0), 1),
            'image_url': unique_images[i],
            'logo_url': f"https://robohash.org/{c_name.replace(' ', '')}?set=set1&bgset=bg1",
            'travel_info': f"{random.choice(['Near', 'Opposite', 'Behind', 'Next to'])} {random.choice(['Metro Station', 'City Mall', 'Bus Depot', 'Central Park', 'Tech Plaza'])} ({random.randint(2, 10)} min walk)",
            'specs': f"RTX {random.choice(['3060', '3080', '4090'])}, {random.choice(['144Hz', '240Hz'])} Monitors",
            'games': all_games
        }
        db.collection('cafes').add(cafe_data)
    
    users_ref = db.collection('users')
    if len(list(users_ref.where('email', '==', 'demo@cyber.com').stream())) == 0:
        demo_user = {
            'username': 'NetRunner',
            'email': 'demo@cyber.com',
            'password_hash': 'password',
            'phone': '9876543210'
        }
        db.collection('users').add(demo_user)
    print("✅ Mock data created!")

# --- Routes ---
@app.route('/')
def index():
    return jsonify({
        'status': 'online',
        'message': 'CYBERVERSE API is running',
        'endpoints': ['/api/auth/login', '/api/auth/signup', '/api/cafes', '/api/cafe/<id>', '/api/book']
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'database': 'connected' if db else 'disconnected'})

# -- API: Auth --
@app.route('/api/auth/login', methods=['POST'])
def login():
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        users = db.collection('users').where('email', '==', email).stream()
        user_doc = None
        for doc in users:
            user_doc = doc
            break
        
        if user_doc:
            user_data = user_doc.to_dict()
            if user_data.get('password_hash') == password:
                session['user_id'] = user_doc.id
                session.modified = True
                return jsonify({
                    'message': 'Login Successful', 
                    'user': {
                        'username': user_data.get('username'), 
                        'id': user_doc.id
                    }
                })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    data = request.json
    email = data.get('email')
    
    try:
        existing = list(db.collection('users').where('email', '==', email).stream())
        if len(existing) > 0:
            return jsonify({'error': 'Email already exists'}), 400
        
        new_user = {
            'username': data.get('username'),
            'email': email,
            'password_hash': data.get('password'),
            'phone': data.get('phone')
        }
        update_time, doc_ref = db.collection('users').add(new_user)
        
        session['user_id'] = doc_ref.id
        session.modified = True
        return jsonify({
            'message': 'Signup Successful', 
            'user': {
                'username': new_user['username'], 
                'id': doc_ref.id
            }
        })
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

# -- API: Cafes --
@app.route('/api/cafes')
def get_cafes():
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    area_filter = request.args.get('area', '')
    price_max = request.args.get('price_max', '1000')
    
    try:
        cafes_ref = db.collection('cafes')
        query = cafes_ref

        if area_filter and area_filter != 'All' and area_filter != '':
            query = query.where('area', '==', area_filter)
        
        docs = query.stream()
        result = []
        
        for doc in docs:
            c = doc.to_dict()
            c['id'] = doc.id
            
            if price_max and price_max != '1000':
                if c.get('price_per_hour', 9999) > int(price_max):
                    continue
                    
            result.append(c)
            
        return jsonify(result)
    except Exception as e:
        print(f"Get cafes error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cafe/<cafe_id>')
def get_cafe_details(cafe_id):
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    try:
        doc = db.collection('cafes').document(cafe_id).get()
        if not doc.exists:
            return jsonify({'error': 'Not found'}), 404
        
        cafe_data = doc.to_dict()
        cafe_data['id'] = doc.id
        
        reviews_ref = db.collection('reviews').where('cafe_id', '==', cafe_id).stream()
        reviews_list = []
        for r in reviews_ref:
            rd = r.to_dict()
            reviews_list.append({
                'user': rd.get('user_name'), 
                'rating': rd.get('rating'), 
                'comment': rd.get('comment')
            })
            
        cafe_data['reviews'] = reviews_list
        return jsonify(cafe_data)
    except Exception as e:
        print(f"Get cafe details error: {e}")
        return jsonify({'error': str(e)}), 500

# -- API: Reviews --
@app.route('/api/reviews', methods=['POST'])
def add_review():
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        user_id = session['user_id']
        
        user_doc = db.collection('users').document(user_id).get()
        user_name = "Unknown"
        if user_doc.exists:
            user_name = user_doc.to_dict().get('username')
        
        new_review = {
            'cafe_id': data['cafe_id'],
            'user_id': user_id,
            'rating': data['rating'],
            'comment': data['comment'],
            'user_name': user_name
        }
        db.collection('reviews').add(new_review)
        return jsonify({'message': 'Review posted'})
    except Exception as e:
        print(f"Add review error: {e}")
        return jsonify({'error': str(e)}), 500

# -- API: Booking --
@app.route('/api/book', methods=['POST'])
def create_booking():
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        
        cafe_doc = db.collection('cafes').document(data['cafe_id']).get()
        cafe_name = cafe_doc.to_dict().get('name') if cafe_doc.exists else "Unknown Cafe"

        new_booking = {
            'user_id': session['user_id'],
            'cafe_id': data['cafe_id'],
            'cafe_name': cafe_name,
            'date': data['date'],
            'time_slot': data['time_slot'],
            'duration_hours': float(data['duration']),
            'total_price': data['total_price'],
            'seat_number': f"PC-{random.randint(1, 20):02d}",
            'status': 'Confirmed'
        }
        
        update_time, doc_ref = db.collection('bookings').add(new_booking)
        
        return jsonify({
            'message': 'Booking Confirmed', 
            'booking_id': doc_ref.id, 
            'seat': new_booking['seat_number']
        })
    except Exception as e:
        print(f"Create booking error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/bookings')
def get_user_bookings():
    if not db:
        return jsonify({'error': 'Database not connected'}), 503
        
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        bookings = db.collection('bookings').where('user_id', '==', session['user_id']).stream()
        
        res = []
        for b in bookings:
            bd = b.to_dict()
            mapped = {
                'id': b.id,
                'cafe_name': bd.get('cafe_name'),
                'date': bd.get('date'),
                'time': bd.get('time_slot'),
                'duration': bd.get('duration_hours'),
                'price': bd.get('total_price'),
                'seat': bd.get('seat_number'),
                'status': bd.get('status')
            }
            res.append(mapped)
            
        return jsonify(res)
    except Exception as e:
        print(f"Get bookings error: {e}")
        return jsonify({'error': str(e)}), 500

# Initialize mock data on startup
try:
    if db: 
        create_mock_data()
        print("🚀 Server ready!")
except Exception as e:
    print(f"⚠️ Startup warning: {e}")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
