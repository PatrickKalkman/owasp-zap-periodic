import requests
import logging


def trigger_zap_scan(zap_host, zap_api_key, zap_context_id):
    params = {'apikey': zap_api_key, 'contextId': zap_context_id}

    response = requests.get(f'{zap_host}/JSON/ascan/action/scan/',
                            params=params)

    if (response.status_code == 200):
        json_response = response.json()
        scan_id = str(json_response["scan"])
        return scan_id
    else:
        logging.error(f'Failed to trigger scan. {str(response.status_code)}')
        return None


def get_zap_scan_progress(zap_host, zap_api_key, zap_scan_id):
    params = {'apikey': zap_api_key, 'scanId': zap_scan_id}

    response = requests.get(f'{zap_host}/JSON/ascan/view/status/',
                            params=params)

    if (response.status_code == 200):
        json_response = response.json()
        return json_response["status"]
    else:
        logging.error(f'Failed to get status. {str(response.status_code)}')
        return None


def get_zap_scan_result_summary(zap_host, zap_api_key):
    params = {'apikey': zap_api_key}

    response = requests.get(f'{zap_host}/JSON/alert/view/alertsSummary/',
                            params=params)

    if (response.status_code == 200):
        json_response = response.json()
        print(type(json_response))
        return json_response["alertsSummary"]
    else:
        logging.error(f'Failed to get summary. {str(response.status_code)}')
        return None


def get_zap_scan_report(zap_host, zap_api_key, reportDirectory, reportName):
    params = {'apikey': zap_api_key}

    response = requests.get(f'{zap_host}/OTHER/core/other/htmlreport/',
                            params=params)

    if (response.status_code == 200):
        report_handle = open(f'{reportDirectory}//{reportName}', 'w')
        report_handle.write(response.content.decode('utf-8'))
        report_handle.close()

    else:
        logging.error(f'Failed to get summary. {str(response.status_code)}')
