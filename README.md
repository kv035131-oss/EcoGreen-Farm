# EcoGreen - Farmer-to-Consumer Application

This is a digital platform that connects farmers directly with consumers, bypassing intermediaries and reducing the overall cost of food products. 
The platform allows farmers to list their produce, and consumers can purchase quality food at lower prices.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

## Features

- User registration and login with JWT authentication
- Farmers can list their products with images
- Consumers can browse and place orders for products
- Payment Processing using Mpesa Express API
- Data pagination for product listings
- Swagger API documentation
- Multi-user authentication with role-based access
- Error handling and data validation
- CI/CD integration for code quality checks
- Human-readable date formatting

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/kv035131-oss/EcoGreen-Farm.git
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables:

    Create a `.env` file in the root directory and add the following:

    ```env
    SECRET_KEY=your_secret_key_here
    CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
    CLOUDINARY_API_KEY=your_cloudinary_api_key
    CLOUDINARY_API_SECRET=your_cloudinary_api_secret
    SENDGRID_API_KEY=your_sendgrid_api_key
    ```

## Usage

1. Run the application:
    ```bash
    python run.py
    ```

2. Access the application in your web browser at `http://localhost:5000`.

3. Register as a farmer or consumer to start using the platform.

## API Endpoints

- POST `/api/v1/User/create`: Register as a new user (farmer or consumer).
- POST `/api/v1/Login`: Log in and receive an access token for authentication.
- POST `/api/v1/products/create`: Create a new product listing (farmers only).
- GET `/api/v1/products`: Get a paginated list of available product listings.
- POST `/api/v1/Orders/create`: Place an order for a product (consumers only).
- GET `/api/v1/Orders`: Get a list of orders.

## Technologies Used

- Python and Flask framework for the backend.
- Flask-JWT-Extended for JWT authentication.
- SQLAlchemy for database management.
- Cloudinary for image uploads and storage.
- Frontend technologies (HTML, CSS, JavaScript) for the user interface.

## Contributing

Contributions to the EcoGreen Farmer-to-Consumer Platform are welcome! Please follow standard guidelines for contributing to open-source projects.

## License

This project is licensed under the [MIT License](https://github.com/kv035131-oss/EcoGreen-Farm/blob/main/LICENSE).
