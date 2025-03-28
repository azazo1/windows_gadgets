import os
from pathlib import Path
import sys
import time
import traceback

import requests
import toml
from Tea.core import TeaCore
from alibabacloud_alidns20150109.client import Client as DnsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as dns_models
from alibabacloud_tea_util.client import Client as UtilClient


def get_public_ip():
    response = requests.get("https://api64.ipify.org/?format=json")
    return response.json()["ip"]


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def initialization(
        region_id: str,
    ) -> DnsClient:
        """
        Initialization  初始化公共请求参数
        """
        config = open_api_models.Config()
        # 您的AccessKey ID
        config.access_key_id = key_config["ACCESS_KEY_ID"]
        # 您的AccessKey Secret
        config.access_key_secret = key_config["ACCESS_KEY_SECRET"]
        # 您的可用区ID
        config.region_id = region_id
        return DnsClient(config)

    @staticmethod
    def describe_domain_records(
        client: DnsClient,
        domain_name: str,
        rr: str,
        record_type: str,
    ) -> dns_models.DescribeDomainRecordsResponse:
        """
        获取主域名的所有解析记录列表
        """
        req = dns_models.DescribeDomainRecordsRequest()
        # 主域名
        req.domain_name = domain_name
        # 主机记录
        req.rrkey_word = rr
        # 解析记录类型
        req.type = record_type
        try:
            resp = client.describe_domain_records(req)
            print("-------------------获取主域名的所有解析记录列表--------------------")
            print(UtilClient.to_jsonstring(TeaCore.to_map(resp)))
            return resp
        except Exception as error:
            print(error, file=sys.stderr)
        return

    @staticmethod
    async def describe_domain_records_async(
        client: DnsClient,
        domain_name: str,
        rr: str,
        record_type: str,
    ) -> dns_models.DescribeDomainRecordsResponse:
        """
        获取主域名的所有解析记录列表
        """
        req = dns_models.DescribeDomainRecordsRequest()
        # 主域名
        req.domain_name = domain_name
        # 主机记录
        req.rrkey_word = rr
        # 解析记录类型
        req.type = record_type
        try:
            resp = await client.describe_domain_records_async(req)
            print("-------------------获取主域名的所有解析记录列表--------------------")
            print(UtilClient.to_jsonstring(TeaCore.to_map(resp)))
            return resp
        except Exception as error:
            print(error)
        return

    @staticmethod
    def update_domain_record(
        client: DnsClient,
        req: dns_models.UpdateDomainRecordRequest,
    ) -> None:
        """
        修改解析记录
        """
        try:
            resp = client.update_domain_record(req)
            print("-------------------修改解析记录--------------------")
            print(UtilClient.to_jsonstring(TeaCore.to_map(resp)))
        except Exception as error:
            print(error)

    @staticmethod
    async def update_domain_record_async(
        client: DnsClient,
        req: dns_models.UpdateDomainRecordRequest,
    ) -> None:
        """
        修改解析记录
        """
        try:
            resp = await client.update_domain_record_async(req)
            print("-------------------修改解析记录--------------------")
            print(UtilClient.to_jsonstring(TeaCore.to_map(resp)))
        except Exception as error:
            print(error)

    @staticmethod
    def main() -> None:
        regionid = key_config["REGION_ID"]
        current_host_ip = get_public_ip()
        domain_name = key_config["DOMAIN_NAME"]
        rr = key_config["RR"]
        record_type = key_config["RECORD_TYPE"]
        client = Sample.initialization(regionid)
        resp = Sample.describe_domain_records(client, domain_name, rr, record_type)
        if UtilClient.is_unset(resp) or UtilClient.is_unset(
            resp.body.domain_records.record[0]
        ):
            print("错误参数！")
            return
        record = resp.body.domain_records.record[0]
        # 记录ID
        record_id = record.record_id
        # 记录值
        records_value = record.value
        print(
            f"-------------------当前主机公网IP为：{current_host_ip}--------------------"
        )
        if not UtilClient.equal_string(current_host_ip, records_value):
            # 修改解析记录
            req = dns_models.UpdateDomainRecordRequest()
            # 主机记录
            req.rr = rr
            # 记录ID
            req.record_id = record_id
            # 将主机记录值改为当前主机IP
            req.value = current_host_ip
            # 解析记录类型
            req.type = record_type
            Sample.update_domain_record(client, req)


def main():
    os.chdir(Path(__file__).parent)
    global key_config
    try:
        ip = get_public_ip()
        key_config = toml.load("ali-ddns-config.toml")
        routine = key_config.get("ROUTINE")
        if isinstance(routine, int) and routine > 0:
            last_time = 0
            while True:
                new_ip = get_public_ip()
                if time.time() - last_time > routine or new_ip != ip:
                    Sample.main()
                    print(f"更新成功！{time.asctime()}")
                    last_time = time.time()
                    ip = new_ip
                time.sleep(10)
        else:
            Sample.main()
    except FileNotFoundError:
        with open("ali-ddns-config.toml", "w") as w:
            toml.dump(
                {
                    "ACCESS_KEY_ID": "your-access-key-id",
                    "ACCESS_KEY_SECRET": "your-access-key-secret",
                    "REGION_ID": "cn-hangzhou",
                    "DOMAIN_NAME": "your-domain-name",
                    "RR": "your-rr",
                    "RECORD_TYPE": "A",
                    "ROUTINE": None,
                },
                w,
            )
        os.system("cmd /c echo 请修改ali-ddns-config.toml文件中的配置信息！ && pause")
        exit(1)
    except Exception:
        with open("error.txt", "w") as w:
            w.write(traceback.format_exc())
