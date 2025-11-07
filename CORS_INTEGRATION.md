
# React Native Integration

Your Flask backend is already configured to accept requests from a React Native application. This is handled by the `Flask-Cors` library, which is set up in your `app.py` file.

## CORS Configuration

The following code in `app.py` enables Cross-Origin Resource Sharing (CORS) for your application:

```python
from flask_cors import CORS

# ... (your app creation)

CORS(
    app,
    origins=[
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:8001",
        "http://localhost:8002",
        "*",
    ],
)
```

The `origins` list includes common development endpoints for web and React Native applications, including the wildcard `*` which allows requests from any origin. This means your backend is ready to be called from your React Native app.

## Calling the API from React Native

Here is an example of how you can call the `/api/rag/ai-remedy` endpoint from a React Native application using `fetch`:

```javascript
const getAiRemedy = async (query) => {
  try {
    const response = await fetch('http://<your-backend-ip>:5000/api/rag/ai-remedy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log(data);
    return data;
  } catch (error) {
    console.error('There was a problem with the fetch operation:', error);
  }
};

// Example usage:
getAiRemedy('I have a headache');
```

**Important:**

*   Replace `<your-backend-ip>` with the actual IP address of the machine running your Flask backend. When running on the same machine, you can often use your machine's local IP address. You cannot use `localhost` or `127.0.0.1` from a physical device unless you have set up port forwarding.
*   Ensure your Flask application is running and accessible from the device or emulator where you are running your React Native app.

This setup should be all you need from the backend perspective to integrate with your React Native application.
