from flask_login import LoginManager, UserMixin
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# from sqlalchemy import ForeignKey
# from sqlalchemy.orm import relationship
# import time
import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(12).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'insert key here'
app.config['MAIL_SERVER'] = 'insert mail here'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index' #page that is redirected to
login_manager.login_message_category = 'info'

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    type = db.Column(db.String(20), unique=True)
    staffId = db.relationship('Staffs', backref='users', lazy=True)

    def __repr__(self):
        return f"Users('{self.id}, {self.email}, {self.type}')"

    def serialize(self):
        return{
            'id': self.id
        }
    def is_authenticated(self):
        return self._authenticated

    def get_reset_token(self,expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id' : self.id}).decode('utf-8')
        
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

class Staffs(UserMixin, db.Model):
    __tablename__ = 'staffs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employeeNo = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(15), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    classId = db.relationship('Classes', backref='staffs', lazy=True)

    def __repr__(self):
        return f"Staffs('{self.id}, {self.name}, {self.employeeNo}, {self.role}, {self.userId}')"

class Students(UserMixin, db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    matricNo = db.Column(db.String(20), nullable=False)
    dateOfEnrollment = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(50), nullable=False)
    attendId = db.relationship('Attend', backref='students', lazy=True)

    def __repr__(self):
        return f"Students('{self.id}, {self.name}, {self.matricNo}, {self.dateOfEnrollment}')"

class Classes(UserMixin, db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(100), nullable=False)
    moduleCode = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    startTime = db.Column(db.DateTime, nullable=False)
    staffInCharged = db.Column(db.Integer, db.ForeignKey('staffs.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.String(10), nullable=False)
    classCode = db.Column(db.String(10), nullable=False)
    attendId = db.relationship('Attend', backref='classes', lazy=True)

    def __repr__(self):
        return f"Classes('{self.id}, {self.module}, {self.moduleCode}, {self.day}, {self.startTime}, {self.duration}, {self.frequency}')"

class Attend(UserMixin, db.Model):
    __tablename__ = 'attend'
    id = db.Column(db.Integer, primary_key=True)
    classId = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    studentId = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    attendance = db.Column(db.String(10), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    closedate = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"Attend('{self.id}, {self.classId}, {self.studentId}, {self.attendance}, {self.datetime}, {self.closedate}')"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))