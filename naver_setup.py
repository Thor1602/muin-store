import hmac, hashlib, base64
import time, requests, json
from Database import Main

def send_notification_code(to_no, code, language):
    main = Main()

    sid = main.get_setting_by_name('naver_sid_sms')[0]
    sms_uri = "/sms/v2/services/{}/messages".format(sid)
    sms_url = "https://sens.apigw.ntruss.com{}".format(sms_uri)
    sec_key = main.get_setting_by_name('naver_sid_sms')[1]

    acc_key_id = main.get_setting_by_name('naver_access_sms')[0]
    acc_sec_key = str.encode(main.get_setting_by_name('naver_access_sms')[1])

    stime = int(float(time.time()) * 1000)

    hash_str = "POST {}\n{}\n{}".format(sms_uri, stime, acc_key_id)

    digest = hmac.new(acc_sec_key, msg=hash_str.encode('utf-8'), digestmod=hashlib.sha256).digest()
    d_hash = base64.b64encode(digest).decode()

    if language == "en":
        message = "[Coup De Foudre] Please enter the verification number [{}].".format(code)
    else:
        message = "[쿠 드 푸드레] 인증번호 [{}]를 입력해주세요.".format(code)
    msg_data = {
        'type': 'SMS',
        'countryCode': '82',
        'from': "{}".format('01048878249'),
        'contentType': 'COMM',
        'content': "{}".format(message),
        'messages': [{'to': "{}".format(to_no)}]
    }

    response = requests.post(
        sms_url, data=json.dumps(msg_data),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "x-ncp-apigw-timestamp": str(stime),
                 "x-ncp-iam-access-key": acc_key_id,
                 "x-ncp-apigw-signature-v2": d_hash
                 }
    )

    return response.text

if __name__ == '__main__':
    # send_notification_code("01048108249", '123456', 'KO-kr')
    pass