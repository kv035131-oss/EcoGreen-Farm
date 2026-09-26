import os
import cloudinary


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    cloudinary.config(
        cloud_name='dlgspxpwr',
        api_key='162229873424843',
        api_secret='PK64yfEbGdYzy7syywRCAhLOYGc'
    )
    

    JWT_TOKEN_LOCATION=['headers']
    JWT_SECRET_KEY='VDpbyCMPTKsrvSEm1Dlp11FCEPx2rpIa3jlqLGi70zY'
    JWT_HEADER_NAME='Authorization'
    JWT_HEADER_TYPE="Bearer"