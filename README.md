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

## 基础软件

功能 | 名称 | 地址 | 参考资源
-----|-------|-------|-------
软路由 | 爱快软路由 | https://www.ikuai8.com/product/software/routersystem.html |
NAS | 群辉 | https://www.synology.cn/zh-cn | 带办公套件 |
nas-on-pc | XPEnology | https://xpenology.club/ |
VPN | WireGuard | https://www.wireguard.com/ | [Set up a personal VPN in the cloud](https://github.com/trailofbits/algo)
ERP | Odoo | https://www.odoo.com/ |
IdM | FreeIPA(DNS、LDAP、CERT) <br> Keycloak| https://www.freeipa.org/ <br> https://www.keycloak.org/ | [Centos7中安装和配置FreeIPA](https://cloud.tencent.com/developer/article/1581277) <br>[Using 3rd part certificates for HTTP/LDAP](https://www.freeipa.org/page/Using_3rd_part_certificates_for_HTTP/LDAP)  <br>--allow-zone-overlap 
镜像仓库 | Harbor | https://goharbor.io/ |
证书管理 | cert-manager <br> FreeIPA <br> OpenSSL | https://cert-manager.io/ | [Rancher - Updating a Private CA Certificate](https://rancher.com/docs/rancher/v2.x/en/installation/resources/update-ca-cert/) <br>[变更 Rancher Server IP 或域名](https://docs.rancher.cn/docs/rancher2/admin-settings/replace-ip-domain/_index/) <br> create_self-signed-cert.sh <br> [Export Certificates and Private Key from a PKCS#12 File with OpenSSL](https://www.ssl.com/how-to/export-certificates-private-key-from-pkcs12-file-with-openssl/) <br> [Alidns-Webhook](https://github.com/pragkent/alidns-webhook)
IT 自动化 | Ansible | https://www.ansible.com/ | 
Infrastructure as Code | TerraForm | https://www.terraform.io/ |
HCI | HarvesterHCI | https://harvesterhci.io/ | [开源HCI软件Harvester beta版深度剖析](https://www.bilibili.com/video/BV1oy4y1M7vZ?from=search&seid=9623238299367553291&spm_id_from=333.337.0.0)
S3兼容文件存储 | MinIO | https://min.io/ | 
知识库 | XWiki | https://www.xwiki.org/ |
Open Source BI | Metabase | https://www.metabase.com/ |
GitLab | GitLab | https://www.gitlab.com | [GitLab-EE Xack](https://www.52dzd.com/2021/10/16/gitlab-ee-cracked/)
图表 | PlantUML | https://plantuml.com/ | [Creating UML Database Diagrams for SQL Server](https://www.red-gate.com/simple-talk/databases/sql-server/tools-sql-server/automatically-creating-uml-database-diagrams-for-sql-server/) [SQL2UML](https://github.com/bmrussell/sql2puml)
图表 | Krokil | https://kroki.io/ |
LoadBalance | HAProxy | http://www.haproxy.org | [Routing to multiple domains over http and https](https://blog.entrostat.com/routing-multiple-domains-using-haproxy-http-and-https-ssl/) Kong

## Kubernetes 相关

功能 | 名称 | 地址 | 参考资源
-----|-------|-------|-------
集群管理 | Rancher | https://www.rancher.cn/ | [推荐架构](https://docs.rancher.cn/docs/rancher2.5/overview/architecture-recommendations/_index/)
轻量集群 | k3s <br> kind <br> k3d | https://k3s.io/ <br> https://k3d.io/ <br> https://kind.sigs.k8s.io/ | [Kubernetes & Rancher 2.5 on a Win 10 laptop with k3d & k3s](https://itnext.io/kubernetes-rancher-2-5-on-your-windows-10-laptop-with-k3d-and-k3s-7404f288342f) [HTTPS using Letsencrypt and Traefik with k3s](https://sysadmins.co.za/https-using-letsencrypt-and-traefik-with-k3s/)
Helm Hub | ArtifactHub | https://artifacthub.io/ |
Operator Hub | OperatorHub | https://operatorhub.io/ |
CNCF | CNCF | https://www.cncf.io/ | https://www.cncf.io/
Storage | Rook <br> OpenEBS <br> LongHorn | https://rook.io/ <br> https://openebs.io/ <br> https://longhorn.io/ |
Backup | Kasten | https://www.kasten.io/product/ |
Load Balancer | MetalLB | https://metallb.universe.tf/ |

