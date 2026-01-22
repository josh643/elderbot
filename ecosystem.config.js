module.exports = {
  apps: [
    {
      name: 'skry-engine',
      script: 'src/main.py',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      env: {
        PYTHONPATH: '.'
      }
    },
    {
      name: 'skry-dashboard',
      script: 'streamlit',
      args: 'run src/dashboard/app.py --server.port 8501 --server.headless true',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      env: {
        PYTHONPATH: '.'
      }
    }
  ]
};
