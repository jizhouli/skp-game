import json

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入对应产品模块的 client models。
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.tiia.v20190529 import tiia_client, models
import base64

from .tencent_config import SECRET_ID, SECRET_KEY

def detect_label(img_url):

    try:
        # 实例化一个客户端配置对象，可以指定超时时间等配置
        clientProfile = ClientProfile()
        clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
        # 实例化一个认证对象，入参需要传入腾讯云账户 secretId，secretKey
        cred = credential.Credential(SECRET_ID, SECRET_KEY)
        client = tiia_client.TiiaClient(cred, "ap-guangzhou", clientProfile)
        # 实例化一个请求对象
        req = models.DetectLabelRequest()

        # 人脸检测参数
        req.ImageUrl = img_url
        req.Scenes = ['CAMERA', 'WEB']

        # 通过 client 对象调用想要访问的接口，需要传入请求对象
        resp = client.DetectLabel(req)
        labels = set()
        if resp.Labels:
            for label in resp.Labels:
                labels.add(label.Name)
        if resp.CameraLabels:
            for label in resp.CameraLabels:
                labels.add(label.Name)

        return list(labels)

    except TencentCloudSDKException as err:
        print(err)
        return None

def get_object(img_url):
    labels = detect_label(img_url)
    if labels is None:
        return ''
    return ' '.join(labels)

if __name__ == '__main__':

    img_dir = "https://skp-1300389873.cos.ap-nanjing.myqcloud.com/test/%E6%B0%B4%E6%9D%AF.jpeg"
    labels = get_object(img_dir)
    print(labels)
