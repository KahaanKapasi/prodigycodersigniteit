from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
import os

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
    phone = db.Column(db.String(15), nullable=True)

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
    phone = request.form['phone']
    if User.query.filter_by(email=email).first():
        flash("Email already registered!", "danger")
        return redirect(url_for('login'))
    new_user = User(
        name=name, email=email, password=password,
        Address=Address, blood_grp=blood_grp,
        age=age, gender=gender, live_loc=live_loc, phone=phone
    )
    db.session.add(new_user)
    db.session.commit()
    session['user_id'] = new_user.id
    flash("Signup successful! Welcome!", "success")
    return redirect(url_for('home'))

#----------
# Accept page route
@app.route('/accept/<int:req_id>')
def accept(req_id):
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    req = SOSRequest.query.get_or_404(req_id)
    patient = User.query.get(req.user_id)

    # Example: find all donors with matching blood group
    donors = User.query.filter(
        User.blood_grp == req.required_blood,
        User.id != patient.id
    ).all()

    # Get hospitals (later you can filter by distance)
    hospitals = Hospital.query.all()

    return render_template(
        'accept.html',
        patient=patient,
        donors=donors,
        hospitals=hospitals
    )
#----------

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('home.html', user=user)


@app.route('/sosrequest')
def sosrequest():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # --- Function 1: Create SOS request ---
    new_req = SOSRequest(
        user_id=user.id,
        required_blood=user.blood_grp,
        status="Pending"
    )
    db.session.add(new_req)
    db.session.commit()

    # --- Function 2: Send WhatsApp SOS ---
    try:
        account_sid = "ACdfb7ba0f1f74a1162f9a1383f566d001"
        auth_token = "1197041287f1d9ab0ebce4828822e655"
        client = Client(account_sid, auth_token)

        msg_text = f"🚨 SOS Alert: {user.blood_grp} blood needed!\n" \
           f"Patient: {user.name}, Age {user.age}\n" \
           f"Location: {user.live_loc}\n" \
           f"https://prodigycodersigniteit-1.onrender.com//accept/{new_req.req_id}"


        message = client.messages.create(
            body=msg_text,
            from_="whatsapp:+14155238886",   # Twilio sandbox number
            to="whatsapp:+917045001010"      # Replace with actual verified number
        )
        flash("SOS request sent via WhatsApp!", "success")

    except Exception as e:
        flash(f"Failed to send WhatsApp message: {str(e)}", "danger")

    # --- Function 3: Render confirmation page ---
    return render_template('sosrequest.html', user=user, request=new_req)





@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port = 8000)
