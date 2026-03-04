from app import create_app

app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 8080))  # Railway sets PORT env variable
    app.run(host='0.0.0.0', port=port, debug=False)
