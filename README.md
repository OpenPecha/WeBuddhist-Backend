# Pecha API

This is the backend API for the Pecha application.


<!--
This section provides instructions for installing the necessary components or dependencies for the project. Follow the steps outlined below to set up the project on your local machine.
-->
### Installation

Follow these steps to set up the project on your local machine:

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/pecha_api.git
    ```
2. Navigate to the project directory:
    ```sh
    cd pecha_api
    ```
3. Install the dependencies:
    ```sh
    poetry install
    ```

### Database Setup

1. Navigate to the local setup directory:
    ```sh
    cd local_setup
    ```
2. Start the database using Docker:
    ```sh
    docker-compose up -d
    ```
3. Apply database migrations:
    ```sh
    poetry run alembic upgrade head
    ```

### Running the Application

1. Start the FastAPI development server:
    ```sh
    poetry run uvicorn pecha_api.app:api --reload
    ```

The application will be available at `http://127.0.0.1:8000/`.

### API Documentation

You can access the Swagger UI for the API documentation at `http://127.0.0.1:8000/docs`.  ```sh
    poetry install
    ```

### Running Tests

To run tests, execute the following command:
    ```sh
    poetry run pytest
    ```

To check the coverage:
    ```sh
    poetry run pytest --cov=pecha_api
    ```
    ```sh
    poetry run coverage html 
    ```

Open the coverage report:
    ```sh
    open htmlcov/index.html  
    ```
    ### Alembic Commands

    Alembic is used for handling database migrations. Here are some common commands:

    1. Create a new migration:
        ```sh
        poetry run alembic revision --autogenerate -m "description of migration"
        ```

    2. Apply the latest migrations:
        ```sh
        poetry run alembic upgrade head
        ```

    3. Downgrade to a previous migration:
        ```sh
        poetry run alembic downgrade -1
        ```

    4. View the current migration history:
        ```sh
        poetry run alembic history
        ```

    5. Show the current migration state:
        ```sh
        poetry run alembic current
        ```

## API Specs
- [Store Segments API](./spec/openapi_create_segments.yaml)
- [Get Segments API](./spec/openapi_get_segments.yaml)