# -*- coding: utf-8 -*-

import json

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ocr.v20181119 import ocr_client
from tencentcloud.ocr.v20181119.models import (
  GeneralAccurateOCRRequest,
  EnglishOCRRequest,
  GeneralBasicOCRRequest,
  GeneralEfficientOCRRequest,
  GeneralFastOCRRequest,
  GeneralHandwritingOCRRequest
)

from .tencent_config import SECRET_ID, SECRET_KEY

class TencentOcr(object):
  """
  计费说明：1,000次/月免费
  https://cloud.tencent.com/document/product/866/17619
  """
	
	# 地域列表
	# https://cloud.tencent.com/document/api/866/33518#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
  Region = "ap-beijing"

  endpoint = "ocr.tencentcloudapi.com"

  # 通用文字识别相关接口
  # https://cloud.tencent.com/document/api/866/37173
  mapping = {
    # 通用印刷体识别（高精度版） ok
    "GeneralAccurateOCR": GeneralAccurateOCRRequest,

    # 英文识别 ok
    "EnglishOCR": EnglishOCRRequest,

    # 通用印刷体识别 一般
    "GeneralBasicOCR": GeneralBasicOCRRequest,

    # 通用印刷体识别（精简版）（免费公测版）no
    "GeneralEfficientOCR": GeneralEfficientOCRRequest,

    # 通用印刷体识别（高速版）一般
    "GeneralFastOCR": GeneralFastOCRRequest,

    # 通用手写体识别 ok
    "GeneralHandwritingOCR": GeneralHandwritingOCRRequest,

  }

  def __init__(self):
    cred = credential.Credential(SECRET_ID, SECRET_KEY)

    httpProfile = HttpProfile()
    httpProfile.endpoint = self.endpoint

    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    self.client = ocr_client.OcrClient(cred, self.Region, clientProfile)

  def get_image_text(self, image_url, ocr="GeneralBasicOCR"):
    req = self.mapping[ocr]()
    req.ImageUrl = image_url
    resp = getattr(self.client, ocr)(req)
    return json.loads(resp.to_json_string())['TextDetections'][0]['DetectedText']


def main():
  tencentOcr = TencentOcr()
  url = "https://skp-1300389873.cos.ap-nanjing.myqcloud.com/test/%E8%88%9E%E8%B9%88%E5%AE%A4.png"
  print(tencentOcr.get_image_text(url, ocr="GeneralHandwritingOCR"))


if __name__ == '__main__':
  main()