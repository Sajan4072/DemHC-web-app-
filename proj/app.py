from enum import unique
import os
import sys

# Flask
from flask import Flask, request, render_template, Response, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin
from flask_wtf import wtforms
from flask_wtf.form import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import InputRequired,Length,ValidationError



#from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

# TensorFlow and tf.keras
#import tensorflow as tf
#from tensorflow import keras

from tensorflow.keras.applications.imagenet_utils import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Some utilites
import numpy as np
from util import base64_to_pil


# Declare a flask app
app = Flask(__name__)
db=SQLAlchemy(app) #creating an db instance
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
#secret key for security of session cookie
app.config['SECRET_KEY']='secret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#print('Model loaded. Check http://127.0.0.1:5000/')



MODEL_PATH = 'models/oldModel.h5'

model = load_model(MODEL_PATH)

print('Model loaded. Start serving...')


def model_predict(img, model):
    
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x, mode='tf')
    
    preds = model.predict(x)
    
    return preds


class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),nullable=False,unique=True)
    password=db.Column(db.String(80),nullable=False)

class RegisterForm(FlaskForm):
    username=StringField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={"placeholder":"Username"})

    password=PasswordField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={"placeholder":"Password"})

    submit=SubmitField("signup")

    def validate_username(self,username):
        existing_user_username=User.query.filter_by(
            username=username.data).first()

        if existing_user_username:
            raise ValidationError(
                "This username is taken please choose another"
            )    

class LoginForm(FlaskForm):
    username=StringField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={"placeholder":"Username"})

    password=PasswordField(validators=[InputRequired(),Length(min=4,max=20)],render_kw={"placeholder":"Password"})

    submit=SubmitField("login")




@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        
        # Get the image from post request
        img = base64_to_pil(request.json)
       
                
        img.save("uploads\image.jpg")
        
        img_path = os.path.join(os.path.dirname(__file__),'uploads\image.jpg')
        
        os.path.isfile(img_path)
        
        img = image.load_img(img_path, target_size=(64,64))

        preds = model_predict(img, model)
        
        
        result = preds[0,0]
        
        print(result)
        
        if result >0.5:
            return jsonify(result="PNEMONIA")
        else:
            return jsonify(result="NORMAL")

    return None


if __name__ == '__main__':
    app.run(port=5002, threaded=False)

    # Serve the app with gevent
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
