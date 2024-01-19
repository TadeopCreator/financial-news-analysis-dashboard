# Stocks Sentiment Dashboard

This project is a Flask application that provides a sentiment analysis dashboard for stocks using Google Cloud Firestore. The application allows users to analyze sentiment data from news related to finance and visualize the information in a dashboard format.

<div align="center">
  <img src="app/static/stocks-dashboard-flow.jpg" alt="Financial News Analysis Architecture">
</div>

## Installation

To run this project locally, make sure you have Docker installed on your machine.

1. Clone this repository:

    ```bash
    git clone [https://github.com/your-username/stocks-sentiment-dashboard.git](https://github.com/TadeopCreator/stocks-sentiment-dashboard.git)
    cd stocks-sentiment-dashboard
    ```

2. Place your `application_default_credentials.json` file (Google Cloud service account key) inside the main directory.

3. Build the Docker image:

    ```bash
    docker build -t stocks-dashboard .
    ```

4. Run the Docker container:

    ```bash
    docker run -p 5000:5000 stocks-dashboard
    ```

5. Access the application in your browser at `http://localhost:5000`.

## Configuration

Before running the application, ensure you have the necessary dependencies listed in `requirements.txt` installed in your environment. Also, make sure to configure the `application_default_credentials.json` file for authentication with Google Cloud Firestore.

## Usage

- Once the application is running, access the provided URL in your browser to interact with the sentiment analysis dashboard.
- Use the dashboard to explore sentiment data related to different stocks.
- Ensure proper permissions and access to Google Cloud services for accurate data retrieval and analysis.

## License

This project is licensed under the [MIT License](LICENSE).
