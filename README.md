# BuildPay — Streamlit Construction Payroll Demo

This version replaces the Flask server entrypoint with a Streamlit app, so Streamlit Community Cloud can run it without `app.run(debug=True)`.

## Deploy to Streamlit Community Cloud
1. Download and extract this ZIP.
2. Open your GitHub repository: https://github.com/magamaiswarya56-cmd/Buildpay
3. Choose **Add file → Upload files** (or the empty-repository upload link if applicable).
4. Upload the contents of this folder to the repository root. Replace `app.py` and `requirements.txt` when asked.
5. Commit the changes.
6. In Streamlit Community Cloud, open the app settings and set **Main file path** to `app.py`. Reboot/redeploy the app.

## Run locally
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Demo credentials
- Admin username: `admin`
- Admin password: `admin123`
- Worker IDs: `23491A1213`, `23491A1214`, `23491A1216`, `23491A1218`, `23491A1222`, `23491A1254`
- Worker PIN: `1234`
- Additional demo workers use PIN `1234`.

## Features
- Admin dashboard and worker directory
- Add workers
- Date-wise attendance editor and SQLite saves
- Payroll estimates and CSV downloads
- Worker self-service portal with profile, attendance lookup and pay estimate
- High-contrast light theme

## Important data note
The app creates `buildpay_streamlit.db` beside `app.py`. On Streamlit Community Cloud, local filesystem data may not be durable across rebuilds/restarts, so this is suitable for a demo. Use a hosted persistent database for real payroll records. This is a classroom prototype; demo credentials are hard-coded and must not be used for real employee data.
