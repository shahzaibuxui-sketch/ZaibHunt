from app import create_app

# Create the Flask application using our factory function
app = create_app()

if __name__ == '__main__':
    # Run the development server
    # debug=True enables:
    #   - Auto-reload when code changes
    #   - Better error messages in the browser
    #   - Interactive debugger if something breaks
    app.run(debug=True, port=5000)