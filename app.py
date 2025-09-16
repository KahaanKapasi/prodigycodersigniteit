from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"   # needed for sessions
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    Address = db.Column(db.String(200), nullable=False)
    blood_grp = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    live_loc = db.Column(db.String(200), nullable=False)

    def __repr__(self) -> str:
        return f"{self.name} - {self.blood_grp} - {self.live_loc}"

class Hospital(db.Model):
    h_id = db.Column(db.Integer, primary_key=True, nullable=False)
    h_name = db.Column(db.String(100), nullable=False)
    h_address = db.Column(db.String(200), nullable=False)
    h_contact_no = db.Column(db.String(100), nullable=False)
    h_email = db.Column(db.String(100), nullable=False)

class SOSRequest(db.Model):
    req_id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    required_blood = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(50), default="Pending")   

# ROUTES
@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials!", "danger")
            return redirect(url_for('login'))

    # if GET request, render login page
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    Address = request.form['Address']
    blood_grp = request.form['blood_grp']
    age = request.form['age']
    gender = request.form['gender']
    live_loc = request.form['live_loc']

    if User.query.filter_by(email=email).first():
        flash("Email already registered!", "danger")
        return redirect(url_for('login'))

    new_user = User(name=name, email=email, password=password,
                    Address=Address, blood_grp=blood_grp,
                    age=age, gender=gender, live_loc=live_loc)
    db.session.add(new_user)
    db.session.commit()
    flash("Signup successful! Please login.", "success")
    return redirect(url_for('home'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return f"Welcome {user.name}! Your blood group is {user.blood_grp}. You live in {user.live_loc}. You are {user.age} years old and you are a {user.gender}. You live at {user.Address}.Your User ID is {user.id}."

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
