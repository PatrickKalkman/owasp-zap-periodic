import os
import requests
import logging
import sqlite3
import time
from datetime import datetime


def create_scan_table():
    """Create the scan database and table if it doesn't already exist."""
    conn = sqlite3.connect('./db/scan_db.sqlite')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS scan (
            id INTEGER NOT NULL UNIQUE,
            scan_id INTEGER NOT NULL UNIQUE,
            created TEXT,
            updated TEXT,
            progress INTEGER,
            high_alerts INTEGER,
            medium_alerts INTEGER,
            low_alerts INTEGER,
            info_alerts INTEGER,
            report TEXT,
            PRIMARY KEY (id)
        )
    ''')

    conn.commit()
    conn.close()


def insert_or_update_scan(scan_id, progress, high_alerts,
                          medium_alerts, low_alerts, info_alerts, report):
    """Insert or update a scan record with the given parameters."""
    conn = sqlite3.connect('./db/scan_db.sqlite')

    cursor = conn.cursor()
    cursor.execute('SELECT scan_id FROM scan WHERE scan_id = ?', (scan_id,))
    exists_row = cursor.fetchone()

    created_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if exists_row is None:
        conn.execute('''
            INSERT INTO scan (scan_id, created, updated, progress, high_alerts,
            medium_alerts, low_alerts, info_alerts, report)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (scan_id, created_str, created_str, progress, high_alerts,
              medium_alerts, low_alerts, info_alerts, report))
    else:
        conn.execute('''
            UPDATE scan
            SET updated = ?, progress = ?, high_alerts = ?,
                medium_alerts = ?, low_alerts = ?, info_alerts = ?, report = ?
            WHERE scan_id = ?
        ''', (created_str, progress, high_alerts, medium_alerts, low_alerts,
              info_alerts, report, scan_id))

    conn.commit()
    conn.close()


def start_zap_scan(zap_host, zap_api_key, zap_context_id):
    """Start a new zap scan with the given context id."""

    params = {'apikey': zap_api_key, 'contextId': zap_context_id}

    resp = requests.get(f'{zap_host}/JSON/ascan/action/scan/',
                        params=params)

    if (resp.status_code == 200):
        json_response = resp.json()
        scan_id = str(json_response["scan"])
        return scan_id
    else:
        logging.error(f'Failed to trigger scan. {str(resp.status_code)}')
        return None


def get_zap_scan_progress(zap_host, zap_api_key, zap_scan_id):
    """Get the progress of an existing new zap scan."""
    params = {'apikey': zap_api_key, 'scanId': zap_scan_id}

    resp = requests.get(f'{zap_host}/JSON/ascan/view/status/',
                        params=params)

    if (resp.status_code == 200):
        json_response = resp.json()
        return int(json_response["status"])
    else:
        logging.error(f'Failed to get the status. {str(resp.status_code)}')
        return None


def get_zap_scan_result_summary(zap_host, zap_api_key):
    """Get the a summary of the zap scan."""
    params = {'apikey': zap_api_key}

    resp = requests.get(f'{zap_host}/JSON/alert/view/alertsSummary/',
                        params=params)

    if (resp.status_code == 200):
        json_response = resp.json()
        print(type(json_response))
        return json_response["alertsSummary"]
    else:
        logging.error(f'Failed to get the summary. {str(resp.status_code)}')
        return None


def generate_zap_scan_report(zap_host, zap_api_key, zap_scan_id):
    """Generate a zap scan report and store it on the file system."""
    params = {'apikey': zap_api_key}

    resp = requests.get(f'{zap_host}/OTHER/core/other/htmlreport/',
                        params=params)

    if (resp.status_code == 200):
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_name = f'scan_report_{zap_scan_id}_{current_datetime}.html'
        report_handle = open(f'./reports/{report_name}', 'w')
        report_handle.write(resp.content.decode('utf-8'))
        report_handle.close()
        return report_name
    else:
        logging.error(f'Failed to create report. {str(resp.status_code)}')


def start_and_process_scan(zap_host, zap_api_key, zap_context_id):
    create_scan_table()

    logging.info('Starting zap scan.')
    scan_id = start_zap_scan(zap_host, zap_api_key, zap_context_id)
    insert_or_update_scan(scan_id, 0, 0, 0, 0, 0, '')

    scan_progress = get_zap_scan_progress(zap_host, zap_api_key, scan_id)
    while scan_progress < 100:
        logging.info(f'Scan progress: {scan_progress}')
        time.sleep(60)
        scan_progress = get_zap_scan_progress(zap_host, zap_api_key, scan_id)
        insert_or_update_scan(scan_id, scan_progress, 0, 0, 0, 0, '')

    summary = get_zap_scan_result_summary(zap_host, zap_api_key)
    report = generate_zap_scan_report(zap_host, zap_api_key)

    high_alerts = summary['High']
    medium_alerts = summary['Medium']
    low_alerts = summary['Low']
    info_alerts = summary['Informational']

    insert_or_update_scan(scan_id, scan_progress, high_alerts, medium_alerts,
                          low_alerts, info_alerts, 0, report)

    logging.info('Scan completed.')


api_key = os.getenv('ZAP_API_KEY')
zap_host = 'http://localhost:8082'
zap_context_id = 1  # 1 is the default context id

start_and_process_scan(zap_host, api_key, zap_context_id)
