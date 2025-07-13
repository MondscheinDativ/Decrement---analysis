from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🎉 恭喜！你的网站在 CentOS 上运行成功！"

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
