# 基础知识库

## 国内镜像加速

镜像提供方 | 镜像地址 | 包含资源
----------|------|-------
阿里云 | http://npm.taobao.org/mirrors/ <br> http://mirrors.aliyun.com | Python、Node、etc.
腾讯 | https://mirrors.tencent.com/ | 各种软件
清华大学 | https://mirrors.tuna.tsinghua.edu.cn/ | 各种开源系统和软件
网易 | http://mirrors.163.com/ | 开源系统软件
豆瓣 | https://pypi.doubanio.com/simple/ | PyPi
华为 | https://mirrors.huaweicloud.com/ | 各种开源系统和软件

### 加速使用方法

加速内容 | 地址 | 使用方法
------|-----|------
Python 下载 | https://npm.taobao.org/mirrors/python/ | 直接选择版本下载
PyPi 安装 | https://pypi.doubanio.com/simple/ <br> https://mirrors.aliyun.com/pypi/simple/ <br> http://mirrors.163.com/pypi/simple/ <br> https://mirrors.cloud.tencent.com/pypi/simple/ | pip -i $index_url $package
Alpine APK | https://mirrors.aliyun.com <br> https://mirrors.aliyun.com <br> https://mirrors.cloud.tencent.com/ | sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
Docker 镜像加速 | https://[系统分配前缀].mirror.aliyuncs.com <br> https://registry.cn-hangzhou.aliyuncs.com   | {"registry-mirrors": ["$mirror1", "$mirror2"]}
Docker 私有仓库 | https://[harbor.localhost] | {"insecure-registries": ["$harbor"]} Or [配置自签名证书](https://docs.docker.com/engine/security/certificates/)

#### Dockfile 加速样例 

<pre>
FROM demisto/sklearn:1.0.0.23593

COPY requirements.txt .

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories

RUN apk --update add --no-cache --virtual .build-dependencies python3-dev build-base wget git \
  && python -m pip install -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com --upgrade pip \
  && pip install --no-cache-dir  -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com -r requirements.txt \
  && apk del .build-dependencies

COPY extract.py /app/

ENTRYPOINT ["python", "/app/extract.py"]
</pre>
