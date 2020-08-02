# -*- coding: utf-8 -*-

import json

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入对应产品模块的 client models。
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.iai.v20180301 import iai_client, models
import base64

from .tencent_config import SECRET_ID, SECRET_KEY


def get_json(img_dir):
    #with open(img_dir, 'rb') as f:
    #    base64_data = base64.b64encode(f.read())
    #    base64_code = base64_data.decode()
    try:
        # 实例化一个客户端配置对象，可以指定超时时间等配置
        clientProfile = ClientProfile()
        clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
        # 实例化一个认证对象，入参需要传入腾讯云账户 secretId，secretKey
        cred = credential.Credential(SECRET_ID, SECRET_KEY)
        client = iai_client.IaiClient(cred, "ap-guangzhou", clientProfile)
        # 实例化一个请求对象
        req = models.DetectFaceRequest()

        # 人脸检测参数
        req.MaxFaceNum = 1
        #req.Image = base64_code
        req.Url = img_dir
        req.NeedFaceAttributes = 1
        req.NeedQualityDetection = 0

        # 通过 client 对象调用想要访问的接口，需要传入请求对象
        resp = client.DetectFace(req)
        # 输出 JSON 格式的字符串回包
        json_data = resp.to_json_string()

        return json_data

    except TencentCloudSDKException as err:
        print(err)
        return None

def get_beauty(img_url):

    # response json sample
    # {"ImageWidth": 600, "ImageHeight": 354, "FaceInfos": [{"X": 314, "Y": 89, "Width": 139, "Height": 172, "FaceAttributesInfo": {"Gender": 99, "Age": 35, "Expression": 51, "Glass": false, "Pitch": 8, "Yaw": 18, "Roll": 0, "Beauty": 58, "Hat": false, "Mask": false, "Hair": {"Length": 1, "Bang": 1, "Color": 0}, "EyeOpen": true}, "FaceQualityInfo": {"Score": 0, "Sharpness": 0, "Brightness": 0, "Completeness": {"Eyebrow": 0, "Eye": 0, "Nose": 0, "Cheek": 0, "Mouth": 0, "Chin": 0}}}], "FaceModelVersion": "3.0", "RequestId": "93b94486-3feb-4bf1-ba04-da9e076eef10"}

    data = get_json(img_url)
    if data is None:
        return -1

    data = json.loads(data)
    max_beauty = 0
    if data:
        face_infos = data.get('FaceInfos', [])
        for info in face_infos:
            max_beauty = max(max_beauty, info.get('FaceAttributesInfo', {}).get('Beauty', 0))
    return max_beauty


if __name__ == '__main__':

    img_dir = "https://skp-1300389873.cos.ap-nanjing.myqcloud.com/test/liudehua.jpeg"
    print(get_beauty(img_dir))

    