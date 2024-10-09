# Acronis Backup Dashboard

This project is a web-based dashboard for monitoring Acronis backup statuses across multiple devices and tenants.

## Features

- Display backup status for multiple devices
- Filter devices by status (OK, Warning, Error)
- Filter devices by tenant
- Sort devices by various attributes
- Show detailed status messages on mouseover

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/acronis-backup-dashboard.git
   cd acronis-backup-dashboard
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Acronis API credentials:
   Create a `.env` file in the root directory of the project and add the following content:
   ```
   CLIENT_ID=your_client_id_here
   CLIENT_SECRET=your_client_secret_here
   DATACENTER_URL=https://us-cloud.acronis.com
   ```
   Replace `your_client_id_here` and `your_client_secret_here` with your actual Acronis API credentials.

4. Run the application:
   ```
   python main.py
   ```

5. Open a web browser and navigate to `http://localhost:5000` to view the dashboard.

## Docker Deployment

To run this application using Docker:

1. Make sure you have created the `.env` file as described in the Setup section.

2. Build the Docker image:
   ```
   docker build -t acronis-backup-dashboard .
   ```

3. Run the Docker container:
   ```
   docker run --env-file .env -p 5000:5000 acronis-backup-dashboard
   ```

4. Access the dashboard at `http://localhost:5000`

## Docker Compose Deployment

To run this application using Docker Compose:

1. Make sure you have Docker Compose installed on your system.

2. Ensure you have created the `.env` file as described in the Setup section.

3. From the project root directory, run:
   ```
   docker-compose up --build
   ```

4. Access the dashboard at `http://localhost:5000`

5. To stop the application, use:
   ```
   docker-compose down
   ```

Using Docker Compose simplifies the process of running the application and makes it easier to add additional services in the future if needed.

## Environment Variables

This project uses environment variables to manage sensitive information and configuration. The following variables are required:

- `CLIENT_ID`: Your Acronis API client ID
- `CLIENT_SECRET`: Your Acronis API client secret
- `DATACENTER_URL`: The URL of the Acronis datacenter (default: https://us-cloud.acronis.com)

These variables should be set in a `.env` file in the root directory of the project. This file is not committed to version control for security reasons.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
