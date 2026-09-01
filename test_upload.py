import requests

# Upload the file
with open(r'E:\SIH\Project_2\test_qpsk_10db.iq', 'rb') as f:
    r = requests.post('http://127.0.0.1:8000/api/upload', files={'file': ('test_qpsk_10db.iq', f)}, data={'iq_dtype': 'float32', 'sample_rate': '1000000'})
    print('Upload:', r.json())
    job_id = r.json().get('job_id')

# Analyze
if job_id:
    r = requests.post('http://127.0.0.1:8000/api/analyze', json={'job_id': job_id, 'iq_dtype': 'float32', 'sample_rate': 1000000})
    print('Analyze:', r.json())

    import time
    for i in range(30):
        r = requests.get('http://127.0.0.1:8000/api/analysis/{}/status'.format(job_id))
        status = r.json()
        print('Status: {} {}% - {}'.format(status['status'], status['progress'], status['message']))
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            print('Error:', status.get('error'))
            break
        time.sleep(1)

    if status['status'] == 'completed':
        r = requests.get('http://127.0.0.1:8000/api/analysis/{}'.format(job_id))
        result = r.json()
        print('Modulation: {} ({:.2f})'.format(result['modulation']['prediction'], result['modulation']['confidence']))
        demod = result['demodulation']
        print('Demod: {} | Bits: {} | EVM: {}'.format(demod['status'], demod['bit_count'], demod['evm_rms_pct']['value']))