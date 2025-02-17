# gurans


## 环境变量

- **REPLACE_CHAT**: 强制替换目标地址,/开头
- **PREFIX_CHAT**:   支持多个,每个都增加前缀，/开头 
- **APPEND_CHAT**:  增加更多的接口, /开头
- **DEBUG**:  是否debug默认，是否可以查看日志



## build and test

* build

``` bash
docker build -t gurans_demo .
```

* run

``` bash
docker run -d --name gurans_demo \
  -p 7860:7860 \
  --shm-size="2g" \
  --cap-add=SYS_ADMIN \
  gurans_demo


docker run -d \
  --name gurans_api \
  --restart always \
  -p 5010:7860 \
  -m 2g \
  -e DEBUG=false \
  ghcr.io/hhhaiai/gurans:latest

```

* test

``` bash
curl http://localhost:7860/v1/models



curl -s --location 'http://0.0.0.0:7860/translate' \
--header 'Content-Type: application/json' \
--data '{
  "msgId": "",
  "srcContent": "",
  "nameList": "",
  "languageFrom": "auto",
  "languageTo": "en",
  "srcDecryptedContent": "武当山驻少林寺办事处王喇嘛，给大家介绍私米，还有无链，介绍l一个文章： https://chainless.hk/zh-hans/2023/11/26/dw20%e5%8e%bb%e4%b8%ad%e5%bf%83%e6%9c%ac%e4%bd%8d%e5%b8%81%e7%9a%84%e5%ae%9e%e7%8e%b0/   好了",
  "serverMsgId": "",
  "num": 100
}'

```
