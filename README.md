# Acronis Backup Dashboard

This project is a web-based dashboard for monitoring Acronis backup statuses across multiple devices and tenants.

## Features

- Display backup status for multiple devices
- Filter devices by status (OK, Warning, Error)
- Filter devices by tenant
- Sort devices by various attributes
- Show detailed status messages on mouseover
- Store device notes in a JSON file

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

## Updating Dependencies

If you make changes to the `requirements.txt` file or need to update dependencies:

1. If you're using Docker Compose:
   ```
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

2. If you're using Docker without Compose:
   ```
   docker stop <container_name>
   docker rm <container_name>
   docker build -t acronis-backup-dashboard .
   docker run --env-file .env -p 5000:5000 acronis-backup-dashboard
   ```

These commands will ensure that your Docker image is rebuilt with the latest dependencies.

## Environment Variables

This project uses environment variables to manage sensitive information and configuration. The following variables are required:

- `CLIENT_ID`: Your Acronis API client ID
- `CLIENT_SECRET`: Your Acronis API client secret
- `DATACENTER_URL`: The URL of the Acronis datacenter (default: https://us-cloud.acronis.com)

These variables should be set in a `.env` file in the root directory of the project. This file is not committed to version control for security reasons.

## Data Storage

This application uses a JSON file (`device_notes.json`) to store device notes. The file is automatically created when the application starts if it doesn't exist. Make sure the application has write permissions in the directory where it's running.

## Troubleshooting

If you encounter a 404 Not Found error when trying to access the dashboard, try the following steps:

1. Verify that the application is running:
   - If running locally, check the console output for any error messages.
   - If using Docker, use `docker ps` to check if the container is running.

2. Confirm the correct URL:
   - The application should be accessible at `http://localhost:5000` by default.
   - If you've modified the port or are accessing it from a different machine, adjust the URL accordingly.

3. Check firewall settings:
   - Ensure that your firewall is not blocking incoming connections on port 5000.

4. Verify Docker port mapping:
   - If using Docker, check that the port mapping is correct in your `docker run` command or `docker-compose.yml` file.

5. Check the logs:
   - For Docker: `docker logs <container_name>`
   - For Docker Compose: `docker-compose logs`

6. Ensure all files are in the correct location:
   - The `dashboard.html` file should be in the same directory as `main.py`.

7. Verify the Flask route:
   - Check that the route for the root URL ('/') is correctly defined in `main.py`.

If you're still encountering issues, please open an issue on the GitHub repository with details about your setup and the exact error message you're seeing.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
