from flask import Flask, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import random
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cybercafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'cyberpunk_secret_key'

CORS(app)
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))  # In real app, hash this!
    phone = db.Column(db.String(20))

class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(50), nullable=False)
    price_per_hour = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    logo_url = db.Column(db.String(200), nullable=True)
    travel_info = db.Column(db.String(200), nullable=True)
    specs = db.Column(db.String(200), nullable=True)
    games = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'area': self.area,
            'price_per_hour': self.price_per_hour,
            'rating': self.rating,
            'distance_km': self.distance_km,
            'image_url': self.image_url,
            'logo_url': self.logo_url,
            'travel_info': self.travel_info,
            'specs': self.specs,
            'games': self.games
        }

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafe.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    time_slot = db.Column(db.String(20), nullable=False) # HH:MM
    duration_hours = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Confirmed') # Confirmed, Cancelled

    cafe = db.relationship('Cafe')

    def to_dict(self):
        return {
            'id': self.id,
            'cafe_name': self.cafe.name,
            'date': self.date,
            'time': self.time_slot,
            'duration': self.duration_hours,
            'price': self.total_price,
            'seat': self.seat_number,
            'status': self.status
        }

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafe.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))
    user_name = db.Column(db.String(80)) # Denormalized for simplicity

# --- Mock Data Generation ---
def create_mock_data():
    if Cafe.query.first():
        return

    areas = ['Andheri', 'Bandra', 'Powai', 'Juhu', 'Colaba']
    cafe_names = ['Neon Nexus', 'Cyber Hive', 'Glitch Gaming', 'Vertex Lounge', 'Obsidian Den', 
                  'Pixel Point', 'Matrix Zone', 'Netrunner Hub', 'Synthetix', 'Void Café',
                  'Bit Bunker', 'Circuit City', 'Holo Haven', 'Quantum Quay', 'Zion Gate']
    
    # Games Lists
    pc_games = ["Valorant", "CS2", "Dota 2", "League of Legends", "Fortnite", "PUBG", "Age of Empires"]
    ps5_games = ["Warzone", "Apex Legends", "FIFA 24", "GTA V", "Spider-Man", "Tekken 8"]
    vr_games = ["Beat Saber", "Superhot", "Half-Life: Alyx"]
    
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
        
        cafe = Cafe(
            name=c_name,
            area=random.choice(areas),
            price_per_hour=random.choice([150, 200, 250, 300, 400]),
            rating=round(random.uniform(3.5, 5.0), 1),
            distance_km=round(random.uniform(0.5, 15.0), 1),
            image_url=unique_images[i],
            logo_url=f"https://robohash.org/{c_name.replace(' ', '')}?set=set1&bgset=bg1",
            travel_info=f"{random.choice(['Near', 'Opposite', 'Behind', 'Next to'])} {random.choice(['Metro Station', 'City Mall', 'Bus Depot', 'Central Park', 'Tech Plaza'])} ({random.randint(2, 10)} min walk)",
            specs=f"RTX {random.choice(['3060', '3080', '4090'])}, {random.choice(['144Hz', '240Hz'])} Monitors",
            games=all_games
        )
        db.session.add(cafe)
    
    # Create a Demo User
    if not User.query.filter_by(email='demo@cyber.com').first():
        demo_user = User(username='NetRunner', email='demo@cyber.com', password_hash='password', phone='9876543210')
        db.session.add(demo_user)

    db.session.commit()
    print("Mock data created!")

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

# -- API: Auth --
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.password_hash == data.get('password'):
        session['user_id'] = user.id
        return jsonify({'message': 'Login Successful', 'user': {'username': user.username, 'id': user.id}})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    new_user = User(
        username=data.get('username'),
        email=data.get('email'),
        password_hash=data.get('password'),
        phone=data.get('phone')
    )
    db.session.add(new_user)
    db.session.commit()
    session['user_id'] = new_user.id
    return jsonify({'message': 'Signup Successful', 'user': {'username': new_user.username, 'id': new_user.id}})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

# -- API: Cafes --
@app.route('/api/cafes')
def get_cafes():
    area_filter = request.args.get('area')
    price_max = request.args.get('price_max')
    
    query = Cafe.query
    
    if area_filter and area_filter != 'All' and area_filter != '':
        query = query.filter(Cafe.area == area_filter)
    
    if price_max and price_max != '1000': # Assuming 1000 is max on slider
        query = query.filter(Cafe.price_per_hour <= int(price_max))
        
    cafes = query.all()
    return jsonify([cafe.to_dict() for cafe in cafes])

@app.route('/api/cafe/<int:cafe_id>')
def get_cafe_details(cafe_id):
    cafe = Cafe.query.get_or_404(cafe_id)
    reviews = Review.query.filter_by(cafe_id=cafe_id).all()
    
    cafe_data = cafe.to_dict()
    cafe_data['reviews'] = [{'user': r.user_name, 'rating': r.rating, 'comment': r.comment} for r in reviews]
    return jsonify(cafe_data)

# -- API: Reviews --
@app.route('/api/reviews', methods=['POST'])
def add_review():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    # Get user name directly
    user = User.query.get(session['user_id'])
    
    new_review = Review(
        cafe_id=data['cafe_id'],
        user_id=session['user_id'],
        rating=data['rating'],
        comment=data['comment'],
        user_name=user.username
    )
    db.session.add(new_review)
    db.session.commit()
    return jsonify({'message': 'Review posted'})

# -- API: Booking --
@app.route('/api/book', methods=['POST'])
def create_booking():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Mock Availability Check
    # In real app, check if seat is taken
    
    new_booking = Booking(
        user_id=session['user_id'],
        cafe_id=data['cafe_id'],
        date=data['date'],
        time_slot=data['time_slot'],
        duration_hours=float(data['duration']),
        total_price=data['total_price'],
        seat_number=f"PC-{random.randint(1, 20)}",
        status='Confirmed'
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    # --- SIMULATE EMAIL SENDING ---
    print(f"\n[EMAIL SENT] To: {session.get('user_id')} | Subject: Booking Confirmed")
    print(f"Ticket #{new_booking.id} | Cafe: {new_booking.cafe.name}")
    print(f"Seat: {new_booking.seat_number} | Time: {new_booking.time_slot}\n")

    return jsonify({
        'message': 'Booking Confirmed', 
        'booking_id': new_booking.id, # Send back ID for "Ticket"
        'seat': new_booking.seat_number
    })

@app.route('/api/user/bookings')
def get_user_bookings():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    return jsonify([b.to_dict() for b in bookings])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_mock_data()
    app.run(debug=True)
