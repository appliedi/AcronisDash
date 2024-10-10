# Acronis Backup Dashboard

This application provides a dashboard for monitoring Acronis backup statuses across multiple tenants.

## Features

- View backup statuses for multiple tenants
- Filter devices by status and activity
- Sort devices by various attributes
- Search for specific devices
- Toggle device active/inactive status

## Prerequisites

- Python 3.8+
- Node.js 14+
- Docker (optional, for containerized deployment)

## Project Structure

```
.
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   └── ... (other frontend files)
├── main.py
├── requirements.txt
├── .env
├── Dockerfile
├── docker-compose.yml
├── README.md
├── LICENSE.md
└── CONTRIBUTING.md
```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/acronis-backup-dashboard.git
   cd acronis-backup-dashboard
   ```

2. Set up the backend:
   ```
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```
   cd frontend
   npm install
   ```

4. Create a `.env` file in the root directory with the following content:
   ```
   ACRONIS_CLIENT_ID=your_client_id
   ACRONIS_CLIENT_SECRET=your_client_secret
   DATACENTER_URL=your_datacenter_url
   ```

## Running the Application

1. Start the backend:
   ```
   python main.py
   ```

2. Start the frontend:
   ```
   cd frontend
   npm start
   ```

3. Open a web browser and navigate to `http://localhost:3000`

## Docker Deployment

To run the application using Docker:

1. Build the Docker image:
   ```
   docker-compose build
   ```

2. Run the containers:
   ```
   docker-compose up
   ```

3. Open a web browser and navigate to `http://localhost:3000`

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
