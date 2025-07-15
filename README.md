# Personal MCP ServiceNow

A personal project to integrate an MCP (Model Context Protocol) server with a ServiceNow instance to enable similarity-based incident retrieval and table description queries within the ServiceNow workflow.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Contributing](#contributing)
- [License](#license)

## Overview
This project implements an MCP server using the `FastMCP` framework to interact with a ServiceNow instance. It provides tools to test server connectivity, query ServiceNow table descriptions, and retrieve incidents based on text similarity or incident numbers. The server integrates with the ServiceNow REST API to fetch incident data and supports keyword-based searches for incident management.

## Features
- **MCP Server Integration**: Runs an MCP server (`mcpnowsimilarity`) for ServiceNow interactions.
- **ServiceNow API Integration**: Connects to the ServiceNow REST API to query incidents and table descriptions.
- **Similarity-Based Incident Retrieval**: Finds incidents based on text input or existing incident descriptions.
- **Table Description Queries**: Retrieves metadata for specified ServiceNow tables.
- **Asynchronous API Requests**: Uses `httpx` for efficient, asynchronous API calls with error handling.
- **Keyword Extraction**: Implements basic keyword extraction for text-based incident searches.

## Prerequisites
Before setting up the project, ensure you have the following:
- Python 3.8 or higher.
- A running ServiceNow instance with REST API access (e.g., a developer or enterprise instance).
- ServiceNow API credentials (username and password).
- Access to the MCP server framework (`FastMCP`).
- Basic knowledge of Python, asynchronous programming, and ServiceNow REST APIs.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/personal-mcp-servicenow.git
   cd personal-mcp-servicenow
   ```

2. **Install Dependencies**:
   Install the required Python packages using pip:
   ```bash
   pip install httpx fastmcp
   ```
   Note: Ensure the `fastmcp` package is available or install it as per its documentation.

3. **Set Up ServiceNow Instance**:
   - Log in to your ServiceNow instance.
   - Verify that the REST API is enabled (e.g., IntegrationHub plugin or equivalent).
   - Ensure you have valid credentials with access to the `incident` table and custom API endpoints (e.g., `/api/x_146833_awesomevi/test`).

## Configuration
1. **Environment Setup**:
   Create a `.env` file in the project root to store sensitive configuration details:
   ```plaintext
   SERVICENOW_INSTANCE=https://matecodev.service-now.com
   SERVICENOW_USERNAME=admin
   SERVICENOW_PASSWORD=your-password
   ```
   Replace `your-password` with your actual ServiceNow password or use a more secure method (e.g., environment variables or a secrets manager).

2. **ServiceNow API Configuration**:
   - Ensure the ServiceNow instance supports the custom API endpoint (`/api/x_146833_awesomevi/test`) used in the code.
   - Verify that the `incident` table is accessible via the `/api/now/table/incident` endpoint with the required fields (`number`, `short_description`).

3. **MCP Server Setup**:
   - The MCP server is initialized with the name `mcpnowsimilarity`, version `1.0.0`, and description `MCP Now Similarity Service`.
   - No additional configuration is required unless you modify the server name or transport method.

## Usage
1. **Run the MCP Server**:
   Start the server using the standard input/output transport:
   ```bash
   python mcp_server.py
   ```
   The server will listen for requests and execute the defined tools.

2. **Interact with Tools**:
   Use the provided tools to interact with the ServiceNow instance. See [Available Tools](#available-tools) for details on each tool's functionality.

3. **Monitor Logs**:
   - The server logs responses from ServiceNow API calls.
   - Check the console for errors like "Unable to fetch alerts or no alerts found" if API requests fail.

## Available Tools
The MCP server provides the following tools, accessible via the `FastMCP` interface:

- **`nowtest`**:
  - **Description**: Tests if the MCP server is running.
  - **Usage**: Returns `"Server is running and ready to handle requests!"`.
  - **Example**: `await nowtest()`

- **`nowtestauth`**:
  - **Description**: Tests authenticated access to the ServiceNow custom API endpoint (`/api/x_146833_awesomevi/test`).
  - **Usage**: Returns the API response or `"Unable to fetch alerts or no alerts found."` if the request fails.
  - **Example**: `await nowtestauth()`

- **`nowtestauthInput(tableName: str)`**:
  - **Description**: Retrieves the description for a specified ServiceNow table.
  - **Parameters**: `tableName` (e.g., `incident`, `user`).
  - **Usage**: Queries the custom API endpoint (`/api/x_146833_awesomevi/test/{tableName}`) and returns the response or an error message.
  - **Example**: `await nowtestauthInput("incident")`

- **`similarincidentsfortext(inputText: str)`**:
  - **Description**: Finds ServiceNow incidents based on keywords extracted from the input text.
  - **Parameters**: `inputText` (text to search for similar incidents).
  - **Usage**: Queries the `incident` table with `short_descriptionCONTAINS{keyword}` and returns matching incidents or an error message.
  - **Example**: `await similarincidentsfortext("server error")`

- **`getshortdescforincident(inputincident: str)`**:
  - **Description**: Retrieves the `short_description` for a given incident number.
  - **Parameters**: `inputincident` (incident number, e.g., `INC0010001`).
  - **Usage**: Queries the `incident` table with `number={inputincident}` and returns the description or an error message.
  - **Example**: `await getshortdescforincident("INC0010001")`

- **`similarincidentsforincident(inputincident: str)`**:
  - **Description**: Finds similar incidents based on the `short_description` of a given incident number.
  - **Parameters**: `inputincident` (incident number).
  - **Usage**: Retrieves the `short_description` using `getshortdescforincident` and then calls `similarincidentsfortext` to find similar incidents.
  - **Example**: `await similarincidentsforincident("INC0010001")`

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please ensure your code follows Python PEP 8 standards and includes relevant documentation for new tools or modifications.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
